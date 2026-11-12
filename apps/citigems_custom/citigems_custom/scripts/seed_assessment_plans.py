"""Seed Assessment Criteria + pilot Assessment Plans — guide 8.3 / SCORE.

Pilots (T1, Saturdays to avoid Course Schedule overlap):
  - B5 - 2026: CA Class Test / Mid Term / Examination on core subjects + Skills
  - Nur 1 - 2026: Nursery Mid Term / Examination on alphabet & numbers

  bench --site <site> execute citigems_custom.scripts.seed_assessment_plans.seed
"""

from __future__ import annotations

from datetime import date, time

import frappe

ACADEMIC_YEAR = "2026-2027"
ACADEMIC_TERM = "2026-2027 (T1)"

CRITERIA = [
	"Note obtenue",  # Marks Obtainable (avoid reserved name "Score")
	"Devoir",
	"Composition",
	"Oral",
]

# (student_group, assessment_group, course, grading_scale, max_score, schedule_date, from_h, to_h, criterion)
# Times staggered per day so same class does not overlap.
PRIMARY_GROUP = "B5 - 2026"
NURSERY_GROUP = "Nur 1 - 2026"

PRIMARY_INSTRUCTOR = "Emile"
NURSERY_INSTRUCTOR = "Tessy"
PRIMARY_ROOM = "Basic 5 / CM1"
NURSERY_ROOM = "Nursery 1"

# Saturdays in T1
DATE_CLASS_TEST = date(2026, 10, 17)
DATE_MID_TERM = date(2026, 11, 14)
DATE_SKILLS = date(2026, 11, 21)  # separate Saturday — no overlap with Mid Term CA
DATE_EXAM = date(2026, 12, 12)

PRIMARY_COURSES_CA = [
	"English Language",
	"Mathematics",
	"Français",
	"Mathématiques",
]

NURSERY_COURSES = [
	"Reading of Alphabet",
	"Counting of Numbers",
]


def _room(room_name: str) -> str:
	name = frappe.db.get_value("Room", {"room_name": room_name}, "name")
	if not name:
		frappe.throw(f"Room manquante: {room_name}")
	return name


def _ensure_criteria() -> list[str]:
	out = []
	for c in CRITERIA:
		if not frappe.db.exists("Assessment Criteria", c):
			frappe.get_doc({"doctype": "Assessment Criteria", "assessment_criteria": c}).insert(
				ignore_permissions=True
			)
		out.append(c)
	return out


def _plan_exists(student_group: str, course: str, assessment_group: str) -> str | None:
	return frappe.db.exists(
		"Assessment Plan",
		{
			"student_group": student_group,
			"course": course,
			"assessment_group": assessment_group,
			"docstatus": ("<", 2),
		},
	)


def _create_plan(
	*,
	student_group: str,
	assessment_group: str,
	course: str,
	grading_scale: str,
	max_score: float,
	schedule_date: date,
	from_time: str,
	to_time: str,
	criterion: str,
	examiner: str,
	room_name: str,
	assessment_name: str,
) -> tuple[str, bool]:
	existing = _plan_exists(student_group, course, assessment_group)
	if existing:
		doc = frappe.get_doc("Assessment Plan", existing)
		# submitted plans may lack term from earlier seeds — backfill quietly
		if not doc.academic_term:
			frappe.db.set_value(
				"Assessment Plan", doc.name, "academic_term", ACADEMIC_TERM, update_modified=False
			)
		if doc.docstatus == 0:
			doc.academic_term = ACADEMIC_TERM
			doc.save(ignore_permissions=True)
			doc.submit()
			return doc.name, True
		return doc.name, False

	doc = frappe.get_doc(
		{
			"doctype": "Assessment Plan",
			"student_group": student_group,
			"assessment_name": assessment_name,
			"assessment_group": assessment_group,
			"grading_scale": grading_scale,
			"course": course,
			"academic_year": ACADEMIC_YEAR,
			"academic_term": ACADEMIC_TERM,
			"schedule_date": schedule_date,
			"from_time": from_time,
			"to_time": to_time,
			"maximum_assessment_score": max_score,
			"examiner": examiner,
			"room": _room(room_name),
			"assessment_criteria": [
				{"assessment_criteria": criterion, "maximum_score": max_score},
			],
		}
	)
	doc.insert(ignore_permissions=True)
	doc.submit()
	return doc.name, True


def seed():
	"""Create criteria + submit pilot Assessment Plans for B5 and Nur 1."""
	frappe.flags.ignore_permissions = True
	for dt, name in (
		("Student Group", PRIMARY_GROUP),
		("Student Group", NURSERY_GROUP),
		("Academic Year", ACADEMIC_YEAR),
		("Academic Term", ACADEMIC_TERM),
		("Grading Scale", "Barème 100 points"),
		("Grading Scale", "Skills 1-5"),
		("Instructor", PRIMARY_INSTRUCTOR),
		("Instructor", NURSERY_INSTRUCTOR),
	):
		if not frappe.db.exists(dt, name):
			frappe.throw(f"{dt} manquant: {name}")

	_ensure_criteria()
	created, existing = [], []

	# Primary CA — 4 courses × 3 groups
	ca_slots = [
		("CA - Class Test", DATE_CLASS_TEST, "Note obtenue", 100.0, "Barème 100 points"),
		("CA - Mid Term", DATE_MID_TERM, "Note obtenue", 100.0, "Barème 100 points"),
		("CA - Examination", DATE_EXAM, "Composition", 100.0, "Barème 100 points"),
	]
	# hour offsets per course index
	base_hours = [(8, 9), (9, 10), (10, 11), (11, 12)]
	for ag, d, criterion, mx, scale in ca_slots:
		for i, course in enumerate(PRIMARY_COURSES_CA):
			fh, th = base_hours[i]
			name, is_new = _create_plan(
				student_group=PRIMARY_GROUP,
				assessment_group=ag,
				course=course,
				grading_scale=scale,
				max_score=mx,
				schedule_date=d,
				from_time=f"{fh:02d}:00:00",
				to_time=f"{th:02d}:00:00",
				criterion=criterion,
				examiner=PRIMARY_INSTRUCTOR,
				room_name=PRIMARY_ROOM,
				assessment_name=f"B5 {ag} — {course}",
			)
			(created if is_new else existing).append(name)

	# Primary Skills
	for ag, course, hour in (
		("Skills - Psychomotor", "Éducation corporelle / PHE", 8),
		("Skills - Affective", "Religious and National Values", 9),
	):
		name, is_new = _create_plan(
			student_group=PRIMARY_GROUP,
			assessment_group=ag,
			course=course,
			grading_scale="Skills 1-5",
			max_score=5.0,
			schedule_date=DATE_SKILLS,
			from_time=f"{hour:02d}:00:00",
			to_time=f"{hour+1:02d}:00:00",
			criterion="Note obtenue",
			examiner=PRIMARY_INSTRUCTOR,
			room_name=PRIMARY_ROOM,
			assessment_name=f"B5 {ag}",
		)
		(created if is_new else existing).append(name)

	# Nursery — Mid Term + Examination
	for ag, d in (
		("Nursery - Mid Term", DATE_MID_TERM),
		("Nursery - Examination", DATE_EXAM),
	):
		for i, course in enumerate(NURSERY_COURSES):
			fh, th = 8 + i, 9 + i
			name, is_new = _create_plan(
				student_group=NURSERY_GROUP,
				assessment_group=ag,
				course=course,
				grading_scale="Barème 100 points",
				max_score=100.0,
				schedule_date=d,
				from_time=f"{fh:02d}:00:00",
				to_time=f"{th:02d}:00:00",
				criterion="Note obtenue",
				examiner=NURSERY_INSTRUCTOR,
				room_name=NURSERY_ROOM,
				assessment_name=f"Nur1 {ag} — {course}",
			)
			(created if is_new else existing).append(name)

	frappe.db.commit()
	return {
		"created_or_submitted": len(created),
		"already_submitted": len(existing),
		"total": frappe.db.count("Assessment Plan", {"docstatus": 1}),
		"criteria": CRITERIA,
		"pilots": [PRIMARY_GROUP, NURSERY_GROUP],
	}
