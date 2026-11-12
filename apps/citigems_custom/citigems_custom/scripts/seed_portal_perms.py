"""Grant Guardian/Student portal read perms + backfill Course Schedule.program."""
import frappe

PORTAL_READ = (
	"Sales Invoice",
	"Student Attendance",
	"Assessment Result",
	"Course Schedule",
	"Program Enrollment",
	"Student",
	"Fee Schedule",
)


def _ensure_perm(doctype: str, role: str) -> None:
	if frappe.db.exists("Custom DocPerm", {"parent": doctype, "role": role, "permlevel": 0}):
		# ensure read
		name = frappe.db.get_value(
			"Custom DocPerm", {"parent": doctype, "role": role, "permlevel": 0}, "name"
		)
		frappe.db.set_value("Custom DocPerm", name, "read", 1, update_modified=False)
		return
	doc = frappe.get_doc(
		{
			"doctype": "Custom DocPerm",
			"parent": doctype,
			"parenttype": "DocType",
			"parentfield": "permissions",
			"role": role,
			"permlevel": 0,
			"read": 1,
			"select": 1,
			"export": 1,
		}
	)
	doc.insert(ignore_permissions=True)


def seed() -> dict:
	for role in ("Guardian", "Student"):
		for dt in PORTAL_READ:
			_ensure_perm(dt, role)
	frappe.clear_cache()
	# backfill schedule.program
	groups = frappe.get_all("Student Group", fields=["name", "program"])
	updated = 0
	for g in groups:
		if not g.program:
			continue
		n = frappe.db.sql(
			"""
			UPDATE `tabCourse Schedule`
			SET program=%s
			WHERE student_group=%s AND IFNULL(program, '')=''
			""",
			(g.program, g.name),
		)
		updated += frappe.db.sql(
			"SELECT COUNT(*) FROM `tabCourse Schedule` WHERE student_group=%s AND program=%s",
			(g.name, g.program),
		)[0][0]
	frappe.db.commit()
	frappe.only_for = None
	from frappe.permissions import clear_user_permissions  # noqa: F401
	return {
		"perms": PORTAL_READ,
		"schedule_with_program": frappe.db.count("Course Schedule", {"program": ["is", "set"]}),
	}
