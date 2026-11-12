"""Parent / student portal dashboard (fees, schedule, attendance, program)."""

from __future__ import annotations

from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import getdate, today


def _require_portal_user() -> str:
	user = frappe.session.user
	if not user or user == "Guest":
		frappe.throw(_("Connectez-vous pour accéder au portail."), frappe.PermissionError)
	return user


def _students_for_user(user: str) -> list[dict]:
	roles = set(frappe.get_roles(user))
	out: list[dict] = []

	if "Student" in roles:
		own = frappe.db.get_value(
			"Student",
			{"user": user},
			["name", "student_name", "customer", "image", "joining_date"],
			as_dict=True,
		)
		if own:
			out.append(own)

	if "Guardian" in roles:
		guardian = frappe.db.get_value("Guardian", {"user": user}, "name")
		if guardian:
			for row in frappe.get_all(
				"Student Guardian",
				filters={"guardian": guardian},
				fields=["parent"],
			):
				stu = frappe.db.get_value(
					"Student",
					row.parent,
					["name", "student_name", "customer", "image", "joining_date"],
					as_dict=True,
				)
				if stu and stu.name not in {s.name for s in out}:
					out.append(stu)

	return out


def _assert_student_access(student_id: str, user: str) -> None:
	allowed = {s.name for s in _students_for_user(user)}
	if student_id not in allowed and not (
		set(frappe.get_roles(user)) & {"System Manager", "Education Manager", "Accounts Manager"}
	):
		frappe.throw(_("Accès non autorisé à cet élève."), frappe.PermissionError)


def _enrollment(student_id: str) -> dict | None:
	rows = frappe.get_all(
		"Program Enrollment",
		filters={"student": student_id, "docstatus": 1},
		fields=[
			"name",
			"program",
			"academic_year",
			"academic_term",
			"student_batch_name",
			"student_category",
		],
		order_by="creation desc",
		limit_page_length=1,
	)
	return rows[0] if rows else None


def _student_group(student_id: str) -> str | None:
	rows = frappe.get_all(
		"Student Group Student",
		filters={"student": student_id, "active": 1},
		fields=["parent"],
		order_by="modified desc",
		limit_page_length=1,
	)
	return rows[0].parent if rows else None


def _program_courses(program: str | None) -> list[dict]:
	if not program:
		return []
	return frappe.get_all(
		"Program Course",
		filters={"parent": program},
		fields=["course", "course_name"],
		order_by="idx asc",
	)


def _fee_plan(program: str | None, student_group: str | None = None) -> list[dict]:
	"""Fee structures for the student's program (catalogue / échéances prévues)."""
	if not program:
		return []
	rows = frappe.get_all(
		"Fee Structure",
		filters={"program": program, "docstatus": 1, "academic_year": "2026-2027"},
		fields=["name", "total_amount", "student_category"],
		order_by="name asc",
	)
	# Drop sibling-class scolarité (keep shared Nursery/Primary lines)
	short = ((student_group or "").split(" - ")[0] or "").strip()  # "Nur 1" / "B5"
	filtered = []
	for fs in rows:
		n = fs.name
		if "Scolarité" in n or "Scolarite" in n:
			if short.startswith("Nur 1") and "Nursery 1" not in n:
				continue
			if short.startswith("Nur 2") and "Nursery 2" not in n:
				continue
			if short.startswith("B") and short[1:].isdigit() and f"Basic {short[1:]}" not in n:
				continue
		filtered.append(fs)

	plan = []
	for fs in filtered:
		components = frappe.get_all(
			"Fee Component",
			filters={"parent": fs.name},
			fields=["fees_category", "amount"],
			order_by="idx asc",
		)
		plan.append(
			{
				"name": fs.name,
				"total_amount": float(fs.total_amount or 0),
				"student_category": fs.student_category,
				"components": components,
			}
		)
	return plan


def _invoices_for_customer(customer: str | None) -> list[dict]:
	if not customer:
		return []
	rows = frappe.get_all(
		"Sales Invoice",
		filters={"customer": customer, "docstatus": 1},
		fields=[
			"name",
			"customer",
			"customer_name",
			"posting_date",
			"due_date",
			"grand_total",
			"outstanding_amount",
			"paid_amount",
			"currency",
			"status",
			"company",
		],
		order_by="due_date asc, posting_date asc",
	)
	out = []
	for inv in rows:
		# label = first item description / item_code
		item = frappe.db.get_value(
			"Sales Invoice Item",
			{"parent": inv.name},
			["item_code", "item_name", "description"],
			as_dict=True,
		)
		label = (item.item_name or item.item_code or inv.name) if item else inv.name
		outstanding = float(inv.outstanding_amount or 0)
		out.append(
			{
				**inv,
				"label": label,
				"grand_total": float(inv.grand_total or 0),
				"outstanding_amount": outstanding,
				"paid_amount": float(inv.paid_amount or 0),
				"is_paid": outstanding <= 0,
				"status_key": "paid" if outstanding <= 0 else "due",
			}
		)
	return out


def _week_bounds(ref=None) -> tuple:
	d = getdate(ref or today())
	monday = d - timedelta(days=d.weekday())
	friday = monday + timedelta(days=4)
	return monday, friday


def _fmt_time(val) -> str:
	if not val:
		return ""
	parts = str(val).split(":")
	try:
		return f"{int(parts[0]):02d}:{int(parts[1]):02d}"
	except (TypeError, ValueError, IndexError):
		return str(val)[:5]


def _schedule(student_group: str | None, ref=None) -> list[dict]:
	if not student_group:
		return []
	start, end = _week_bounds(ref)
	rows = frappe.get_all(
		"Course Schedule",
		filters={
			"student_group": student_group,
			"schedule_date": ["between", [start, end]],
		},
		fields=[
			"name",
			"schedule_date",
			"from_time",
			"to_time",
			"course",
			"room",
			"instructor_name",
			"title",
		],
		order_by="schedule_date asc, from_time asc",
	)
	room_names = {}
	for r in rows:
		r["schedule_date"] = str(r.schedule_date)
		r["from_time"] = _fmt_time(r.from_time)
		r["to_time"] = _fmt_time(r.to_time)
		r["weekday"] = getdate(r.schedule_date).weekday()  # 0=Mon
		if r.room and r.room not in room_names:
			room_names[r.room] = (
				frappe.db.get_value("Room", r.room, "room_name") or r.room
			)
		r["room"] = room_names.get(r.room, r.room)
	return rows


def _attendance(student_id: str) -> dict:
	rows = frappe.get_all(
		"Student Attendance",
		filters={"student": student_id, "docstatus": 1},
		fields=["date", "status", "student_group"],
		order_by="date desc",
		limit_page_length=200,
	)
	present = sum(1 for r in rows if r.status == "Present")
	absent = sum(1 for r in rows if r.status == "Absent")
	absences = [
		{"date": str(r.date), "status": r.status, "student_group": r.student_group}
		for r in rows
		if r.status == "Absent"
	][:30]
	return {
		"present": present,
		"absent": absent,
		"total": present + absent,
		"absences": absences,
	}


@frappe.whitelist()
def get_dashboard(student: str | None = None) -> dict:
	"""Full parent/student portal payload for one child."""
	user = _require_portal_user()
	students = _students_for_user(user)
	if not students:
		return {"students": [], "student": None}

	selected = student or students[0].name
	_assert_student_access(selected, user)
	stu = next((s for s in students if s.name == selected), students[0])

	enr = _enrollment(stu.name)
	group = _student_group(stu.name)
	program = enr.program if enr else None

	return {
		"students": [
			{"name": s.name, "student_name": s.student_name, "image": s.image} for s in students
		],
		"student": {
			"name": stu.name,
			"student_name": stu.student_name,
			"image": stu.image,
			"joining_date": str(stu.joining_date) if stu.joining_date else None,
			"customer": stu.customer,
			"student_group": group,
			"enrollment": enr,
			"program_courses": _program_courses(program),
		},
		"fee_plan": _fee_plan(program, group),
		"invoices": _invoices_for_customer(stu.customer),
		"schedule": _schedule(group),
		"schedule_week": {
			"from": str(_week_bounds()[0]),
			"to": str(_week_bounds()[1]),
		},
		"attendance": _attendance(stu.name),
	}
