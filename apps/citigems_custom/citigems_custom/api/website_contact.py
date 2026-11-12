"""Public website contact form → ERP Communication + outgoing email."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, now_datetime, strip_html, validate_email_address

SCHOOL_EMAIL = "citigems2014@gmail.com"
_RATE_WINDOW_MIN = 10
_RATE_MAX = 5


def _client_ip() -> str:
	try:
		xff = (frappe.get_request_header("X-Forwarded-For") or "").split(",")[0].strip()
	except Exception:
		xff = ""
	return xff or (getattr(frappe.local, "request_ip", None) or "unknown")


def _rate_limited(ip: str) -> bool:
	"""ponytail: in-memory-ish cache rate limit; ceiling ~guest spam. Upgrade: Redis."""
	key = f"website_contact_rate::{ip}"
	hits = cint(frappe.cache().get_value(key) or 0)
	if hits >= _RATE_MAX:
		return True
	frappe.cache().set_value(key, hits + 1, expires_in_sec=_RATE_WINDOW_MIN * 60)
	return False


def _desk_todo(subject: str, description: str, reference_name: str) -> None:
	"""Fallback when SMTP is down: surface contact in Desk."""
	try:
		todo = frappe.get_doc(
			{
				"doctype": "ToDo",
				"description": description,
				"reference_type": "Communication",
				"reference_name": reference_name,
				"assigned_by": "Administrator",
				"allocated_to": "Administrator",
				"priority": "Medium",
				"status": "Open",
			}
		)
		todo.insert(ignore_permissions=True)
	except Exception as exc:
		frappe.log_error(title="website_contact todo failed", message=str(exc)[:500])


@frappe.whitelist(allow_guest=True, methods=["POST"])
def submit_contact(name: str | None = None, email: str | None = None, phone: str | None = None, message: str | None = None):
	"""Receive marketing-site contact form and notify the school mailbox."""
	frappe.flags.ignore_permissions = True

	name = (name or "").strip()[:120]
	email = (email or "").strip()[:140]
	phone = (phone or "").strip()[:60]
	message = strip_html((message or "").strip())[:5000]

	if not name or not email or not message:
		frappe.throw(_("Name, email and message are required."), frappe.ValidationError)
	validate_email_address(email, throw=True)

	ip = _client_ip()
	if _rate_limited(ip):
		frappe.throw(_("Too many messages. Please try again later."), frappe.ValidationError)

	subject = f"Contact site web — {name}"
	body = (
		f"<p><b>Nom :</b> {frappe.utils.escape_html(name)}</p>"
		f"<p><b>E-mail :</b> {frappe.utils.escape_html(email)}</p>"
		f"<p><b>Téléphone :</b> {frappe.utils.escape_html(phone) or '—'}</p>"
		f"<p><b>Message :</b></p>"
		f"<p>{frappe.utils.escape_html(message).replace(chr(10), '<br>')}</p>"
		f"<hr><p style='color:#666;font-size:12px'>IP {frappe.utils.escape_html(ip)} · {now_datetime()}</p>"
	)

	comm = frappe.get_doc(
		{
			"doctype": "Communication",
			"subject": subject,
			"content": body,
			"communication_medium": "Email",
			"communication_type": "Communication",
			"sent_or_received": "Received",
			"sender": email,
			"recipients": SCHOOL_EMAIL,
			"status": "Linked",
		}
	)
	comm.insert(ignore_permissions=True)
	frappe.db.commit()

	email_sent = False
	email_error = None
	try:
		frappe.sendmail(
			recipients=[SCHOOL_EMAIL],
			reply_to=email,
			subject=subject,
			message=body,
			reference_doctype="Communication",
			reference_name=comm.name,
			now=True,
		)
		email_sent = True
	except Exception as exc:
		email_error = str(exc)[:500]
		frappe.log_error(title="website_contact sendmail failed", message=email_error)
		# sendmail may have pushed a ValidationError into message_log; don't leak to guest.
		frappe.local.message_log = []
		_desk_todo(
			subject,
			f"{subject}\nDe: {email}\nTél: {phone or '—'}\n\n{message}",
			comm.name,
		)

	return {
		"ok": True,
		"communication": comm.name,
		"email_sent": email_sent,
	}
