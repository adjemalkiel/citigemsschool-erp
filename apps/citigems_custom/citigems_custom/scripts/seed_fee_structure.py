"""Seed Fee Categories + Fee Structures — guide 9.1 / checklist 11 + 12.

  - 6 Fee Categories (catalogue)
  - Fee Structures 2026-2027 / Régulier : scolarité par classe,
    fournitures par palier, cantine / uniforme / inscription (tous)

  Les sorties : catégorie seule (pas de montant dans 12_Grille_tarifaire).

  bench --site <site> execute citigems_custom.scripts.seed_fee_structure.seed
"""

from __future__ import annotations

import frappe

COMPANY = "Citigems Bilingual School"
ACADEMIC_YEAR = "2026-2027"
STUDENT_CATEGORY = "Régulier"
INCOME_ACCOUNT = "7061 - Dans la Région - CBS"  # leaf (706 is group)
RECEIVABLE_ACCOUNT = "4111 - Clients - CBS"
COST_CENTER = "Main - CBS"

# (category_name, description)
CATEGORIES: list[tuple[str, str]] = [
	("Scolarité / School Fees", "Frais de scolarité"),
	("Cantine / Canteen", "Cantine"),
	("Inscription / Registration", "Frais d’inscription"),
	("Uniforme / Uniform", "Uniforme scolaire"),
	("Fournitures / Books", "Fournitures scolaire"),
	("Les sorties", "Activite Extra Scolaires"),
]

# (label, program, [(fees_category, amount), ...])
# label → renamed Fee Structure name for desk readability
STRUCTURES: list[tuple[str, str, list[tuple[str, float]]]] = [
	# Scolarité par classe (12_Grille_tarifaire)
	("Scolarité Pre-Nursery 2026-2027", "Nursery / Maternelle", [("Scolarité / School Fees", 75000)]),
	("Scolarité Nursery 1 2026-2027", "Nursery / Maternelle", [("Scolarité / School Fees", 119000)]),
	("Scolarité Nursery 2 2026-2027", "Nursery / Maternelle", [("Scolarité / School Fees", 119000)]),
	("Scolarité Basic 1 2026-2027", "Primary / Primaire", [("Scolarité / School Fees", 157000)]),
	("Scolarité Basic 2 2026-2027", "Primary / Primaire", [("Scolarité / School Fees", 157000)]),
	("Scolarité Basic 3 2026-2027", "Primary / Primaire", [("Scolarité / School Fees", 167000)]),
	("Scolarité Basic 4 2026-2027", "Primary / Primaire", [("Scolarité / School Fees", 167000)]),
	("Scolarité Basic 5 2026-2027", "Primary / Primaire", [("Scolarité / School Fees", 172000)]),
	("Scolarité Basic 6 2026-2027", "Primary / Primaire", [("Scolarité / School Fees", 172000)]),
	# Fournitures (Mat 1–2 / CI–CM2 ; Pre-Nursery = 0 → omis)
	("Fournitures Nursery 2026-2027", "Nursery / Maternelle", [("Fournitures / Books", 15000)]),
	("Fournitures Primary 2026-2027", "Primary / Primaire", [("Fournitures / Books", 25000)]),
	# Frais communs (*) — une structure par programme pour le lien Program
	("Cantine Nursery 2026-2027", "Nursery / Maternelle", [("Cantine / Canteen", 124500)]),
	("Cantine Primary 2026-2027", "Primary / Primaire", [("Cantine / Canteen", 124500)]),
	("Uniforme Nursery 2026-2027", "Nursery / Maternelle", [("Uniforme / Uniform", 20000)]),
	("Uniforme Primary 2026-2027", "Primary / Primaire", [("Uniforme / Uniform", 20000)]),
	("Inscription Nursery 2026-2027", "Nursery / Maternelle", [("Inscription / Registration", 5000)]),
	("Inscription Primary 2026-2027", "Primary / Primaire", [("Inscription / Registration", 5000)]),
]


def _ensure_uom() -> None:
	if not frappe.db.exists("UOM", "Nos"):
		frappe.get_doc({"doctype": "UOM", "uom_name": "Nos"}).insert(ignore_permissions=True)
	ss = frappe.get_single("Stock Settings")
	if ss.stock_uom != "Nos":
		ss.stock_uom = "Nos"
		ss.save(ignore_permissions=True)


def _ensure_fee_item(name: str, description: str) -> str:
	"""Education create_item omits stock_uom; pre-create so after_insert reuses it."""
	# db.exists can miss just-inserted rows in the same request; SQL is definitive.
	if frappe.db.get_value("Item", name, "name"):
		return name
	item = frappe.get_doc(
		{
			"doctype": "Item",
			"item_code": name,
			"item_name": name,
			"description": description,
			"item_group": "Fee Component",
			"stock_uom": "Nos",
			"is_stock_item": 0,
			"is_sales_item": 1,
			"is_service_item": 1,
			"item_defaults": [
				{
					"company": COMPANY,
					"income_account": INCOME_ACCOUNT,
					"selling_cost_center": COST_CENTER,
				}
			],
		}
	)
	item.insert(ignore_permissions=True)
	return item.name


def _ensure_category(name: str, description: str) -> tuple[str, str]:
	_ensure_fee_item(name, description)
	if frappe.db.exists("Fee Category", name):
		doc = frappe.get_doc("Fee Category", name)
		changed = False
		if doc.description != description:
			doc.description = description
			changed = True
		if not doc.item:
			doc.item = name
			changed = True
		if not any(d.company == COMPANY for d in doc.item_defaults):
			doc.append(
				"item_defaults",
				{
					"company": COMPANY,
					"income_account": INCOME_ACCOUNT,
					"selling_cost_center": COST_CENTER,
				},
			)
			changed = True
		if changed:
			doc.save(ignore_permissions=True)
			return name, "updated"
		return name, "exists"

	doc = frappe.get_doc(
		{
			"doctype": "Fee Category",
			"category_name": name,
			"description": description,
			"item": name,
			"item_defaults": [
				{
					"company": COMPANY,
					"income_account": INCOME_ACCOUNT,
					"selling_cost_center": COST_CENTER,
				}
			],
		}
	)
	doc.insert(ignore_permissions=True)
	return name, "created"


def _structure_exists(label: str) -> bool:
	return bool(frappe.db.get_value("Fee Structure", label, "name"))


def _ensure_structure(label: str, program: str, components: list[tuple[str, float]]) -> tuple[str, str]:
	# ponytail: same XOF amounts on sibling classes (N1=N2, B1=B2…) — match by label only,
	# never by component totals (that collapses tiers).
	if _structure_exists(label):
		doc = frappe.get_doc("Fee Structure", label)
		if doc.docstatus == 1:
			return label, "exists"
		doc.program = program
		doc.student_category = STUDENT_CATEGORY
		doc.academic_year = ACADEMIC_YEAR
		doc.receivable_account = RECEIVABLE_ACCOUNT
		doc.company = COMPANY
		doc.cost_center = COST_CENTER
		doc.set("components", [])
		for cat, amount in components:
			doc.append("components", {"fees_category": cat, "amount": amount})
		doc.save(ignore_permissions=True)
		doc.submit()
		return label, "updated"

	doc = frappe.get_doc(
		{
			"doctype": "Fee Structure",
			"program": program,
			"student_category": STUDENT_CATEGORY,
			"academic_year": ACADEMIC_YEAR,
			"receivable_account": RECEIVABLE_ACCOUNT,
			"company": COMPANY,
			"cost_center": COST_CENTER,
			"components": [
				{"fees_category": cat, "amount": amount} for cat, amount in components
			],
		}
	)
	doc.insert(ignore_permissions=True)
	doc.submit()
	if doc.name != label:
		frappe.rename_doc("Fee Structure", doc.name, label, force=True, merge=False)
	return label, "created"


def seed() -> dict:
	frappe.flags.in_import = True
	_ensure_uom()

	cats: dict[str, int] = {"created": 0, "updated": 0, "exists": 0}
	for name, desc in CATEGORIES:
		_, st = _ensure_category(name, desc)
		cats[st] += 1

	structs: dict[str, int] = {"created": 0, "updated": 0, "exists": 0}
	for label, program, comps in STRUCTURES:
		_, st = _ensure_structure(label, program, comps)
		structs[st] += 1

	frappe.db.commit()
	# smallest check: every labelled structure submitted with expected total
	for label, _program, comps in STRUCTURES:
		total = frappe.db.get_value("Fee Structure", label, ["total_amount", "docstatus"], as_dict=True)
		assert total and total.docstatus == 1, label
		assert float(total.total_amount) == float(sum(a for _, a in comps)), (
			label,
			total.total_amount,
			comps,
		)

	out = {
		"fee_categories": cats,
		"fee_structures": structs,
		"totals": {
			"categories": frappe.db.count("Fee Category"),
			"structures": frappe.db.count("Fee Structure", {"docstatus": 1}),
		},
	}
	print(out)
	return out
