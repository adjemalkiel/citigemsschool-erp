"""Site locale defaults for Citigems (French-first guest experience).

XOF display (FR): keep ISO code XOF; show amounts as ``5,500 FCFA``.
"""

import frappe
from frappe.utils import cint, fmt_money

DEFAULT_LANGUAGE = "fr"
XOF = "XOF"
FCFA_SYMBOL = "FCFA"
# Comma thousands, no decimals — CFA franc amounts are whole units in Desk/portal.
XOF_NUMBER_FORMAT = "#,###"


def force_site_language_for_guests():
	"""French-first for guests; honor login FR/EN picker (preferred_language cookie)."""
	if frappe.session.user != "Guest":
		return
	if frappe.form_dict.get("_lang"):
		return

	# Same cookie stock Frappe language picker sets (website.js).
	cookie = None
	if getattr(frappe, "request", None) and frappe.request.cookies:
		cookie = (frappe.request.cookies.get("preferred_language") or "").strip().lower()
	if cookie in ("fr", "en"):
		if frappe.local.lang != cookie:
			frappe.local.lang = cookie
		return

	site_lang = frappe.get_system_settings("language") or DEFAULT_LANGUAGE
	if site_lang and frappe.local.lang != site_lang:
		frappe.local.lang = site_lang


def ensure_site_language():
	"""Persist French as the site default language (System Settings)."""
	ss = frappe.get_single("System Settings")
	if ss.language != DEFAULT_LANGUAGE:
		ss.language = DEFAULT_LANGUAGE
		ss.flags.ignore_mandatory = True
		ss.save(ignore_permissions=True)
		frappe.db.commit()


def ensure_xof_fcfa_display():
	"""XOF stays the ISO currency; French UI shows FCFA after the amount.

	Example: ``5,500 FCFA`` (comma thousands, symbol on the right).
	"""
	if not frappe.db.exists("Currency", XOF):
		frappe.get_doc(
			{
				"doctype": "Currency",
				"currency_name": XOF,
				"enabled": 1,
				"fraction": "Centime",
				"fraction_units": 100,
				"symbol": FCFA_SYMBOL,
				"symbol_on_right": 1,
				"number_format": XOF_NUMBER_FORMAT,
			}
		).insert(ignore_permissions=True)
	else:
		frappe.db.set_value(
			"Currency",
			XOF,
			{
				"enabled": 1,
				"symbol": FCFA_SYMBOL,
				"symbol_on_right": 1,
				"number_format": XOF_NUMBER_FORMAT,
			},
			update_modified=False,
		)

	ss = frappe.get_single("System Settings")
	changed = False
	if cint(ss.use_number_format_from_currency) != 1:
		ss.use_number_format_from_currency = 1
		changed = True
	# Whole CFA francs in FR Desk / portal (matches ``5,500 FCFA``).
	if str(ss.currency_precision or "") != "0":
		ss.currency_precision = "0"
		changed = True
	if ss.number_format != XOF_NUMBER_FORMAT:
		ss.number_format = XOF_NUMBER_FORMAT
		changed = True
	if changed:
		ss.flags.ignore_mandatory = True
		ss.save(ignore_permissions=True)

	frappe.db.commit()
	frappe.clear_cache()


def _selfcheck_fcfa_format():
	"""Runnable check: fails if XOF no longer formats as ``5,500 FCFA``."""
	ensure_xof_fcfa_display()
	got = fmt_money(5500, currency=XOF)
	assert got == "5,500 FCFA", f"expected '5,500 FCFA', got {got!r}"
	return got
