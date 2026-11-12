"""Seed Guardians (tuteurs) — guide 7.2 / checklist 10_Parents.

One guardian per demo Student: linked on Student.guardians, Website User
with role Guardian for the parent portal. Emails @citigemsschool.com.

  bench --site <site> execute citigems_custom.scripts.seed_guardians.seed

Temp password: ChangeMe2026!
"""

from __future__ import annotations

import frappe
from frappe.utils.password import update_password

EMAIL_DOMAIN = "citigemsschool.com"
TEMP_PASSWORD = "ChangeMe2026!"

# (guardian first, guardian last, relation, phone_suffix) keyed later by student
# Relation values must match Student Guardian select: Mother / Father / Others


def _slug(s: str) -> str:
	return (
		s.lower()
		.replace("ï", "i")
		.replace("é", "e")
		.replace("è", "e")
		.replace("ê", "e")
		.replace("à", "a")
		.replace("ù", "u")
		.replace("ç", "c")
		.replace(" ", "")
		.replace("'", "")
	)


def _guardian_for_student(last: str, idx: int) -> tuple[str, str, str, str]:
	"""Return guardian_name, relation, email, mobile (8-digit BJ)."""
	if idx % 2:
		g_first, relation = "Akossiwa", "Mother"
	else:
		g_first, relation = "Jean", "Father"
	email = f"parent.{_slug(last)}@{EMAIL_DOMAIN}"
	mobile = f"97{idx:06d}"  # e.g. 97000001
	return f"{g_first} {last}", relation, email, mobile


def _ensure_guardian(name: str, email: str, mobile: str, gender: str) -> str:
	existing = frappe.db.get_value("Guardian", {"email_address": email}, "name")
	if existing:
		doc = frappe.get_doc("Guardian", existing)
		changed = False
		if doc.mobile_number != mobile:
			doc.mobile_number = mobile
			changed = True
		if doc.guardian_name != name:
			doc.guardian_name = name
			changed = True
		if changed:
			doc.save(ignore_permissions=True)
		return doc.name
	doc = frappe.get_doc(
		{
			"doctype": "Guardian",
			"guardian_name": name,
			"email_address": email,
			"mobile_number": mobile,
			"gender": gender,
			"nationality": "Beninese",
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _link_student(student: str, guardian: str, relation: str) -> bool:
	doc = frappe.get_doc("Student", student)
	if any(r.guardian == guardian for r in doc.guardians):
		return False
	doc.append(
		"guardians",
		{
			"guardian": guardian,
			"guardian_name": frappe.db.get_value("Guardian", guardian, "guardian_name"),
			"relation": relation,
		},
	)
	doc.save(ignore_permissions=True)
	return True


def _ensure_portal_user(guardian_name: str, email: str, guardian: str) -> tuple[str, bool]:
	created = False
	if not frappe.db.exists("User", email):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": guardian_name.split()[0],
				"last_name": " ".join(guardian_name.split()[1:]) or guardian_name,
				"send_welcome_email": 0,
				"user_type": "Website User",
			}
		)
		user.append("roles", {"role": "Guardian"})
		user.insert(ignore_permissions=True)
		update_password(email, TEMP_PASSWORD)
		created = True
	else:
		user = frappe.get_doc("User", email)
		if "Guardian" not in {r.role for r in user.roles}:
			user.add_roles("Guardian")
		if user.user_type != "Website User":
			user.user_type = "Website User"
			user.flags.ignore_permissions = True
			user.save()

	if frappe.db.get_value("Guardian", guardian, "user") != email:
		frappe.db.set_value("Guardian", guardian, "user", email, update_modified=False)
	return email, created


def seed():
	"""Create guardians, link to students, portal users."""
	frappe.flags.ignore_permissions = True
	if not frappe.db.exists("Role", "Guardian"):
		frappe.throw("Role Guardian manquant")
	# Education default desk_access on Guardian → Desk for parents; kill it first.
	from citigems_custom.website_home import ensure_portal_roles_no_desk

	ensure_portal_roles_no_desk()

	students = frappe.get_all(
		"Student",
		fields=["name", "first_name", "last_name", "gender"],
		order_by="name",
	)
	if not students:
		frappe.throw("Aucun élève — lancer seed_students d’abord")

	guardians, linked, users_created = [], [], []
	for i, s in enumerate(students, start=1):
		g_name, relation, email, mobile = _guardian_for_student(s.last_name, i)
		gender = "Female" if relation == "Mother" else "Male"
		grd = _ensure_guardian(g_name, email, mobile, gender)
		if _link_student(s.name, grd, relation):
			linked.append(f"{grd} → {s.name}")
		_, created = _ensure_portal_user(g_name, email, grd)
		if created:
			users_created.append(email)
		guardians.append(grd)

	frappe.db.commit()
	return {
		"guardians": len(set(guardians)),
		"linked": len(linked),
		"users_created": users_created,
		"temp_password": TEMP_PASSWORD,
		"total_guardians": frappe.db.count("Guardian"),
	}
