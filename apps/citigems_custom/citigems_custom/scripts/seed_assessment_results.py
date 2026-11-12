"""Seed Assessment Results for submitted Assessment Plans — guide 8.3 suite.

Demo scores for B5 + Nur 1 pupils, then submit.

  bench --site <site> execute citigems_custom.scripts.seed_assessment_results.seed
"""

from __future__ import annotations

import frappe
from frappe.utils import flt

# Stable demo scores by student suffix + plan hash (readable, reproducible)
_BASE_SCORES_100 = {
	"EDU-STU-2026-00013": 78,  # Gloria
	"EDU-STU-2026-00014": 65,  # Isaac
	"EDU-STU-2026-00001": 82,  # Aïcha
	"EDU-STU-2026-00002": 71,  # Koffi
}
_BASE_SCORES_5 = {
	"EDU-STU-2026-00013": 4,
	"EDU-STU-2026-00014": 3,
}


def _score_for(student: str, max_score: float, assessment_group: str) -> float:
	if max_score <= 5:
		base = _BASE_SCORES_5.get(student, 3)
		# slight variation by group
		adj = 1 if "Psychomotor" in (assessment_group or "") else 0
		return float(min(max_score, max(1, base + adj - 1)))
	base = _BASE_SCORES_100.get(student, 70)
	bump = {"CA - Class Test": 0, "CA - Mid Term": 3, "CA - Examination": -2}.get(
		assessment_group or "", 0
	)
	return float(min(max_score, max(0, base + bump)))


def _ensure_result(plan_name: str, student: str) -> tuple[str, bool]:
	existing = frappe.db.exists(
		"Assessment Result",
		{"assessment_plan": plan_name, "student": student, "docstatus": ("<", 2)},
	)
	if existing:
		doc = frappe.get_doc("Assessment Result", existing)
		if doc.docstatus == 0:
			doc.submit()
			return doc.name, True
		return doc.name, False

	plan = frappe.get_doc("Assessment Plan", plan_name)
	details = []
	for row in plan.assessment_criteria:
		score = _score_for(student, flt(row.maximum_score), plan.assessment_group)
		details.append(
			{
				"assessment_criteria": row.assessment_criteria,
				"maximum_score": row.maximum_score,
				"score": score,
			}
		)

	doc = frappe.get_doc(
		{
			"doctype": "Assessment Result",
			"assessment_plan": plan.name,
			"student": student,
			"student_name": frappe.db.get_value("Student", student, "student_name"),
			"student_group": plan.student_group,
			"program": plan.program,
			"course": plan.course,
			"academic_year": plan.academic_year,
			"academic_term": plan.academic_term,
			"assessment_group": plan.assessment_group,
			"grading_scale": plan.grading_scale,
			"maximum_score": plan.maximum_assessment_score,
			"details": details,
			"comment": "Saisie démo Citigems (seed)",
		}
	)
	doc.insert(ignore_permissions=True)
	doc.submit()
	return doc.name, True


def seed():
	"""Enter & submit Assessment Results for all pilot plans."""
	frappe.flags.ignore_permissions = True
	plans = frappe.get_all(
		"Assessment Plan",
		filters={"docstatus": 1},
		fields=["name", "student_group"],
	)
	created, existing = [], []
	for plan in plans:
		students = frappe.get_all(
			"Student Group Student",
			filters={"parent": plan.student_group, "active": 1},
			pluck="student",
		)
		if not students:
			students = frappe.get_all(
				"Student Group Student",
				filters={"parent": plan.student_group},
				pluck="student",
			)
		for student in students:
			name, is_new = _ensure_result(plan.name, student)
			(created if is_new else existing).append(name)

	frappe.db.commit()
	return {
		"created_or_submitted": len(created),
		"already_submitted": len(existing),
		"total": frappe.db.count("Assessment Result", {"docstatus": 1}),
	}
