"""Seed invoice tax for school fees — guide 9.2 / MeCeF groupes A–B.

  - Ensure Item Tax Templates A (0 %) / B (18 %) + Sales Taxes B (from seed_citigems)
  - Sales Taxes template Groupe A (exonéré) if missing
  - Tag all Fee Component items with Groupe A (scolarité exonérée)

  bench --site <site> execute citigems_custom.scripts.seed_fee_tax.seed
"""

from __future__ import annotations

import frappe

from citigems_custom.scripts.seed_citigems import (
	_ensure_mecef_tax_templates,
	_syscohada_tax_account,
)

COMPANY = "Citigems Bilingual School"
GROUP_A_ITEM = "MECeF Groupe A — Exonéré"
GROUP_A_SALES = "MECeF Exonéré (Groupe A)"


def _ensure_sales_template_a() -> str:
	"""0 % Sales Taxes template tagged mecef_tax_group=A (mirror of Groupe B)."""
	existing = frappe.db.get_value(
		"Sales Taxes and Charges Template",
		{"company": COMPANY, "mecef_tax_group": "A"},
		"name",
	)
	if existing:
		return existing

	if not frappe.db.exists(
		"Custom Field",
		{"dt": "Sales Taxes and Charges Template", "fieldname": "mecef_tax_group"},
	):
		return ""

	tax_account = _syscohada_tax_account(COMPANY)
	if not tax_account:
		return ""

	doc = frappe.get_doc(
		{
			"doctype": "Sales Taxes and Charges Template",
			"title": GROUP_A_SALES,
			"company": COMPANY,
			"mecef_tax_group": "A",
			"taxes": [
				{
					"doctype": "Sales Taxes and Charges",
					"charge_type": "On Net Total",
					"account_head": tax_account,
					"description": "Exonéré (Groupe A)",
					"rate": 0,
				}
			],
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _item_tax_template_a() -> str:
	name = frappe.db.get_value(
		"Item Tax Template",
		{"title": GROUP_A_ITEM, "company": COMPANY},
		"name",
	)
	if not name:
		frappe.throw(f"Item Tax Template « {GROUP_A_ITEM} » manquant pour {COMPANY}")
	return name


def _tag_fee_items(template: str) -> dict[str, int]:
	stats = {"tagged": 0, "exists": 0}
	items = frappe.get_all(
		"Item",
		filters={"item_group": "Fee Component", "disabled": 0},
		pluck="name",
	)
	for item_name in items:
		doc = frappe.get_doc("Item", item_name)
		if any(r.item_tax_template == template for r in doc.taxes):
			stats["exists"] += 1
			continue
		# replace empty / wrong fee tax rows with Groupe A
		doc.set("taxes", [])
		doc.append("taxes", {"item_tax_template": template})
		doc.save(ignore_permissions=True)
		stats["tagged"] += 1
	return stats


def seed() -> dict:
	_ensure_mecef_tax_templates(COMPANY)
	sales_a = _ensure_sales_template_a()
	template_a = _item_tax_template_a()
	items = _tag_fee_items(template_a)
	frappe.db.commit()

	out = {
		"item_tax_template_a": template_a,
		"sales_taxes_a": sales_a,
		"fee_items": items,
		"templates": {
			"item": frappe.get_all(
				"Item Tax Template",
				filters={"company": COMPANY},
				fields=["name", "mecef_tax_group"],
			),
			"sales": frappe.get_all(
				"Sales Taxes and Charges Template",
				filters={"company": COMPANY},
				fields=["name", "mecef_tax_group"],
			),
		},
	}
	# check: every Fee Component item carries Groupe A
	untagged = frappe.db.sql(
		"""
		select i.name from tabItem i
		left join `tabItem Tax` t on t.parent = i.name and t.item_tax_template = %s
		where i.item_group = 'Fee Component' and i.disabled = 0 and t.name is null
		""",
		template_a,
	)
	assert not untagged, untagged
	print(out)
	return out
