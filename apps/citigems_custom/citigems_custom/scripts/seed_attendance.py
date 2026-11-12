"""Seed Student Attendance for pilot class — guide 10 / checklist 15_Presences.

  - Holiday List (weekends + congés Dec–Jan) on Company
  - Daily Present/Absent for B5 - 2026 from rentrée → today (weekdays)

  Uses education.education.api.mark_attendance (same as Student Attendance Tool).

  bench --site <site> execute citigems_custom.scripts.seed_attendance.seed
"""

from __future__ import annotations

import json
from datetime import date, timedelta

import frappe
from frappe.utils import getdate, today

from education.education.api import mark_attendance

COMPANY = "Citigems Bilingual School"
HOLIDAY_LIST = "Citigems 2026-2027"
STUDENT_GROUPS = ("B5 - 2026", "Nur 1 - 2026")
YEAR_START = date(2026, 9, 14)
HOLIDAY_START = date(2026, 12, 21)
HOLIDAY_END = date(2027, 1, 4)


def _ensure_holiday_list() -> str:
	if not frappe.db.exists("Holiday List", HOLIDAY_LIST):
		doc = frappe.get_doc(
			{
				"doctype": "Holiday List",
				"holiday_list_name": HOLIDAY_LIST,
				"from_date": "2026-09-01",
				"to_date": "2027-07-31",
				"weekly_off": "Saturday",
			}
		)
		# add Sunday as weekly off via holidays table (ERPNext allows one weekly_off)
		doc.get_weekly_off_dates()  # expands Saturdays into holidays
		# Sundays
		d = getdate(doc.from_date)
		end = getdate(doc.to_date)
		existing = {getdate(h.holiday_date) for h in doc.holidays}
		while d <= end:
			if d.weekday() == 6 and d not in existing:
				doc.append(
					"holidays",
					{"holiday_date": d, "description": "Sunday", "weekly_off": 1},
				)
			d += timedelta(days=1)
		# Christmas / New Year break (aligns with course schedule seed)
		break_d = HOLIDAY_START
		while break_d <= HOLIDAY_END:
			if break_d not in {getdate(h.holiday_date) for h in doc.holidays}:
				doc.append(
					"holidays",
					{
						"holiday_date": break_d,
						"description": "Congés scolaires",
					},
				)
			break_d += timedelta(days=1)
		doc.insert(ignore_permissions=True)
	else:
		doc = frappe.get_doc("Holiday List", HOLIDAY_LIST)

	frappe.db.set_value(
		"Company", COMPANY, "default_holiday_list", doc.name, update_modified=False
	)
	return doc.name


def _teaching_days_until(end: date) -> list[date]:
	days: list[date] = []
	d = YEAR_START
	while d <= end:
		if d.weekday() < 5 and not (HOLIDAY_START <= d <= HOLIDAY_END):
			days.append(d)
		d += timedelta(days=1)
	return days


def _students(group: str) -> list[dict]:
	return frappe.get_all(
		"Student Group Student",
		filters={"parent": group, "active": 1},
		fields=["student", "student_name"],
		order_by="group_roll_number",
	)


def _already_marked(group: str, day: date) -> bool:
	return bool(
		frappe.db.exists(
			"Student Attendance",
			{
				"student_group": group,
				"date": day,
				"docstatus": 1,
			},
		)
	)


def _mark_day(group: str, day: date, students: list[dict], absent_student: str | None) -> str:
	present = []
	absent = []
	for s in students:
		row = {"student": s.student, "student_name": s.student_name}
		if absent_student and s.student == absent_student:
			absent.append(row)
		else:
			present.append(row)
	mark_attendance(
		json.dumps(present),
		json.dumps(absent),
		course_schedule=None,
		student_group=group,
		date=str(day),
	)
	return "marked"


def seed() -> dict:
	_ensure_holiday_list()
	end = min(getdate(today()), date(2026, 12, 20))
	days = _teaching_days_until(end)
	absent_day = days[len(days) // 2] if days else None

	from citigems_custom.education_report import get_attendance_count

	groups_out = {}
	for group in STUDENT_GROUPS:
		students = _students(group)
		if not students:
			frappe.throw(f"Aucun élève actif dans {group}")

		# deliberate absences for portal/bulletin demo
		if group.startswith("B5"):
			absent_id = next(
				(s.student for s in students if "Fassinou" in (s.student_name or "")),
				students[-1].student,
			)
		else:
			absent_id = next(
				(s.student for s in students if "Dossou" in (s.student_name or "")),
				students[0].student,
			)

		stats = {"marked": 0, "skipped": 0, "days": len(days)}
		for day in days:
			if _already_marked(group, day):
				stats["skipped"] += 1
				continue
			_mark_day(group, day, students, absent_id if day == absent_day else None)
			stats["marked"] += 1

		checks = {}
		for s in students:
			att = get_attendance_count(s.student, "2026-2027")
			checks[s.student_name] = dict(att)
			assert att.total > 0, s.student_name

		groups_out[group] = {
			"stats": stats,
			"attendance": checks,
			"total_records": frappe.db.count(
				"Student Attendance", {"student_group": group, "docstatus": 1}
			),
		}

	frappe.db.commit()
	out = {"holiday_list": HOLIDAY_LIST, "groups": groups_out}
	print(out)
	return out

