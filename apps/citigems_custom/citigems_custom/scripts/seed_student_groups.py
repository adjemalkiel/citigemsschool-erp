"""Seed Student Batch Names + Student Groups (classes) — checklist 4.4 / 05_Classes.

Maps checklist « programmes » de niveau (Nursery 1, Basic 1…) to Student Batch Name,
and attaches groups to the two Programs already seeded (Nursery / Primary).

  bench --site <site> execute citigems_custom.scripts.seed_student_groups.seed
"""

from __future__ import annotations

import frappe

ACADEMIC_YEAR = "2026-2027"
# Leave academic_term empty so Course Schedules can span the whole school year
# (Education validates schedule_date against the group's term if set).

# batch_name (= Student Batch Name)
BATCHES: list[str] = [
	"Pre-Nursery / Pre-Maternelle",
	"Nursery 1 / Maternelle 1",
	"Nursery 2 / Maternelle 2",
	"Basic 1 / CI",
	"Basic 2 / CP",
	"Basic 3 / CE1",
	"Basic 4 / CE2",
	"Basic 5 / CM1",
	"Basic 6 / CM2",
]

# (student_group_name, batch, program)
# Checklist 05_Classes — Program ERPNext = Nursery/Primary (not per-level Program docs)
CLASSES: list[tuple[str, str, str]] = [
	("Nur 1 - 2026", "Nursery 1 / Maternelle 1", "Nursery / Maternelle"),
	("Nur 2 - 2026", "Nursery 2 / Maternelle 2", "Nursery / Maternelle"),
	("B1 - 2026", "Basic 1 / CI", "Primary / Primaire"),
	("B2 - 2026", "Basic 2 / CP", "Primary / Primaire"),
	("B3 - 2026", "Basic 3 / CE1", "Primary / Primaire"),
	("B4 - 2026", "Basic 4 / CE2", "Primary / Primaire"),
	("B5 - 2026", "Basic 5 / CM1", "Primary / Primaire"),
	("B6 - 2026", "Basic 6 / CM2", "Primary / Primaire"),
]


def _ensure_batch(batch_name: str) -> str:
	if frappe.db.exists("Student Batch Name", batch_name):
		return batch_name
	doc = frappe.get_doc({"doctype": "Student Batch Name", "batch_name": batch_name})
	doc.insert(ignore_permissions=True)
	return doc.name


def _ensure_student_group(name: str, batch: str, program: str) -> tuple[str, bool]:
	if frappe.db.exists("Student Group", name):
		doc = frappe.get_doc("Student Group", name)
		changed = False
		for field, value in (
			("academic_year", ACADEMIC_YEAR),
			("academic_term", None),
			("group_based_on", "Batch"),
			("program", program),
			("batch", batch),
		):
			if doc.get(field) != value:
				doc.set(field, value)
				changed = True
		if changed:
			doc.save(ignore_permissions=True)
		return doc.name, changed

	doc = frappe.get_doc(
		{
			"doctype": "Student Group",
			"student_group_name": name,
			"academic_year": ACADEMIC_YEAR,
			"group_based_on": "Batch",
			"program": program,
			"batch": batch,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name, True


def _ensure_academic_year() -> None:
	if frappe.db.exists("Academic Year", ACADEMIC_YEAR):
		return
	frappe.get_doc(
		{
			"doctype": "Academic Year",
			"academic_year_name": ACADEMIC_YEAR,
			"year_start_date": "2026-09-14",
			"year_end_date": "2027-06-30",
		}
	).insert(ignore_permissions=True)
	# Education autoname: "{academic_year} ({term_name})"
	for term_name, start, end in (
		("T1", "2026-09-14", "2026-12-18"),
		("T2", "2027-01-05", "2027-03-27"),
		("T3", "2027-04-06", "2027-06-30"),
	):
		wanted = f"{ACADEMIC_YEAR} ({term_name})"
		if frappe.db.exists("Academic Term", wanted):
			continue
		frappe.get_doc(
			{
				"doctype": "Academic Term",
				"academic_year": ACADEMIC_YEAR,
				"term_name": term_name,
				"term_start_date": start,
				"term_end_date": end,
			}
		).insert(ignore_permissions=True)


def _ensure_programs() -> None:
	for prog in ("Nursery / Maternelle", "Primary / Primaire"):
		if not frappe.db.exists("Program", prog):
			frappe.get_doc({"doctype": "Program", "program_name": prog}).insert(
				ignore_permissions=True
			)


def seed():
	"""Create batches + Student Groups for 2026-2027."""
	frappe.flags.ignore_permissions = True
	_ensure_academic_year()
	_ensure_programs()

	batches = [_ensure_batch(b) for b in BATCHES]
	created, updated = [], []
	for name, batch, program in CLASSES:
		existed = bool(frappe.db.exists("Student Group", name))
		_ensure_student_group(name, batch, program)
		(updated if existed else created).append(name)

	frappe.db.commit()
	return {
		"batches": len(batches),
		"created": created,
		"updated": updated,
		"total_groups": frappe.db.count("Student Group"),
	}
