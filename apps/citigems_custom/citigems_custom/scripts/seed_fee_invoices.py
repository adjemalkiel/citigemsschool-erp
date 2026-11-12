"""Seed Fee Schedule + Sales Invoices for pilot payment test — guide 9.3.

  Échéance 1 — 70 000 XOF/FCFA (checklist 13):
  - B5 / CM1 (groupe B5 - 2026)
  - Nur 1 (groupe Nur 1 - 2026) — so parent.dossou portal has fees to pay

  bench --site <site> execute citigems_custom.scripts.seed_fee_invoices.seed
"""

from __future__ import annotations

import frappe
from frappe.utils import add_days, today

COMPANY = "Citigems Bilingual School"
ACADEMIC_YEAR = "2026-2027"
RECEIVABLE = "4111 - Clients - CBS"
INCOME = "7061 - Dans la Région - CBS"
ECHEANCE_1_AMOUNT = 70000
PRICE_LIST = "Standard Selling"
ITEM_TAX_A = "MECeF Groupe A — Exonéré - CBS"

# (fee_structure, student_group, program)
TARGETS = (
	("Scolarité Basic 5 2026-2027", "B5 - 2026", "Primary / Primaire"),
	("Scolarité Nursery 1 2026-2027", "Nur 1 - 2026", "Nursery / Maternelle"),
)

# Extra échéances for Nur 1 portal demo (item_code, amount) — no Fee Schedule required
NUR1_EXTRA = (
	("Inscription / Registration", 5000),
	("Fournitures / Books", 15000),
	("Uniforme / Uniform", 20000),
	("Scolarité / School Fees", 49000),  # échéance 2 (reste après 70 000)
)
NUR1_GROUP = "Nur 1 - 2026"


def _ensure_xof_fcfa_parity() -> None:
	# FCFA is XOF display symbol only (locale.ensure_xof_fcfa_display) — not a Currency.
	from citigems_custom.locale import ensure_xof_fcfa_display

	ensure_xof_fcfa_display()


def _ensure_fiscal_year() -> None:
	year = "2026"
	if not frappe.db.exists("Fiscal Year", year):
		frappe.get_doc(
			{
				"doctype": "Fiscal Year",
				"year": year,
				"year_start_date": "2026-01-01",
				"year_end_date": "2026-12-31",
				"companies": [{"company": COMPANY}],
			}
		).insert(ignore_permissions=True)
	elif not frappe.db.exists(
		"Fiscal Year Company", {"parent": year, "company": COMPANY}
	):
		fy = frappe.get_doc("Fiscal Year", year)
		fy.append("companies", {"company": COMPANY})
		fy.save(ignore_permissions=True)


def _ensure_party_type_customer() -> None:
	if not frappe.db.exists("Party Type", "Customer"):
		frappe.get_doc(
			{"doctype": "Party Type", "party_type": "Customer", "account_type": "Receivable"}
		).insert(ignore_permissions=True)


def _ensure_round_off() -> str:
	name = frappe.db.get_value(
		"Account", {"company": COMPANY, "account_name": "Round Off", "is_group": 0}, "name"
	)
	if name:
		return name
	parent = frappe.db.get_value(
		"Account", {"company": COMPANY, "account_number": "65", "is_group": 1}, "name"
	)
	doc = frappe.get_doc(
		{
			"doctype": "Account",
			"account_name": "Round Off",
			"parent_account": parent,
			"company": COMPANY,
			"account_type": "Expense Account",
			"root_type": "Expense",
			"is_group": 0,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _fix_fee_income_accounts() -> None:
	for name in frappe.get_all(
		"Item", filters={"item_group": "Fee Component"}, pluck="name"
	):
		doc = frappe.get_doc("Item", name)
		changed = False
		for row in doc.item_defaults:
			if row.income_account != INCOME:
				row.income_account = INCOME
				changed = True
		if not doc.item_defaults:
			doc.append(
				"item_defaults",
				{
					"company": COMPANY,
					"income_account": INCOME,
					"selling_cost_center": "Main - CBS",
				},
			)
			changed = True
		if changed:
			doc.save(ignore_permissions=True)


def _prep_accounts() -> None:
	_ensure_xof_fcfa_parity()
	_ensure_fiscal_year()
	_ensure_party_type_customer()
	_fix_fee_income_accounts()
	round_off = _ensure_round_off()

	co = frappe.get_doc("Company", COMPANY)
	co.default_receivable_account = RECEIVABLE
	co.round_off_account = round_off
	co.round_off_cost_center = "Main - CBS"
	if not co.default_income_account:
		co.default_income_account = INCOME
	co.save(ignore_permissions=True)

	es = frappe.get_single("Education Settings")
	if not es.auto_submit_sales_invoice:
		es.auto_submit_sales_invoice = 1
		es.flags.ignore_mandatory = True
		es.save(ignore_permissions=True)

	if not frappe.db.exists("Price List", PRICE_LIST):
		frappe.get_doc(
			{
				"doctype": "Price List",
				"price_list_name": PRICE_LIST,
				"selling": 1,
				"currency": "XOF",
			}
		).insert(ignore_permissions=True)
	ss = frappe.get_single("Selling Settings")
	if ss.selling_price_list != PRICE_LIST:
		ss.selling_price_list = PRICE_LIST
		ss.save(ignore_permissions=True)


def _ensure_schedule(fee_structure: str, student_group: str, program: str) -> tuple[str, str]:
	existing = frappe.db.get_value(
		"Fee Schedule",
		{
			"fee_structure": fee_structure,
			"academic_year": ACADEMIC_YEAR,
			"docstatus": 1,
			"status": "Invoice Created",
		},
		"name",
	)
	if existing and frappe.db.exists(
		"Fee Schedule Student Group",
		{"parent": existing, "student_group": student_group},
	):
		return existing, "exists"

	n_students = frappe.db.count("Student Group Student", {"parent": student_group})
	doc = frappe.get_doc(
		{
			"doctype": "Fee Schedule",
			"fee_structure": fee_structure,
			"posting_date": today(),
			"due_date": add_days(today(), 30),
			"academic_year": ACADEMIC_YEAR,
			"student_category": "Régulier",
			"program": program,
			"currency": "XOF",
			"receivable_account": RECEIVABLE,
			"company": COMPANY,
			"cost_center": "Main - CBS",
			"student_groups": [
				{"student_group": student_group, "total_students": n_students or 1}
			],
			"components": [
				{
					"fees_category": "Scolarité / School Fees",
					"amount": ECHEANCE_1_AMOUNT,
					"total": ECHEANCE_1_AMOUNT,
				}
			],
		}
	)
	doc.insert(ignore_permissions=True)
	doc.submit()
	return doc.name, "created"


def _ensure_customer_account(customer: str) -> None:
	if frappe.db.exists("Party Account", {"parent": customer, "company": COMPANY}):
		return
	cust = frappe.get_doc("Customer", customer)
	cust.append("accounts", {"company": COMPANY, "account": RECEIVABLE})
	cust.save(ignore_permissions=True)


def _create_invoice(
	student_id: str,
	schedule: str | None,
	amount: float = ECHEANCE_1_AMOUNT,
	item_code: str = "Scolarité / School Fees",
	due_in_days: int = 30,
) -> dict:
	from education.education.doctype.fee_schedule.fee_schedule import (
		get_customer_from_student,
	)

	customer = get_customer_from_student(student_id)
	_ensure_customer_account(customer)

	# idempotent: unpaid SI already for this customer + amount + item
	existing_rows = frappe.db.sql(
		"""
		SELECT si.name
		FROM `tabSales Invoice` si
		INNER JOIN `tabSales Invoice Item` it ON it.parent = si.name
		WHERE si.customer = %s
			AND si.docstatus = 1
			AND si.outstanding_amount > 0
			AND si.grand_total = %s
			AND it.item_code = %s
		LIMIT 1
		""",
		(customer, amount, item_code),
	)
	if existing_rows:
		return {"name": existing_rows[0][0], "status": "exists", "customer": customer}

	si = frappe.new_doc("Sales Invoice")
	si.customer = customer
	si.company = COMPANY
	si.posting_date = today()
	si.due_date = add_days(today(), due_in_days)
	si.currency = "XOF"
	si.conversion_rate = 1
	si.selling_price_list = PRICE_LIST
	si.price_list_currency = "XOF"
	si.plc_conversion_rate = 1
	si.debit_to = RECEIVABLE
	si.append(
		"items",
		{
			"item_code": item_code,
			"qty": 1,
			"rate": amount,
			"income_account": INCOME,
			"cost_center": "Main - CBS",
			"item_tax_template": ITEM_TAX_A,
		},
	)
	if si.meta.has_field("student"):
		si.student = student_id
	if schedule and si.meta.has_field("fee_schedule"):
		si.fee_schedule = schedule
	si.flags.ignore_permissions = True
	si.insert()
	si.submit()
	return {
		"name": si.name,
		"status": "created",
		"customer": customer,
		"item": item_code,
		"outstanding": float(si.outstanding_amount),
	}


def seed() -> dict:
	_prep_accounts()
	from education.education.doctype.fee_schedule.fee_schedule import get_students

	batches = []
	for fee_structure, student_group, program in TARGETS:
		schedule, st = _ensure_schedule(fee_structure, student_group, program)
		students = get_students(student_group, ACADEMIC_YEAR, None, "Régulier")
		invoices = [_create_invoice(s.student, schedule) for s in students]
		frappe.db.set_value("Fee Schedule", schedule, "status", "Invoice Created")
		batches.append(
			{
				"fee_schedule": schedule,
				"schedule_status": st,
				"student_group": student_group,
				"invoices": invoices,
			}
		)
		assert invoices, batches[-1]

	# Nur 1: inscription / fournitures / uniforme / scolarité échéance 2
	# Keep fee_schedule so portal Programme column resolves (stock API needs it).
	nur1_schedule = next(
		(b["fee_schedule"] for b in batches if b.get("student_group") == NUR1_GROUP),
		None,
	)
	extra = []
	nur_students = get_students(NUR1_GROUP, ACADEMIC_YEAR, None, "Régulier")
	due_offsets = {
		"Inscription / Registration": 7,
		"Fournitures / Books": 14,
		"Uniforme / Uniform": 21,
		"Scolarité / School Fees": 60,
	}
	for s in nur_students:
		for item_code, amount in NUR1_EXTRA:
			extra.append(
				_create_invoice(
					s.student,
					nur1_schedule,
					amount=amount,
					item_code=item_code,
					due_in_days=due_offsets.get(item_code, 30),
				)
			)

	frappe.db.commit()
	out = {"batches": batches, "nur1_extra": extra}
	print(out)
	return out
