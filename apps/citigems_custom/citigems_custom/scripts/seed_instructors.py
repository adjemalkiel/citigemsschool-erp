"""Seed Employees + Instructors + Student Group links — guide 6 / checklist 08_Enseignants.

Creates HR Employee (company CBS), links Instructor, Desk User (role Instructor),
and attaches teachers to their Student Group.

  bench --site <site> execute citigems_custom.scripts.seed_instructors.seed

Temp login password for new users: ChangeMe2026!  (school must rotate).
"""

from __future__ import annotations

import frappe
from frappe.utils.password import update_password

COMPANY = "Citigems Bilingual School"
EMAIL_DOMAIN = "citigemsschool.com"
TEMP_PASSWORD = "ChangeMe2026!"
# ponytail: DOB unknown in checklist — placeholder until HR updates; upgrade: import real DOB
DEFAULT_DOB = "1990-01-01"
DATE_OF_JOINING = "2026-09-01"

# (first_name, last_name|None, gender FR, phone, student_group, primary_for_schedules)
TEACHERS: list[tuple[str, str | None, str, str, str, bool]] = [
	("Tessy", None, "Femme", "0161508248", "Nur 1 - 2026", True),
	("Armelle", None, "Femme", "0167045427", "Nur 1 - 2026", False),
	("Geraldine", None, "Femme", "0141270593", "Nur 2 - 2026", True),
	("Tina", None, "Femme", "0166199500", "Nur 2 - 2026", False),
	("Joy", None, "Femme", "0191828384", "B1 - 2026", True),
	("Ulysse", None, "Homme", "0195487174", "B2 - 2026", True),
	("Blessing", None, "Femme", "0140386400", "B3 - 2026", True),
	("Habib", None, "Homme", "0167474041", "B4 - 2026", True),
	("Emile", None, "Homme", "0197643198", "B5 - 2026", True),
	("Samuel", None, "Homme", "002347014579695", "B6 - 2026", True),
]


def _email(first: str) -> str:
	return f"{first.strip().lower()}@{EMAIL_DOMAIN}"


def _gender(fr: str) -> str:
	return "Female" if fr.strip().lower().startswith("f") else "Male"


def _ensure_employee(first: str, last: str | None, gender_fr: str, phone: str, email: str) -> str:
	existing = frappe.db.get_value("Employee", {"employee_name": first if not last else f"{first} {last}"}, "name")
	if not existing:
		# match by personal_email or cell
		existing = frappe.db.get_value("Employee", {"personal_email": email}, "name")
	if existing:
		doc = frappe.get_doc("Employee", existing)
		changed = False
		if phone and doc.cell_number != phone:
			doc.cell_number = phone
			changed = True
		if email and doc.personal_email != email:
			doc.personal_email = email
			doc.company_email = email
			changed = True
		if changed:
			doc.save(ignore_permissions=True)
		return doc.name

	doc = frappe.get_doc(
		{
			"doctype": "Employee",
			"naming_series": "HR-EMP-",
			"first_name": first,
			"last_name": last or "",
			"gender": _gender(gender_fr),
			"date_of_birth": DEFAULT_DOB,
			"date_of_joining": DATE_OF_JOINING,
			"status": "Active",
			"company": COMPANY,
			"cell_number": phone,
			"personal_email": email,
			"company_email": email,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _ensure_instructor(name: str, employee: str) -> str:
	existing = frappe.db.get_value("Instructor", {"instructor_name": name}, "name")
	if existing:
		doc = frappe.get_doc("Instructor", existing)
		if doc.employee != employee:
			doc.employee = employee
			doc.status = "Active"
			doc.save(ignore_permissions=True)
		return doc.name
	doc = frappe.get_doc(
		{
			"doctype": "Instructor",
			"instructor_name": name,
			"employee": employee,
			"status": "Active",
			"naming_series": "EDU-INS-.YYYY.-",
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _ensure_user(first: str, email: str, employee: str) -> tuple[str, bool]:
	"""Create Desk user with Instructor role; return (email, created?)."""
	created = False
	if not frappe.db.exists("User", email):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": first,
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		)
		user.append("roles", {"role": "Instructor"})
		user.insert(ignore_permissions=True)
		update_password(email, TEMP_PASSWORD)
		created = True
	else:
		user = frappe.get_doc("User", email)
		roles = {r.role for r in user.roles}
		if "Instructor" not in roles:
			user.add_roles("Instructor")

	# Link Employee → User
	if frappe.db.get_value("Employee", employee, "user_id") != email:
		frappe.db.set_value("Employee", employee, "user_id", email, update_modified=False)
	return email, created


def _attach_to_group(student_group: str, instructor: str) -> bool:
	if not frappe.db.exists("Student Group", student_group):
		frappe.throw(f"Student Group manquant: {student_group}")
	doc = frappe.get_doc("Student Group", student_group)
	if any(r.instructor == instructor for r in doc.instructors):
		return False
	doc.append("instructors", {"instructor": instructor})
	doc.save(ignore_permissions=True)
	return True


def seed():
	"""Employees + Instructors + Users + Student Group instructors."""
	frappe.flags.ignore_permissions = True
	if not frappe.db.exists("Company", COMPANY):
		frappe.throw(f"Company manquante: {COMPANY}")
	if not frappe.db.exists("Role", "Instructor"):
		frappe.throw("Role Instructor manquant")

	employees, instructors, users_created, groups_linked = [], [], [], []
	for first, last, gender_fr, phone, group, _primary in TEACHERS:
		email = _email(first)
		emp = _ensure_employee(first, last, gender_fr, phone, email)
		ins = _ensure_instructor(first, emp)
		user, created = _ensure_user(first, email, emp)
		if created:
			users_created.append(user)
		if _attach_to_group(group, ins):
			groups_linked.append(f"{ins} → {group}")
		employees.append(emp)
		instructors.append(ins)

	frappe.db.commit()
	return {
		"employees": len(set(employees)),
		"instructors": len(set(instructors)),
		"users_created": users_created,
		"temp_password": TEMP_PASSWORD,
		"groups_linked": groups_linked,
		"logins": [_email(t[0]) for t in TEACHERS],
	}
