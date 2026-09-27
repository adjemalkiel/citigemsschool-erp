"""FedaPay Mobile Money for Citigems school fee payments (Guardian / Student portal)."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import time

import frappe
import requests
from frappe import _
from frappe.utils import cint, flt, now_datetime

REQUEST_TIMEOUT = 45
MOBILE_MONEY_MOP = "Mobile Money"
OPERATOR_ENDPOINTS = {
	"mtn_open": "mtn_open",
	"MTN": "mtn_open",
	"moov": "moov",
	"MOOV": "moov",
	"sbin": "sbin",
	"CELTIIS": "sbin",
}
OPERATOR_LABELS = {
	"mtn_open": "MTN",
	"moov": "MOOV",
	"sbin": "CELTIIS",
}
STATUS_MAP = {
	"approved": "Approved",
	"declined": "Declined",
	"canceled": "Canceled",
	"cancelled": "Canceled",
	"expired": "Expired",
	"pending": "Pending",
}
FEDAPAY_ERROR_MESSAGES = {
	"ACCOUNT_NOT_FOUND": _(
		"Ce numero n'a pas de compte Mobile Money actif chez l'operateur choisi. "
		"Verifiez le numero et l'operateur (Benin: MTN, MOOV, CELTIIS)."
	),
	"INSUFFICIENT_FUNDS": _("Solde Mobile Money insuffisant sur le compte du client."),
	"USER_CANCELLED": _("Le client a refuse le paiement sur son telephone."),
	"TIMEOUT": _("Le client n'a pas confirme le paiement a temps."),
}


def get_fedapay_settings(company, required=True):
	"""Load FedaPay Settings for a company."""
	if not company:
		if required:
			frappe.throw(_("Société manquante pour FedaPay Settings."))
		return None

	settings = None
	if frappe.db.exists("FedaPay Settings", company):
		settings = frappe.get_doc("FedaPay Settings", company)
		if not cint(settings.is_active):
			settings = None

	if settings is None:
		if required:
			frappe.throw(
				_("FedaPay Settings non configuré pour la société {0}.").format(company)
			)
		return None

	if required and not settings.api_key:
		frappe.throw(_("Configurez la clé API dans FedaPay Settings."))
	return settings


def _settings_value(settings, fieldname, default=0):
	if settings is None:
		return default
	if hasattr(settings, "get"):
		return settings.get(fieldname, default)
	return getattr(settings, fieldname, default)


def calculate_customer_fee(amount, settings=None):
	base_amount = flt(amount)
	percent = flt(_settings_value(settings, "customer_fee_percent"))
	minimum = flt(_settings_value(settings, "customer_fee_minimum"))
	if base_amount <= 0 or percent <= 0:
		return 0
	fee = base_amount * percent / 100
	if minimum > 0:
		fee = max(fee, minimum)
	return int(round(fee))


def get_mobile_money_quote(amount, settings=None):
	order_total = flt(amount)
	fee = calculate_customer_fee(order_total, settings)
	return {
		"order_total": order_total,
		"fee": fee,
		"total_charged": order_total + fee,
		"currency": "XOF",
	}


@frappe.whitelist()
def get_mobile_money_quote_api(amount, company=None):
	settings = None
	if company:
		settings = get_fedapay_settings(company, required=False)
		if not settings:
			frappe.throw(
				_("FedaPay Settings non actif pour cette société ({0}).").format(company)
			)
	return get_mobile_money_quote(amount, settings)


def get_base_url(settings=None):
	if settings is None:
		frappe.throw(_("FedaPay Settings requis pour déterminer l'URL API."))
	if settings.environment == "Live":
		return "https://api.fedapay.com/v1"
	return "https://sandbox-api.fedapay.com/v1"


def normalize_benin_phone(phone):
	"""Normalise un numéro béninois (10 chiffres nationaux, ex. 0197123456)."""
	digits = re.sub(r"\D", "", phone or "")
	if digits.startswith("00229"):
		digits = digits[5:]
	elif digits.startswith("229") and len(digits) > 8:
		digits = digits[3:]

	if len(digits) == 10 and digits.startswith("0"):
		national = digits
	elif len(digits) == 9 and digits.startswith("1"):
		national = f"0{digits}"
	elif len(digits) == 8:
		national = f"01{digits}"
	else:
		frappe.throw(_("Numéro de téléphone invalide (10 chiffres attendus, ex. 0197123456)."))

	if not re.fullmatch(r"0\d{9}", national):
		frappe.throw(_("Numéro de téléphone invalide (10 chiffres attendus, ex. 0197123456)."))

	local = national[2:]
	return {
		"national": national,
		"local": local,
		"international": f"+229{local}",
		"msisdn": f"229{national}",
		"country_code": "BJ",
	}


def normalize_phone(phone, company=None, country=None):
	return normalize_benin_phone(phone)


def _resolve_operator(operator):
	raw = (operator or "").strip()
	if not raw:
		frappe.throw(_("Opérateur invalide. Choisissez MTN, MOOV ou CELTIIS."))
	code = OPERATOR_ENDPOINTS.get(raw) or OPERATOR_ENDPOINTS.get(raw.upper())
	if not code:
		upper = raw.upper()
		for key, endpoint in OPERATOR_ENDPOINTS.items():
			if key.upper() == upper:
				code = endpoint
				break
	if not code:
		frappe.throw(_("Opérateur invalide. Choisissez MTN, MOOV ou CELTIIS."))
	return code


def _fedapay_request(method, path, json_data=None, settings=None, timeout=None):
	if settings is None:
		frappe.throw(_("FedaPay Settings requis pour l'appel API."))
	api_key = settings.get_password("api_key")
	url = get_base_url(settings).rstrip("/") + "/" + path.lstrip("/")
	headers = {
		"Authorization": f"Bearer {api_key}",
		"Content-Type": "application/json",
		"Accept": "application/json",
	}
	try:
		response = requests.request(
			method,
			url,
			headers=headers,
			json=json_data,
			timeout=timeout if timeout is not None else REQUEST_TIMEOUT,
		)
	except requests.RequestException as exc:
		frappe.log_error(message=frappe.get_traceback(), title="FedaPay - Réseau")
		frappe.throw(_("Erreur réseau FedaPay : {0}").format(exc))

	try:
		payload = response.json()
	except ValueError:
		payload = {"raw": response.text}

	if response.status_code >= 400:
		message = _extract_error(payload) or response.text
		frappe.log_error(
			title=f"FedaPay {response.status_code} {method} {path}",
			message=json.dumps(
				{"request": json_data, "response": payload},
				ensure_ascii=False,
				default=str,
			),
		)
		frappe.throw(_("FedaPay ({0}) : {1}").format(response.status_code, message))

	return payload


def _extract_error(payload):
	if not isinstance(payload, dict):
		return None
	if payload.get("message"):
		return payload.get("message")
	errors = payload.get("errors") or payload.get("error")
	if isinstance(errors, list) and errors:
		return errors[0].get("message") or str(errors[0])
	if isinstance(errors, dict):
		parts = []
		for key, value in errors.items():
			if isinstance(value, list):
				for item in value:
					parts.append(f"{key}: {item}")
			else:
				parts.append(f"{key}: {value}")
		if parts:
			return "; ".join(parts)
	return None


def _doc_value(doc, fieldname, default=None):
	if isinstance(doc, dict):
		return doc.get(fieldname) or default
	if hasattr(doc, "get"):
		return doc.get(fieldname) or default
	return getattr(doc, fieldname, None) or default


def _customer_email(doc, phone_info):
	email = _doc_value(doc, "contact_email") or _doc_value(doc, "contact_email_id")
	customer = _doc_value(doc, "customer")
	if not email and customer:
		email = frappe.db.get_value("Customer", customer, "email_id")
	if not email:
		email = f"fees.{phone_info['local']}@citigems.school"
	return email


def _customer_payload(doc, phone_info):
	name = (_doc_value(doc, "customer_name") or _doc_value(doc, "customer") or "Tuteur").strip()
	parts = name.split(None, 1)
	firstname = parts[0][:50] if parts else "Tuteur"
	lastname = parts[1][:50] if len(parts) > 1 else "Citigems"
	return {
		"firstname": firstname,
		"lastname": lastname,
		"email": _customer_email(doc, phone_info),
		"phone_number": {
			"number": phone_info["local"],
			"country": phone_info.get("country_code") or "BJ",
		},
	}


def _merchant_reference(payment_name):
	return f"{payment_name}-{secrets.token_hex(4)}"


def _payment_name_from_merchant_reference(merchant_reference):
	if not merchant_reference:
		return None
	if frappe.db.exists("FedaPay Payment", merchant_reference):
		return merchant_reference
	if "-" in merchant_reference:
		base = merchant_reference.rsplit("-", 1)[0]
		if frappe.db.exists("FedaPay Payment", base):
			return base
	return None


def _extract_resource(payload):
	if not isinstance(payload, dict):
		return payload
	for key in ("v1/transaction", "v1/token", "transaction", "token", "data"):
		if key in payload and isinstance(payload[key], dict):
			return payload[key]
	if "v1" in payload and isinstance(payload["v1"], dict):
		return payload["v1"]
	if "id" in payload:
		return payload
	for value in payload.values():
		if isinstance(value, dict) and "id" in value:
			return value
	return payload


def _create_fedapay_transaction(
	doc, operator_code, phone_info, settings, merchant_reference, charged_amount=None, description=None
):
	amount = int(round(flt(charged_amount if charged_amount is not None else doc.grand_total)))
	currency = doc.currency or "XOF"
	if currency == "FCFA":
		currency = "XOF"

	payload = {
		"locale": "fr",
		"description": description or _("Frais scolaires {0}").format(doc.name),
		"amount": amount,
		"currency": {"iso": currency},
		"merchant_reference": merchant_reference,
		"customer": _customer_payload(doc, phone_info),
	}
	response = _fedapay_request("POST", "/transactions", payload, settings)
	transaction = _extract_resource(response)
	transaction_id = str(transaction.get("id") or transaction.get("transaction_id") or "")
	if not transaction_id:
		frappe.throw(_("FedaPay n'a pas renvoyé d'identifiant de transaction."))
	return transaction_id, amount, currency


def _generate_payment_token(transaction_id, settings):
	response = _fedapay_request(
		"POST", f"/transactions/{transaction_id}/token", settings=settings
	)
	resource = _extract_resource(response)
	token = resource.get("token") or resource.get("payment_token")
	if not token:
		frappe.throw(_("Impossible de générer le token de paiement FedaPay."))
	return token


def _send_phone_payment(token, operator_code, phone_info, settings):
	payload = {
		"token": token,
		"phone_number": {
			"number": phone_info["local"],
			"country": phone_info.get("country_code") or "BJ",
		},
	}
	_fedapay_request("POST", f"/{operator_code}", payload, settings)


def _assert_fee_invoice_access(invoice_name):
	"""Guardian / Student / Accounts may pay outstanding fee invoices."""
	user = frappe.session.user
	if user in (None, "Guest"):
		frappe.throw(_("Connectez-vous pour payer les frais."), frappe.PermissionError)

	roles = set(frappe.get_roles(user))
	if roles & {"System Manager", "Accounts Manager", "Accounts User", "Education Manager"}:
		return

	si = frappe.get_doc("Sales Invoice", invoice_name)
	customer = si.customer
	# Student linked to customer
	student = frappe.db.get_value("Student", {"customer": customer}, "name")
	if "Student" in roles:
		own = frappe.db.get_value("Student", {"user": user}, "name")
		if own and own == student:
			return
	if "Guardian" in roles and student:
		guardian = frappe.db.get_value("Guardian", {"user": user}, "name")
		if guardian and frappe.db.exists(
			"Student Guardian", {"parent": student, "guardian": guardian}
		):
			return

	frappe.throw(_("Vous n'êtes pas autorisé à payer cette facture."), frappe.PermissionError)


@frappe.whitelist()
def create_fee_payment(sales_invoice, operator, phone_number):
	"""Portal « Payer les frais » — create FedaPay transaction for outstanding SI."""
	_assert_fee_invoice_access(sales_invoice)
	if not frappe.db.exists("Sales Invoice", sales_invoice):
		frappe.throw(_("Facture introuvable."))

	doc = frappe.get_doc("Sales Invoice", sales_invoice)
	if doc.docstatus != 1:
		frappe.throw(_("La facture doit être soumise."))
	outstanding = flt(doc.outstanding_amount)
	if outstanding <= 0:
		frappe.throw(_("Cette facture est déjà soldée."))

	operator_code = _resolve_operator(operator)
	phone_info = normalize_phone(phone_number, company=doc.company)
	settings = get_fedapay_settings(doc.company)
	quote = get_mobile_money_quote(outstanding, settings)

	payment_doc = frappe.get_doc(
		{
			"doctype": "FedaPay Payment",
			"status": "Pending",
			"operator": OPERATOR_LABELS.get(operator_code, operator_code),
			"phone_number": phone_info["national"],
			"amount": quote["order_total"],
			"transaction_fee": quote["fee"],
			"amount_charged": quote["total_charged"],
			"currency": doc.currency or "XOF",
			"sales_invoice": doc.name,
			"company": doc.company,
		}
	)
	payment_doc.flags.ignore_permissions = True
	payment_doc.insert()

	try:
		merchant_reference = _merchant_reference(payment_doc.name)
		transaction_id, amount, currency = _create_fedapay_transaction(
			doc,
			operator_code,
			phone_info,
			settings,
			merchant_reference,
			quote["order_total"],
			description=_("Frais scolaires {0}").format(doc.name),
		)
		token = _generate_payment_token(transaction_id, settings)
		_send_phone_payment(token, operator_code, phone_info, settings)
		payment_doc.db_set(
			{
				"fedapay_transaction_id": transaction_id,
				"fedapay_token": token,
				"amount_charged": amount,
				"currency": currency,
			}
		)
		if doc.meta.has_field("fedapay_payment"):
			doc.db_set(
				{
					"fedapay_payment": payment_doc.name,
					"fedapay_transaction_id": transaction_id,
					"mobile_money_operator": OPERATOR_LABELS.get(operator_code, operator_code),
					"mobile_money_phone": phone_info["national"],
				}
			)
	except Exception as exc:
		payment_doc.db_set({"status": "Declined", "error_message": str(exc)})
		raise

	return {
		"payment_name": payment_doc.name,
		"transaction_id": transaction_id,
		"sales_invoice": doc.name,
		"status": "Pending",
		"order_total": quote["order_total"],
		"fee": quote["fee"],
		"total_charged": quote["total_charged"],
		"message": _("Confirmez le paiement sur votre téléphone."),
	}


def _submit_payment_entry(payment):
	"""Mark Sales Invoice paid via Payment Entry after FedaPay approval."""
	if not payment.sales_invoice or not frappe.db.exists("Sales Invoice", payment.sales_invoice):
		return False

	si = frappe.get_doc("Sales Invoice", payment.sales_invoice)
	if si.docstatus != 1:
		return False
	if flt(si.outstanding_amount) <= 0:
		return True

	prev_user = frappe.session.user
	frappe.set_user("Administrator")
	try:
		from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

		entry = get_payment_entry("Sales Invoice", si.name)
		entry.mode_of_payment = MOBILE_MONEY_MOP
		entry.reference_no = payment.fedapay_transaction_id
		entry.reference_date = now_datetime().date()
		entry.insert(ignore_permissions=True)
		entry.submit()
	finally:
		frappe.set_user(prev_user)
	return True


def _approve_payment(payment, transaction=None, raw_webhook=None):
	if transaction and isinstance(transaction, dict):
		tx_id = str(transaction.get("id") or "")
		if tx_id and tx_id != (payment.fedapay_transaction_id or ""):
			payment.db_set({"fedapay_transaction_id": tx_id})
			payment.reload()

	_submit_payment_entry(payment)

	if payment.status == "Approved":
		return

	updates = {"status": "Approved"}
	if raw_webhook:
		updates["raw_webhook"] = raw_webhook
	payment.db_set(updates)


_STATUS_POLL_CACHE_TTL = 2
_STATUS_REQUEST_TIMEOUT = 12


def _fetch_fedapay_transaction(payment, timeout=None):
	if not payment.fedapay_transaction_id:
		return None
	try:
		settings = get_fedapay_settings(payment.company or frappe.db.get_value(
			"Sales Invoice", payment.sales_invoice, "company"
		))
		response = _fedapay_request(
			"GET",
			f"/transactions/{payment.fedapay_transaction_id}",
			settings=settings,
			timeout=timeout if timeout is not None else _STATUS_REQUEST_TIMEOUT,
		)
		return _extract_resource(response)
	except Exception:
		frappe.log_error(title="FedaPay status refresh", message=frappe.get_traceback())
		return None


def _friendly_fedapay_error(transaction):
	code = (transaction or {}).get("last_error_code")
	if code and code in FEDAPAY_ERROR_MESSAGES:
		return FEDAPAY_ERROR_MESSAGES[code]
	if code and code not in ("NO_ERROR", ""):
		return _("Erreur FedaPay : {0}").format(code)
	return None


def _refresh_payment_from_fedapay(payment, timeout=None):
	transaction = _fetch_fedapay_transaction(payment, timeout=timeout)
	if not transaction:
		return
	status = (transaction.get("status") or "").lower()
	mapped = STATUS_MAP.get(status)
	if mapped == "Approved":
		_approve_payment(payment, transaction)
	elif mapped and mapped != "Pending":
		updates = {"status": mapped}
		error_message = _friendly_fedapay_error(transaction)
		if error_message:
			updates["error_message"] = error_message
		payment.db_set(updates)


@frappe.whitelist()
def get_payment_status(payment_name):
	"""Poll FedaPay payment status (portal)."""
	_assert_fee_invoice_access(
		frappe.db.get_value("FedaPay Payment", payment_name, "sales_invoice")
	)
	payment = frappe.get_doc("FedaPay Payment", payment_name)
	if payment.status == "Pending" and payment.fedapay_transaction_id:
		cache_key = f"fedapay_status_poll:{payment_name}"
		if not frappe.cache.get_value(cache_key):
			_refresh_payment_from_fedapay(payment, timeout=_STATUS_REQUEST_TIMEOUT)
			payment.reload()
			frappe.cache.set_value(cache_key, 1, expires_in_sec=_STATUS_POLL_CACHE_TTL)

	return {
		"status": payment.status,
		"sales_invoice": payment.sales_invoice,
		"transaction_id": payment.fedapay_transaction_id,
		"error_message": payment.error_message,
	}


def _verify_webhook_signature(payload_bytes, signature_header, secret, tolerance=300):
	if not secret:
		return True
	if not signature_header:
		return False

	timestamp = -1
	signatures = []
	for item in signature_header.split(","):
		key, _, value = item.partition("=")
		key = key.strip()
		value = value.strip()
		if key == "t":
			try:
				timestamp = int(value)
			except ValueError:
				timestamp = -1
		elif key == "s":
			signatures.append(value)

	if timestamp < 0 or not signatures:
		return False

	payload_text = payload_bytes.decode("utf-8") if isinstance(payload_bytes, bytes) else payload_bytes
	signed_payload = f"{timestamp}.{payload_text}"
	expected = hmac.new(
		secret.encode("utf-8"),
		signed_payload.encode("utf-8"),
		hashlib.sha256,
	).hexdigest()

	if not any(hmac.compare_digest(expected, sig) for sig in signatures):
		return False

	if tolerance and abs(int(time.time()) - timestamp) > tolerance:
		return False

	return True


def _verify_against_active_fedapay_secrets(payload_bytes, signature_header):
	active = frappe.get_all("FedaPay Settings", filters={"is_active": 1}, pluck="name")
	if not active:
		return False

	checked_secret = False
	for name in active:
		settings = frappe.get_doc("FedaPay Settings", name)
		secret = settings.get_password("webhook_secret") or ""
		if not secret:
			continue
		checked_secret = True
		if _verify_webhook_signature(payload_bytes, signature_header, secret):
			return True

	return not checked_secret


def _find_payment_from_event(event):
	entity = event.get("entity") or event.get("data") or {}
	if isinstance(entity, dict) and "entity" in entity:
		entity = entity.get("entity") or entity

	transaction_id = str(entity.get("id") or entity.get("transaction_id") or "")
	merchant_reference = entity.get("merchant_reference")

	if merchant_reference:
		payment_name = _payment_name_from_merchant_reference(merchant_reference)
		if payment_name:
			return frappe.get_doc("FedaPay Payment", payment_name)

	if transaction_id:
		name = frappe.db.get_value(
			"FedaPay Payment", {"fedapay_transaction_id": transaction_id}, "name"
		)
		if name:
			return frappe.get_doc("FedaPay Payment", name)
	return None


@frappe.whitelist(allow_guest=True)
def webhook():
	"""Webhook FedaPay : confirmation transaction.approved → Payment Entry."""
	frappe.flags.ignore_permissions = True
	payload_bytes = frappe.request.get_data() or b""
	signature = frappe.get_request_header("X-FEDAPAY-SIGNATURE") or frappe.get_request_header(
		"x-fedapay-signature"
	)

	if not frappe.get_all("FedaPay Settings", filters={"is_active": 1}, limit=1):
		frappe.local.response.http_status_code = 503
		return {"error": "FedaPay not configured"}

	if not _verify_against_active_fedapay_secrets(payload_bytes, signature):
		frappe.local.response.http_status_code = 401
		return {"error": "Invalid signature"}

	try:
		event = json.loads(payload_bytes.decode("utf-8"))
	except ValueError:
		frappe.local.response.http_status_code = 400
		return {"error": "Invalid JSON"}

	event_name = event.get("name") or event.get("event")
	entity = event.get("entity") or event.get("data") or {}
	if isinstance(entity, dict) and "entity" in entity:
		entity = entity.get("entity") or entity

	raw_webhook = json.dumps(event, ensure_ascii=False)
	payment = _find_payment_from_event(event)
	if not payment:
		frappe.log_error(title="FedaPay webhook orphan", message=raw_webhook)
		frappe.local.response.http_status_code = 200
		return {"received": True}

	status = (entity.get("status") or "").lower() if isinstance(entity, dict) else ""

	if event_name == "transaction.approved" or status == "approved":
		_approve_payment(payment, entity, raw_webhook)
	elif status in STATUS_MAP:
		mapped = STATUS_MAP[status]
		if mapped != "Approved":
			payment.db_set({"status": mapped, "raw_webhook": raw_webhook})
	else:
		payment.db_set({"raw_webhook": raw_webhook})

	frappe.local.response.http_status_code = 200
	return {"received": True}


@frappe.whitelist()
def list_outstanding_fees(student=None):
	"""Outstanding fee invoices for the logged-in Guardian or Student."""
	user = frappe.session.user
	if user in (None, "Guest"):
		frappe.throw(_("Connectez-vous pour voir les frais."), frappe.PermissionError)

	customers = set()
	roles = set(frappe.get_roles(user))

	if "Student" in roles or student:
		own = student or frappe.db.get_value("Student", {"user": user}, "name")
		if own:
			cust = frappe.db.get_value("Student", own, "customer")
			if cust:
				customers.add(cust)

	if "Guardian" in roles:
		guardian = frappe.db.get_value("Guardian", {"user": user}, "name")
		if guardian:
			for row in frappe.get_all(
				"Student Guardian", filters={"guardian": guardian}, fields=["parent"]
			):
				cust = frappe.db.get_value("Student", row.parent, "customer")
				if cust:
					customers.add(cust)

	if not customers and roles & {"System Manager", "Accounts Manager", "Education Manager"}:
		# Staff: optional student filter only
		if student:
			cust = frappe.db.get_value("Student", student, "customer")
			if cust:
				customers.add(cust)

	if not customers:
		return []

	invoices = frappe.get_all(
		"Sales Invoice",
		filters={
			"customer": ["in", list(customers)],
			"docstatus": 1,
			"outstanding_amount": [">", 0],
		},
		fields=[
			"name",
			"customer",
			"customer_name",
			"posting_date",
			"due_date",
			"grand_total",
			"outstanding_amount",
			"currency",
			"company",
		],
		order_by="due_date asc",
	)
	return invoices
