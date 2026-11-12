"""Generate sample bulletin PDFs — guide 8.4 (Citigems booklet layout).

  bench --site <site> execute citigems_custom.scripts.seed_report_card.seed
"""

from __future__ import annotations

import json

import frappe

from citigems_custom.education_report import preview_report_card

ACADEMIC_YEAR = "2026-2027"
ACADEMIC_TERM = "2026-2027 (T1)"

PILOTS = [
	(
		"EDU-STU-2026-00013",
		"Primary / Primaire",
		"Basic 5 / CM1",
		"Continuous Assessment",
	),
	(
		"EDU-STU-2026-00001",
		"Nursery / Maternelle",
		"Nursery 1",
		"Nursery",
	),
]


def _ensure_letter_head() -> str | None:
	name = "Citigems School"
	if frappe.db.exists("Letter Head", name):
		return name
	logo = "/assets/citigems_custom/images/citigems-logo.png"
	doc = frappe.get_doc(
		{
			"doctype": "Letter Head",
			"letter_head_name": name,
			"source": "HTML",
			"is_default": 1,
			"content": (
				f'<div style="text-align:center">'
				f'<img src="{logo}" style="max-height:64px"/><br/>'
				f"<b>CITIGEMS BILINGUAL SCHOOL</b><br/>"
				f"<small>Cotonou · www.citigemsschools.com</small>"
				f"</div>"
			),
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def seed():
	"""Build Citigems-format bulletin PDFs for B5 + Nursery pilots."""
	frappe.flags.ignore_permissions = True
	letter = _ensure_letter_head()
	out = []
	for student, program, batch, ag in PILOTS:
		if not frappe.db.exists("Student", student):
			frappe.throw(f"Student manquant: {student}")
		if frappe.db.count("Assessment Result", {"student": student, "docstatus": 1}) < 1:
			frappe.throw(f"Aucun Assessment Result pour {student}")
		payload = {
			"student": student,
			"student_name": frappe.db.get_value("Student", student, "student_name"),
			"program": program,
			"student_batch": batch,
			"assessment_group": ag,
			"academic_year": ACADEMIC_YEAR,
			"academic_term": ACADEMIC_TERM,
			"add_letterhead": 1,
			"letter_head": letter,
			"show_marks": 1,
			"doctype": "Student Report Generation Tool",
		}
		preview_report_card(doc=json.dumps(payload))
		pdf = frappe.response.filecontent
		fname = f"Bulletin_{student}_T1.pdf"
		existing = frappe.db.get_value("File", {"file_name": fname, "is_private": 1}, "name")
		if existing:
			frappe.delete_doc("File", existing, force=True, ignore_permissions=True)
		f = frappe.get_doc(
			{"doctype": "File", "file_name": fname, "is_private": 1, "content": pdf}
		)
		f.insert(ignore_permissions=True)
		out.append(
			{
				"student": student,
				"student_name": payload["student_name"],
				"assessment_group": ag,
				"file": f.name,
				"file_url": f.file_url,
				"pdf_bytes": len(pdf),
			}
		)
	frappe.db.commit()
	return {"letter_head": letter, "bulletins": out}
