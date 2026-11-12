"""Seed Grading Scales — guide 8.1 / checklist 07_Bareme + SCORE_REPORTS.

  - Barème 100 points (E / VG / G / P / F)
  - Skills 1–5 (Psychomotor / Affective)
  - Symboles FR (Satisfaisant / Moyen / Insuffisant)

  bench --site <site> execute citigems_custom.scripts.seed_grading_scales.seed
"""

from __future__ import annotations

import frappe

# (grading_scale_name, description, [(grade_code, threshold%, description), ...])
# Threshold 0% is mandatory (Education validate).
SCALES: list[tuple[str, str, list[tuple[str, float, str]]]] = [
	(
		"Barème 100 points",
		"Continuous Assessment / notes sur 100 (checklist 07).",
		[
			("E", 80, "Excellent"),
			("VG", 70, "Very Good / Très bien"),
			("G", 60, "Good / Bien"),
			("P", 50, "Pass / Passable"),
			("F", 0, "Fail / Insuffisant"),
		],
	),
	(
		"Barème 20 points",
		"Évaluation sommative francophone (note sur 20).",
		[
			("E", 80, "Excellent (≥16/20)"),
			("TB", 70, "Très bien (≥14/20)"),
			("B", 60, "Bien (≥12/20)"),
			("P", 50, "Passable (≥10/20)"),
			("I", 0, "Insuffisant (<10/20)"),
		],
	),
	(
		"Skills 1-5",
		"Psychomotor & Affective (SCORE): 5 Excellent … 1 Poor.",
		[
			("5", 100, "Excellent"),
			("4", 80, "Very Good"),
			("3", 60, "Good"),
			("2", 40, "Fair"),
			("1", 0, "Poor"),
		],
	),
	(
		"Symboles FR",
		"Bulletin FR: Satisfaisant / Moyen / Insuffisant.",
		[
			("S", 67, "Satisfaisant"),
			("M", 40, "Moyen"),
			("I", 0, "Insuffisant"),
		],
	),
]


def _ensure_scale(name: str, description: str, intervals: list[tuple[str, float, str]]) -> tuple[str, str]:
	"""Return (name, status) status in created|updated|exists."""
	if frappe.db.exists("Grading Scale", name):
		doc = frappe.get_doc("Grading Scale", name)
		if doc.docstatus == 1:
			return name, "exists"
		# amend draft
		doc.set("intervals", [])
		for code, thr, desc in intervals:
			doc.append(
				"intervals",
				{"grade_code": code, "threshold": thr, "grade_description": desc},
			)
		doc.description = description
		doc.save(ignore_permissions=True)
		doc.submit()
		return name, "updated"

	doc = frappe.get_doc(
		{
			"doctype": "Grading Scale",
			"grading_scale_name": name,
			"description": description,
			"intervals": [
				{"grade_code": c, "threshold": t, "grade_description": d} for c, t, d in intervals
			],
		}
	)
	doc.insert(ignore_permissions=True)
	doc.submit()
	return name, "created"


def seed():
	"""Create and submit Citigems grading scales."""
	frappe.flags.ignore_permissions = True
	results = {}
	for name, desc, intervals in SCALES:
		_, status = _ensure_scale(name, desc, intervals)
		results[name] = status
	frappe.db.commit()
	return {
		"scales": results,
		"total_submitted": frappe.db.count("Grading Scale", {"docstatus": 1}),
	}
