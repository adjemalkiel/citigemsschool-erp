"""Seed Citigems Bilingual School company + MECeF tax templates (XOF / BJ / fr).

Run inside bench after install-app:

  bench --site citigems.localhost execute citigems_custom.scripts.seed_citigems.seed

Does not store API secrets — configure MeCef / FedaPay Settings in Desk.
"""

from __future__ import annotations

import frappe
from frappe.utils import getdate, today


COMPANY_NAME = "Citigems Bilingual School"
COMPANY_ABBR = "CBS"
COUNTRY = "Benin"
CURRENCY = "XOF"
DEFAULT_LANGUAGE = "fr"
MISSION_NOTE = (
	"École bilingue (français / anglais) — Citigems Bilingual School, Bénin. "
	"Périmètre fondation ERP : 18 mois (admissions, scolarité, frais, RH de base, "
	"e-MECeF et paiements Mobile Money FedaPay)."
)


def _ensure_currency():
	"""ISO XOF; French display symbol FCFA after amount (see locale.ensure_xof_fcfa_display)."""
	from citigems_custom.locale import ensure_xof_fcfa_display

	ensure_xof_fcfa_display()


def _ensure_warehouse_types():
	"""ERPNext company insert creates a Transit warehouse; type must exist first."""
	for name in ("Transit",):
		if not frappe.db.exists("Warehouse Type", name):
			frappe.get_doc({"doctype": "Warehouse Type", "name": name}).insert(
				ignore_permissions=True
			)


def _ensure_company():
	if frappe.db.exists("Company", COMPANY_NAME):
		company = frappe.get_doc("Company", COMPANY_NAME)
	else:
		company = frappe.get_doc(
			{
				"doctype": "Company",
				"company_name": COMPANY_NAME,
				"abbr": COMPANY_ABBR,
				"default_currency": CURRENCY,
				"country": COUNTRY,
				"create_chart_of_accounts_based_on": "Standard Template",
				"chart_of_accounts": "Standard",
			}
		)
		company.insert(ignore_permissions=True)

	# Soft mission note on company (custom field may not exist — use remarks if present)
	if company.meta.has_field("company_description") and not company.company_description:
		company.company_description = MISSION_NOTE
		company.save(ignore_permissions=True)
	elif company.meta.has_field("address") and not getattr(company, "address", None):
		pass

	# Global defaults
	gd = frappe.get_single("Global Defaults")
	changed = False
	if gd.default_company != COMPANY_NAME:
		gd.default_company = COMPANY_NAME
		changed = True
	if gd.default_currency != CURRENCY:
		gd.default_currency = CURRENCY
		changed = True
	if changed:
		gd.flags.ignore_mandatory = True
		gd.save(ignore_permissions=True)

	ss = frappe.get_single("System Settings")
	if ss.language != DEFAULT_LANGUAGE:
		ss.language = DEFAULT_LANGUAGE
		ss.flags.ignore_mandatory = True
		ss.save(ignore_permissions=True)

	# Education Settings abbreviation when Education app present
	if frappe.db.exists("DocType", "Education Settings"):
		es = frappe.get_single("Education Settings")
		if hasattr(es, "school_college_name_abbreviation"):
			if es.school_college_name_abbreviation != "Citigems":
				es.school_college_name_abbreviation = "Citigems"
				es.flags.ignore_mandatory = True
				es.save(ignore_permissions=True)

	return company


def _ensure_mecef_tax_templates(company_name):
	"""Tax groups A (exonéré) and B (TVA 18%) for e-MECeF fee invoices."""
	if not frappe.db.exists("DocType", "Item Tax Template"):
		return

	# Ensure custom field exists (fixtures / migrate)
	if not frappe.db.exists("Custom Field", {"dt": "Item Tax Template", "fieldname": "mecef_tax_group"}):
		return

	for group, rate, title in (
		("A", 0, "MECeF Groupe A — Exonéré"),
		("B", 18, "MECeF Groupe B — TVA 18%"),
	):
		# ERPNext names Item Tax Template as "{title} - {abbr}"
		if frappe.db.exists("Item Tax Template", {"title": title, "company": company_name}):
			continue
		# Need a tax account — skip if COA not ready
		tax_account = frappe.db.get_value(
			"Account",
			{"company": company_name, "account_type": "Tax", "is_group": 0},
			"name",
		)
		if not tax_account and rate:
			tax_account = frappe.db.get_value(
				"Account",
				{"company": company_name, "is_group": 0, "account_name": ["like", "%TVA%"]},
				"name",
			)
		if not tax_account:
			# Item Tax Template.taxes is mandatory — need any Tax account (rate may be 0)
			tax_account = frappe.db.get_value(
				"Account",
				{"company": company_name, "account_type": "Tax", "is_group": 0},
				"name",
			)
		if not tax_account:
			frappe.logger().warning("No tax account for MECeF Item Tax Template %s — create manually", group)
			continue

		doc = {
			"doctype": "Item Tax Template",
			"title": title,
			"company": company_name,
			"mecef_tax_group": group,
			"taxes": [
				{
					"doctype": "Item Tax Template Detail",
					"tax_type": tax_account,
					"tax_rate": rate,
				}
			],
		}
		frappe.get_doc(doc).insert(ignore_permissions=True)

	# Sales Taxes and Charges Template for group B
	if frappe.db.exists("DocType", "Sales Taxes and Charges Template"):
		if not frappe.db.exists(
			"Custom Field",
			{"dt": "Sales Taxes and Charges Template", "fieldname": "mecef_tax_group"},
		):
			return
		title = "MECeF TVA 18% (Groupe B)"
		name = frappe.db.get_value(
			"Sales Taxes and Charges Template",
			{"company": company_name, "mecef_tax_group": "B"},
			"name",
		)
		if not name:
			tax_account = frappe.db.get_value(
				"Account",
				{"company": company_name, "account_type": "Tax", "is_group": 0},
				"name",
			)
			if tax_account:
				frappe.get_doc(
					{
						"doctype": "Sales Taxes and Charges Template",
						"title": title,
						"company": company_name,
						"mecef_tax_group": "B",
						"taxes": [
							{
								"doctype": "Sales Taxes and Charges",
								"charge_type": "On Net Total",
								"account_head": tax_account,
								"description": "TVA 18%",
								"rate": 18,
							}
						],
					}
				).insert(ignore_permissions=True)


def _ensure_mobile_money_mop(company_name):
	if not frappe.db.exists("Mode of Payment", "Mobile Money"):
		frappe.get_doc(
			{
				"doctype": "Mode of Payment",
				"mode_of_payment": "Mobile Money",
				"type": "Bank",
				"enabled": 1,
			}
		).insert(ignore_permissions=True)

	# Link default account if available
	mop = frappe.get_doc("Mode of Payment", "Mobile Money")
	bank = frappe.db.get_value(
		"Account",
		{"company": company_name, "account_type": "Bank", "is_group": 0},
		"name",
	)
	if bank and not any(r.company == company_name for r in mop.accounts):
		mop.append("accounts", {"company": company_name, "default_account": bank})
		mop.save(ignore_permissions=True)


def seed():
	"""Create company Citigems Bilingual School (BJ, XOF, fr) + tax helpers."""
	frappe.flags.ignore_permissions = True
	_ensure_currency()
	_ensure_warehouse_types()
	company = _ensure_company()
	_ensure_mecef_tax_templates(company.name)
	_ensure_mobile_money_mop(company.name)

	# Note document for operators (no secrets)
	if frappe.db.exists("DocType", "Note"):
		title = "Citigems — fondation 18 mois"
		if not frappe.db.exists("Note", title):
			frappe.get_doc(
				{
					"doctype": "Note",
					"title": title,
					"public": 0,
					"content": f"<p>{MISSION_NOTE}</p>"
					"<p>Configurer ensuite <b>MeCef Settings</b> et <b>FedaPay Settings</b> "
					"pour cette société (jetons uniquement via l’UI Desk).</p>",
				}
			).insert(ignore_permissions=True)

	frappe.db.commit()
	return {
		"company": company.name,
		"abbr": COMPANY_ABBR,
		"country": COUNTRY,
		"currency": CURRENCY,
		"language": DEFAULT_LANGUAGE,
		"mission": MISSION_NOTE,
	}
