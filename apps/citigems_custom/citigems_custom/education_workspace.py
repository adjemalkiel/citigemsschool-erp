"""Fix Education workspace links that point at DocTypes missing on v16.

Upstream Education v16 has no Timetable Generator / Timetable Generation Result /
school-timetable page — leftover shortcuts cause « DocType … not found ».
Use Course Schedule instead (already seeded from the Word timetable).
"""

from __future__ import annotations

import frappe

_BROKEN_LINKS = {
	"Timetable Generator",
	"Timetable Generation Result",
	"school-timetable",
}


def ensure_education_workspace():
	"""Drop broken Timetable shortcuts/links; ensure Course Schedule shortcut."""
	if not frappe.db.exists("Workspace", "Education"):
		return

	doc = frappe.get_doc("Workspace", "Education")
	changed = False

	kept_shortcuts = []
	for row in doc.shortcuts or []:
		if row.link_to in _BROKEN_LINKS:
			changed = True
			continue
		kept_shortcuts.append(row)
	if changed:
		doc.set("shortcuts", [])
		for row in kept_shortcuts:
			doc.append("shortcuts", row.as_dict())

	kept_links = []
	for row in doc.links or []:
		if row.link_to in _BROKEN_LINKS:
			changed = True
			continue
		kept_links.append(row)
	if len(kept_links) != len(doc.links or []):
		doc.set("links", [])
		for row in kept_links:
			doc.append("links", row.as_dict())

	has_cs = any(s.link_to == "Course Schedule" for s in (doc.shortcuts or []))
	if not has_cs and frappe.db.exists("DocType", "Course Schedule"):
		doc.append(
			"shortcuts",
			{
				"type": "DocType",
				"link_to": "Course Schedule",
				"label": "Course Schedule",
			},
		)
		changed = True

	if changed:
		doc.flags.ignore_permissions = True
		doc.flags.ignore_links = True
		doc.save(ignore_permissions=True)
		frappe.db.commit()
