"""Education SPA portal API overrides — Guardian can read own wards' data."""

from __future__ import annotations

import frappe
from frappe import _
from education.education.api import (
	check_permission,
	get_currency_symbol,
	get_fees_print_format,
	get_posting_date_from_payment_entry_against_sales_invoice,
	get_program_from_fee_schedule,
)

# Portal receipt: MECeF normalised invoice by default; Classic kept as setting fallback.
FEES_PRINT_MECEF = "Facture MECeF Citigems"
FEES_PRINT_CLASSIC = "Sales Invoice Classic"


def _portal_fees_print_format() -> str:
	"""Education Settings → Property Setter → MECeF → Classic."""
	for candidate in (
		frappe.db.get_single_value("Education Settings", "citigems_fees_print_format"),
		get_fees_print_format(),
		FEES_PRINT_MECEF,
		FEES_PRINT_CLASSIC,
	):
		if candidate and frappe.db.exists("Print Format", candidate):
			return candidate
	return "Standard"


@frappe.whitelist()
def get_student_invoices(student: str):
	"""Like education.api.get_student_invoices but ignore SI role perms after check."""
	check_permission(student, "invoices")

	sales_invoice_list = frappe.get_all(
		"Sales Invoice",
		filters={
			"student": student,
			"status": ["in", ["Paid", "Unpaid", "Overdue", "Partly Paid"]],
			"docstatus": 1,
		},
		fields=[
			"name",
			"status",
			"student",
			"due_date",
			"fee_schedule",
			"outstanding_amount",
			"currency",
			"grand_total",
		],
		order_by="status desc",
		ignore_permissions=True,
	)

	# Installment / manual SIs often omit fee_schedule → blank Programme in SPA.
	fallback_program = frappe.db.get_value(
		"Program Enrollment",
		{"student": student, "docstatus": 1},
		"program",
		order_by="creation desc",
	)

	student_sales_invoices = []
	for si in sales_invoice_list:
		symbol = get_currency_symbol(si.get("currency") or "XOF")
		program = (
			get_program_from_fee_schedule(si.fee_schedule) if si.fee_schedule else None
		) or fallback_program
		row = {
			"status": si.status,
			"program": program,
			"invoice": si.name,
		}
		if si.status == "Paid":
			row["amount"] = f"{symbol} {si.grand_total}"
			row["payment_date"] = get_posting_date_from_payment_entry_against_sales_invoice(
				si.name
			)
			row["due_date"] = "-"
		else:
			row["amount"] = f"{symbol} {si.outstanding_amount}"
			row["due_date"] = si.due_date
			row["payment_date"] = "-"
		# item label for clearer fees list
		item = frappe.db.get_value(
			"Sales Invoice Item",
			{"parent": si.name},
			["item_name", "item_code"],
			as_dict=True,
		)
		if item:
			row["label"] = item.item_name or item.item_code
		student_sales_invoices.append(row)

	return {
		"invoices": student_sales_invoices,
		"print_format": _portal_fees_print_format(),
	}


@frappe.whitelist()
def get_course_schedule_for_student(program_name: str, student_groups: list | str):
	"""Schedule by student_group (program backfilled); ignore Course Schedule perms."""
	if isinstance(student_groups, str):
		import json

		student_groups = json.loads(student_groups)
	labels = [sg.get("label") for sg in student_groups if sg.get("label")]
	if not labels:
		return []

	# any linked student for permission — take first group membership
	student = frappe.db.get_value(
		"Student Group Student",
		{"parent": labels[0], "active": 1},
		"student",
	)
	if student:
		check_permission(student, "schedule")

	return frappe.get_all(
		"Course Schedule",
		fields=[
			"schedule_date",
			"room",
			"class_schedule_color",
			"course",
			"from_time",
			"to_time",
			"instructor",
			"title",
			"name",
			"student_group",
		],
		filters={"student_group": ["in", labels]},
		order_by="schedule_date asc",
		ignore_permissions=True,
	)


@frappe.whitelist()
def get_student_attendance(student: str, student_group: str | None = None):
	"""Attendance events for SPA calendar (ignore perms after check)."""
	check_permission(student, "attendance")
	filters = {"student": student, "docstatus": 1}
	if student_group:
		filters["student_group"] = student_group
	return frappe.get_all(
		"Student Attendance",
		filters=filters,
		fields=["date", "status", "name"],
		order_by="date asc",
		ignore_permissions=True,
	)


@frappe.whitelist()
def get_student_leaves(student: str):
	"""Student Leave Application list for portal."""
	check_permission(student, "leaves")
	return frappe.get_all(
		"Student Leave Application",
		filters={"student": student},
		fields=[
			"name",
			"from_date",
			"to_date",
			"total_leave_days",
			"reason",
			"docstatus",
			"student_group",
		],
		order_by="from_date desc",
		ignore_permissions=True,
	)


@frappe.whitelist()
def get_student_diary(student: str):
	"""Student Log entries = school diary for parents/students."""
	check_permission(student, "diary")
	return frappe.get_all(
		"Student Log",
		filters={"student": student},
		fields=[
			"name",
			"date",
			"type",
			"log",
			"academic_year",
			"academic_term",
			"program",
			"student_batch",
		],
		order_by="date desc",
		ignore_permissions=True,
	)


def _ensure_perm(doctype: str, role: str, *, create: int = 0) -> None:
	exists = frappe.db.exists(
		"Custom DocPerm", {"parent": doctype, "role": role, "permlevel": 0}
	)
	vals = {"read": 1, "select": 1, "export": 1, "create": create, "write": create}
	if exists:
		frappe.db.set_value("Custom DocPerm", exists, vals)
		return
	frappe.get_doc(
		{
			"doctype": "Custom DocPerm",
			"parent": doctype,
			"parenttype": "DocType",
			"parentfield": "permissions",
			"role": role,
			"permlevel": 0,
			**vals,
		}
	).insert(ignore_permissions=True)


def seed_portal_demo_content() -> dict:
	"""Sample leave + diary lines for Nur 1 portal testing (Aïcha)."""
	student = frappe.db.get_value(
		"Student", {"student_name": "Aïcha Dossou"}, ["name", "student_name"], as_dict=True
	)
	if not student:
		return {"skipped": "no Aïcha"}

	created = {"leave": None, "logs": []}
	if not frappe.db.exists(
		"Student Leave Application",
		{"student": student.name, "from_date": "2026-10-13"},
	):
		leave = frappe.get_doc(
			{
				"doctype": "Student Leave Application",
				"student": student.name,
				"student_name": student.student_name,
				"from_date": "2026-10-13",
				"to_date": "2026-10-13",
				"total_leave_days": 1,
				"reason": "Rendez-vous médical",
				"attendance_based_on": "Student Group",
				"student_group": "Nur 1 - 2026",
			}
		)
		leave.insert(ignore_permissions=True)
		leave.submit()
		created["leave"] = leave.name

	samples = [
		("2026-09-20", "Achievement", "Bonne participation en pré-lecture."),
		("2026-10-05", "Academic", "Progrès en reconnaissance des chiffres."),
		(
			"2026-10-13",
			"Medical",
			"Absente (congé médical) — rattrapage lecture recommandé.",
		),
	]
	for date, typ, text in samples:
		if frappe.db.exists("Student Log", {"student": student.name, "date": date, "type": typ}):
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Student Log",
				"student": student.name,
				"student_name": student.student_name,
				"date": date,
				"type": typ,
				"log": text,
				"academic_year": "2026-2027",
				"program": "Nursery / Maternelle",
				"student_batch": "Nursery 1 / Maternelle 1",
			}
		)
		doc.insert(ignore_permissions=True)
		created["logs"].append(doc.name)

	frappe.db.commit()
	return created


def seed_portal_access() -> dict:
	"""Custom DocPerm for portal roles + schedule program backfill + demo content."""
	read_docs = (
		"Sales Invoice",
		"Student Attendance",
		"Assessment Result",
		"Course Schedule",
		"Program Enrollment",
		"Student",
		"Fee Schedule",
		"Student Log",
		"Student Leave Application",
	)
	for role in ("Guardian", "Student"):
		for dt in read_docs:
			create = 1 if dt == "Student Leave Application" else 0
			_ensure_perm(dt, role, create=create)

	for g in frappe.get_all("Student Group", fields=["name", "program"]):
		if not g.program:
			continue
		frappe.db.sql(
			"""
			UPDATE `tabCourse Schedule`
			SET program=%s
			WHERE student_group=%s AND IFNULL(program, '')=''
			""",
			(g.program, g.name),
		)
	demo = seed_portal_demo_content()
	frappe.db.commit()
	frappe.clear_cache()
	return {
		"schedule_programs": frappe.db.sql(
			"SELECT program, COUNT(*) FROM `tabCourse Schedule` GROUP BY program"
		),
		"demo": demo,
	}
