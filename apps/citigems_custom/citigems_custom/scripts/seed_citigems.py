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
# ERPNext verified chart (bj_plan_comptable_avec_code.json) — SYSCOHADA with account numbers
CHART_OF_ACCOUNTS = "Syscohada - Plan Comptable avec code"
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
				"chart_of_accounts": CHART_OF_ACCOUNTS,
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
		tax_account = _syscohada_tax_account(company_name)
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
			tax_account = _syscohada_tax_account(company_name)
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


def _tag_syscohada_tax_accounts(company_name):
	"""SYSCOHADA JSON omits account_type on 443x — tag leaves as Tax for ERPNext validators."""
	for name in frappe.get_all(
		"Account",
		filters={
			"company": company_name,
			"is_group": 0,
			"account_number": ["like", "443%"],
		},
		pluck="name",
	):
		frappe.db.set_value("Account", name, "account_type", "Tax", update_modified=False)


def _syscohada_tax_account(company_name):
	"""Prefer SYSCOHADA 443x (TVA facturée), then any Tax / %TVA% leaf."""
	_tag_syscohada_tax_accounts(company_name)
	for number in ("4432", "4431", "443"):
		name = frappe.db.get_value(
			"Account",
			{"company": company_name, "account_number": number, "is_group": 0},
			"name",
		)
		if name:
			return name
	name = frappe.db.get_value(
		"Account",
		{"company": company_name, "account_type": "Tax", "is_group": 0},
		"name",
	)
	if name:
		return name
	return frappe.db.get_value(
		"Account",
		{"company": company_name, "is_group": 0, "account_name": ["like", "%TVA%"]},
		"name",
	)


def _syscohada_bank_account(company_name):
	"""Classic bank (5211) — not Mobile Money."""
	for number in ("5211", "5215"):
		name = frappe.db.get_value(
			"Account",
			{"company": company_name, "account_number": number, "is_group": 0},
			"name",
		)
		if name:
			return name
	return frappe.db.get_value(
		"Account",
		{"company": company_name, "account_type": "Bank", "is_group": 0},
		"name",
	)


def _syscohada_cash_account(company_name):
	"""Espèces → 5711 Caisse en monnaie nationale."""
	name = frappe.db.get_value(
		"Account",
		{"company": company_name, "account_number": "5711", "is_group": 0},
		"name",
	)
	if name:
		# Tag Cash so MoP type=Cash validators / defaults work
		if frappe.db.get_value("Account", name, "account_type") != "Cash":
			frappe.db.set_value("Account", name, "account_type", "Cash", update_modified=False)
		return name
	return frappe.db.get_value(
		"Account",
		{"company": company_name, "account_type": "Cash", "is_group": 0},
		"name",
	)


def _ensure_mobile_money_account(company_name):
	"""Dedicated bank leaf 5218 under 521 — separate from 5211 for cashflow reporting."""
	existing = frappe.db.get_value(
		"Account",
		{"company": company_name, "account_number": "5218", "is_group": 0},
		"name",
	)
	if existing:
		if frappe.db.get_value("Account", existing, "account_type") != "Bank":
			frappe.db.set_value("Account", existing, "account_type", "Bank", update_modified=False)
		return existing

	parent = frappe.db.get_value(
		"Account",
		{"company": company_name, "account_number": "521", "is_group": 1},
		"name",
	)
	if not parent:
		frappe.logger().warning("No parent 521 for Mobile Money account — skip")
		return None

	doc = frappe.get_doc(
		{
			"doctype": "Account",
			"account_name": "Mobile Money",
			"account_number": "5218",
			"company": company_name,
			"parent_account": parent,
			"is_group": 0,
			"account_type": "Bank",
			"root_type": frappe.db.get_value("Account", parent, "root_type") or "Asset",
			"report_type": "Balance Sheet",
			"account_currency": frappe.get_cached_value("Company", company_name, "default_currency"),
		}
	)
	doc.flags.ignore_permissions = True
	doc.insert()
	return doc.name


def _null_company_account_links(company_name):
	"""Clear Company → Account links in DB (avoids LinkValidationError after CoA wipe)."""
	meta = frappe.get_meta("Company")
	for field in meta.fields:
		if field.fieldtype == "Link" and field.options == "Account":
			frappe.db.set_value("Company", company_name, field.fieldname, None, update_modified=False)


def _delete_company_tax_templates(company_name):
	for dt in ("Item Tax Template", "Sales Taxes and Charges Template"):
		if not frappe.db.exists("DocType", dt):
			continue
		for name in frappe.get_all(dt, {"company": company_name}, pluck="name"):
			frappe.delete_doc(dt, name, force=1, ignore_permissions=True)


def _ensure_syscohada_coa(company):
	"""Replace Standard CoA with SYSCOHADA+codes when no GL exists yet."""
	from erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts import create_charts
	from frappe.utils.nestedset import rebuild_tree

	has_syscohada = frappe.db.exists(
		"Account", {"company": company.name, "account_number": "5211"}
	)
	if company.chart_of_accounts == CHART_OF_ACCOUNTS and has_syscohada:
		return company

	if frappe.db.count("GL Entry", {"company": company.name}):
		frappe.throw(
			"Impossible de basculer vers SYSCOHADA : des écritures GL existent déjà "
			f"pour {company.name}. Migrer / mapper les comptes manuellement."
		)

	_delete_company_tax_templates(company.name)
	if frappe.db.exists("DocType", "Mode of Payment Account"):
		frappe.db.delete("Mode of Payment Account", {"company": company.name})

	_null_company_account_links(company.name)
	frappe.db.delete("Account", {"company": company.name})
	frappe.db.commit()
	rebuild_tree("Account")

	create_charts(company.name, CHART_OF_ACCOUNTS)
	frappe.db.commit()

	# Point company at new chart; set whatever English-named defaults exist (may be few on OHADA)
	frappe.db.set_value(
		"Company",
		company.name,
		{
			"chart_of_accounts": CHART_OF_ACCOUNTS,
			"create_chart_of_accounts_based_on": "Standard Template",
		},
		update_modified=False,
	)
	company = frappe.get_doc("Company", company.name)
	company.update_default_account = 1
	company.set_default_accounts()
	_null_company_account_links(company.name)  # drop any defaults that still point nowhere
	# Re-apply OHADA-friendly defaults we care about
	bank = _syscohada_bank_account(company.name)
	if bank:
		frappe.db.set_value("Company", company.name, "default_bank_account", bank)
	cash = _syscohada_cash_account(company.name)
	if cash:
		frappe.db.set_value("Company", company.name, "default_cash_account", cash)
	income = frappe.db.get_value(
		"Account",
		{"company": company.name, "account_number": "7061", "is_group": 0},
		"name",
	)
	if income:
		frappe.db.set_value("Company", company.name, "default_income_account", income)
	frappe.db.commit()
	return frappe.get_doc("Company", company.name)

def _ensure_mop(company_name, mop_name, mop_type, account):
	"""Ensure Mode of Payment exists and points at the given company account only."""
	if not frappe.db.exists("Mode of Payment", mop_name):
		frappe.get_doc(
			{
				"doctype": "Mode of Payment",
				"mode_of_payment": mop_name,
				"type": mop_type,
				"enabled": 1,
			}
		).insert(ignore_permissions=True)

	mop = frappe.get_doc("Mode of Payment", mop_name)
	mop.type = mop_type
	mop.enabled = 1
	mop.accounts = [r for r in mop.accounts if r.company != company_name]
	if account:
		mop.append("accounts", {"company": company_name, "default_account": account})
	mop.save(ignore_permissions=True)


def _ensure_payment_modes(company_name):
	"""Espèces → 5711 (caisse) ; Mobile Money → 5218 (banque dédiée)."""
	cash = _syscohada_cash_account(company_name)
	mm_account = _ensure_mobile_money_account(company_name)
	_ensure_mop(company_name, "Espèces", "Cash", cash)
	_ensure_mop(company_name, "Mobile Money", "Bank", mm_account)


def _ensure_genders():
	"""Fresh sites have empty Gender; Student/Employee/Guardian link Male|Female."""
	for name in ("Male", "Female"):
		if not frappe.db.exists("Gender", name):
			frappe.get_doc({"doctype": "Gender", "gender": name}).insert(ignore_permissions=True)


def seed():
	"""Create company Citigems Bilingual School (BJ, XOF, fr) + tax helpers."""
	frappe.flags.ignore_permissions = True
	_ensure_currency()
	_ensure_warehouse_types()
	_ensure_genders()
	company = _ensure_company()
	company = _ensure_syscohada_coa(company)
	_ensure_mecef_tax_templates(company.name)
	_ensure_payment_modes(company.name)

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
