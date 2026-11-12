"""Link Courses (matières) to Programs — checklist 4.3.

Sources:
  - docs/school-config/checklist_parametrage_education_lycee (1).xlsx → 04_Matieres
  - docs/school-config/SCORE_REPORTS.md (Nursery vs Primary subject lists)

  bench --site <site> execute citigems_custom.scripts.seed_program_courses.seed
"""

from __future__ import annotations

import frappe

# Program name → course titles (must match Course.course_name)
PROGRAM_COURSES: dict[str, list[str]] = {
	"Nursery / Maternelle": [
		# Checklist nursery
		"Mathématiques (Nursery)",
		"Français (Nursery)",
		"Éducation pour la santé",
		# SCORE cognitive
		"Reading of Alphabet",
		"Writing of Alphabet",
		"Recognition of Alphabet",
		"Counting of Numbers",
		"Writing of Numbers",
		"Recognition of Numbers",
		"Music",
		"Creative Fine Art",
		"General Studies / General Knowledge",
		"Nursery Rhymes",
		# SCORE FR maternelle
		"Éducation corporelle / PHE",
		"Pré-Lecture",
		"Pré-Mathématique",
		"Éducation Sensorielle",
		"Travaux Manuels",
		"Expression Émotionnelle",
		"Expression Plastique",
		"Communication Orale",
		"Conte / Poésie / Chant",
		"Activité Loisir",
		# Extras + checklist « toutes classes »
		"Speech development",
		"Activité de vie pratique",
		"Écriture",
	],
	"Primary / Primaire": [
		# Checklist primaire
		"Communication Orale",
		"Mathématiques",
		"Français",
		"Éducation Science et Technologie",
		"Éducation Sociale",
		"Éducation Artistique",
		"Mathematics",
		"English Language",
		"Religious and National Values",
		"Basic Science and Technology",
		"Cultural and Creative Art",
		"Pre Vocational Studies",
		"Verbal Reasoning",
		"Quantitative Reasoning",
		# Checklist « toutes classes »
		"Éducation corporelle / PHE",
		"Écriture",
		# SCORE primary
		"Civil Education",
		"Social Studies",
		"Religious Instruction",
		"Social Security",
		"Computer Science",
		"Music",
		"Agricultural Science",
		"Home Economics",
		# Timetable extras
		"Géographie",
		"Histoire",
		"Lecture / Reading",
	],
}


def _sync_program_courses(program_name: str, course_names: list[str]) -> dict:
	missing = [c for c in course_names if not frappe.db.exists("Course", c)]
	if missing:
		frappe.throw(f"Courses manquants pour {program_name}: {missing}")

	doc = frappe.get_doc("Program", program_name)
	wanted = list(dict.fromkeys(course_names))  # stable unique
	current = [r.course for r in doc.courses]
	if current == wanted and all(r.required for r in doc.courses):
		return {"program": program_name, "linked": len(wanted), "changed": False}

	doc.set("courses", [])
	for name in wanted:
		doc.append("courses", {"course": name, "required": 1})
	doc.save(ignore_permissions=True)
	return {"program": program_name, "linked": len(wanted), "changed": True}


def seed():
	"""Attach matières to Nursery / Primary programs."""
	frappe.flags.ignore_permissions = True
	results = []
	for program_name, courses in PROGRAM_COURSES.items():
		if not frappe.db.exists("Program", program_name):
			frappe.throw(f"Program manquant: {program_name}")
		results.append(_sync_program_courses(program_name, courses))
	frappe.db.commit()
	return {
		"programs": results,
		"program_course_rows": frappe.db.count("Program Course"),
	}
