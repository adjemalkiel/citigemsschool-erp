"""Seed Assessment Groups — guide 8.2 / SCORE_REPORTS + checklist 07.

Tree under « All Assessment Groups »:
  Continuous Assessment → Class Test / Mid Term / Examination
  Skills → Psychomotor / Affective
  Trimestre 1|2|3 (folders for FR planning)
  Nursery → Mid Term / Examination (no Class Test)

  bench --site <site> execute citigems_custom.scripts.seed_assessment_groups.seed
"""

from __future__ import annotations

import frappe

ROOT = "All Assessment Groups"

# (name, parent, is_group)
GROUPS: list[tuple[str, str, int]] = [
	# Term folders (checklist)
	("Trimestre 1", ROOT, 1),
	("Trimestre 2", ROOT, 1),
	("Trimestre 3", ROOT, 1),
	# Continuous Assessment (Primary SCORE)
	("Continuous Assessment", ROOT, 1),
	("CA - Class Test", "Continuous Assessment", 0),
	("CA - Mid Term", "Continuous Assessment", 0),
	("CA - Examination", "Continuous Assessment", 0),
	# Skills 1–5
	("Skills", ROOT, 1),
	("Skills - Psychomotor", "Skills", 0),
	("Skills - Affective", "Skills", 0),
	# Nursery booklet (mid-term + exam only)
	("Nursery", ROOT, 1),
	("Nursery - Mid Term", "Nursery", 0),
	("Nursery - Examination", "Nursery", 0),
]


def _ensure_root() -> None:
	if frappe.db.exists("Assessment Group", ROOT):
		doc = frappe.get_doc("Assessment Group", ROOT)
		if not doc.is_group:
			doc.is_group = 1
			doc.save(ignore_permissions=True)
		return
	# NestedSet root: parent may be empty / itself depending on version
	doc = frappe.get_doc(
		{
			"doctype": "Assessment Group",
			"assessment_group_name": ROOT,
			"is_group": 1,
		}
	)
	doc.insert(ignore_permissions=True)


def _ensure_group(name: str, parent: str, is_group: int) -> str:
	if frappe.db.exists("Assessment Group", name):
		doc = frappe.get_doc("Assessment Group", name)
		changed = False
		if doc.parent_assessment_group != parent:
			doc.parent_assessment_group = parent
			changed = True
		if int(bool(doc.is_group)) != is_group:
			doc.is_group = is_group
			changed = True
		if changed:
			doc.save(ignore_permissions=True)
		return "updated" if changed else "exists"

	doc = frappe.get_doc(
		{
			"doctype": "Assessment Group",
			"assessment_group_name": name,
			"parent_assessment_group": parent,
			"is_group": is_group,
		}
	)
	doc.insert(ignore_permissions=True)
	return "created"


def seed():
	"""Create Assessment Group tree for Citigems evaluations."""
	frappe.flags.ignore_permissions = True
	_ensure_root()
	results = {}
	for name, parent, is_group in GROUPS:
		if not frappe.db.exists("Assessment Group", parent):
			frappe.throw(f"Parent Assessment Group manquant: {parent}")
		results[name] = _ensure_group(name, parent, is_group)
	frappe.db.commit()
	return {
		"groups": results,
		"total": frappe.db.count("Assessment Group"),
	}
