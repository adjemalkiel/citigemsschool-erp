"""Frappe v16 broke Education's report-card attendance query.

``frappe.get_all(..., ["count(student) as count"])`` is rejected:
SQL functions are not allowed as strings in SELECT.

Replace get_attendance_count with the dict-syntax equivalent.
"""

from __future__ import annotations

_INSTALLED = False


def get_attendance_count(student, academic_year, academic_term=None):
	import frappe
	from frappe import _

	attendance = frappe._dict()
	attendance.total = 0
	from_date = to_date = None

	if academic_year:
		from_date, to_date = frappe.db.get_value(
			"Academic Year", academic_year, ["year_start_date", "year_end_date"]
		)
	elif academic_term:
		from_date, to_date = frappe.db.get_value(
			"Academic Term", academic_term, ["term_start_date", "term_end_date"]
		)

	if not (from_date and to_date):
		frappe.throw(_("Please enter the Academic Year and set the Start and End date."))

	data = frappe.get_all(
		"Student Attendance",
		filters={"student": student, "docstatus": 1, "date": ["between", (from_date, to_date)]},
		fields=["status", {"COUNT": "student", "as": "count"}],
		group_by="status",
	)
	for row in data:
		n = row.get("count") or 0
		if row.status == "Present":
			attendance.present = n
		if row.status == "Absent":
			attendance.absent = n
		attendance.total += n
	return attendance


def install_report_card_patch() -> None:
	global _INSTALLED
	if _INSTALLED:
		return
	try:
		from education.education.doctype.student_report_generation_tool import (
			student_report_generation_tool as mod,
		)
	except Exception:
		return
	mod.get_attendance_count = get_attendance_count
	_INSTALLED = True
