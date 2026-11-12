"""Seed Program Enrollments + Student Group membership — guide 7.3.

Uses demo Students from seed_students + class map from seed_student_groups.

  bench --site <site> execute citigems_custom.scripts.seed_enrollments.seed
"""

from __future__ import annotations

import frappe

from citigems_custom.scripts.seed_students import STUDENTS, _email

ACADEMIC_YEAR = "2026-2027"
ENROLLMENT_DATE = "2026-09-14"
CATEGORY = "Régulier"

# Student Group → (program, batch)
GROUP_META: dict[str, tuple[str, str]] = {
	"Nur 1 - 2026": ("Nursery / Maternelle", "Nursery 1 / Maternelle 1"),
	"Nur 2 - 2026": ("Nursery / Maternelle", "Nursery 2 / Maternelle 2"),
	"B1 - 2026": ("Primary / Primaire", "Basic 1 / CI"),
	"B2 - 2026": ("Primary / Primaire", "Basic 2 / CP"),
	"B3 - 2026": ("Primary / Primaire", "Basic 3 / CE1"),
	"B4 - 2026": ("Primary / Primaire", "Basic 4 / CE2"),
	"B5 - 2026": ("Primary / Primaire", "Basic 5 / CM1"),
	"B6 - 2026": ("Primary / Primaire", "Basic 6 / CM2"),
}


def _student_by_email(email: str) -> str | None:
	return frappe.db.get_value("Student", {"student_email_id": email}, "name")


def _ensure_enrollment(student: str, program: str, batch: str) -> tuple[str, bool]:
	existing = frappe.db.exists(
		"Program Enrollment",
		{
			"student": student,
			"program": program,
			"academic_year": ACADEMIC_YEAR,
			"docstatus": ("<", 2),
		},
	)
	if existing:
		doc = frappe.get_doc("Program Enrollment", existing)
		changed = False
		if doc.student_batch_name != batch:
			if doc.docstatus == 0:
				doc.student_batch_name = batch
				doc.student_category = CATEGORY
				doc.save(ignore_permissions=True)
				changed = True
		if doc.docstatus == 0:
			doc.submit()
			changed = True
		return doc.name, changed

	doc = frappe.get_doc(
		{
			"doctype": "Program Enrollment",
			"student": student,
			"program": program,
			"academic_year": ACADEMIC_YEAR,
			"enrollment_date": ENROLLMENT_DATE,
			"student_batch_name": batch,
			"student_category": CATEGORY,
		}
	)
	# validate() auto-fills required Program Courses
	doc.insert(ignore_permissions=True)
	doc.submit()
	return doc.name, True


def _ensure_in_group(student_group: str, student: str) -> bool:
	doc = frappe.get_doc("Student Group", student_group)
	if any(r.student == student for r in doc.students):
		return False
	roll = max((r.group_roll_number or 0 for r in doc.students), default=0) + 1
	doc.append(
		"students",
		{
			"student": student,
			"student_name": frappe.db.get_value("Student", student, "student_name"),
			"group_roll_number": roll,
			"active": 1,
		},
	)
	doc.save(ignore_permissions=True)
	return True


def seed():
	"""Enroll all demo students and place them in Student Groups."""
	frappe.flags.ignore_permissions = True
	for needed in (ACADEMIC_YEAR, CATEGORY, "Nursery / Maternelle", "Primary / Primaire"):
		dt = (
			"Academic Year"
			if needed == ACADEMIC_YEAR
			else "Student Category"
			if needed == CATEGORY
			else "Program"
		)
		if not frappe.db.exists(dt, needed):
			frappe.throw(f"{dt} manquant: {needed}")

	enrolled, grouped, skipped = [], [], []
	for first, last, _gender, _dob, group in STUDENTS:
		email = _email(first, last)
		student = _student_by_email(email)
		if not student:
			skipped.append(email)
			continue
		if group not in GROUP_META:
			frappe.throw(f"Classe inconnue: {group}")
		program, batch = GROUP_META[group]
		name, _ = _ensure_enrollment(student, program, batch)
		enrolled.append(name)
		if _ensure_in_group(group, student):
			grouped.append(f"{student} → {group}")

	frappe.db.commit()
	return {
		"enrollments": len(enrolled),
		"added_to_groups": len(grouped),
		"skipped_missing_students": skipped,
		"program_enrollment_total": frappe.db.count("Program Enrollment", {"docstatus": 1}),
		"course_enrollment_total": frappe.db.count("Course Enrollment"),
	}
