"""Seed Students (élèves) — guide 7.1.

Checklist 09_Eleves only has lycée examples; Citigems demo pupils are created
per Student Group with ages matching Nursery / Basic levels.

Enrollment (7.3) and Guardians (7.2) are separate seeds.

  bench --site <site> execute citigems_custom.scripts.seed_students.seed
"""

from __future__ import annotations

import frappe

EMAIL_DOMAIN = "citigemsschool.com"
JOINING_DATE = "2026-09-14"

# (first, last, gender FR, DOB, class student_group) — 2 demo pupils / class
STUDENTS: list[tuple[str, str, str, str, str]] = [
	# Nur 1 (~3–4 ans)
	("Aïcha", "Dossou", "Femme", "2022-04-12", "Nur 1 - 2026"),
	("Koffi", "Agbé", "Homme", "2022-09-03", "Nur 1 - 2026"),
	# Nur 2 (~4–5 ans)
	("Mariam", "Hounkpatin", "Femme", "2021-06-21", "Nur 2 - 2026"),
	("Emmanuel", "Zinsou", "Homme", "2021-11-08", "Nur 2 - 2026"),
	# B1 / CI (~6 ans)
	("Grace", "Adjo", "Femme", "2020-02-14", "B1 - 2026"),
	("Samuel", "Toko", "Homme", "2020-07-30", "B1 - 2026"),
	# B2 / CP
	("Esther", "Gbedo", "Femme", "2019-01-19", "B2 - 2026"),
	("Junior", "Akplogan", "Homme", "2019-05-05", "B2 - 2026"),
	# B3 / CE1
	("Divine", "Houngbo", "Femme", "2018-03-22", "B3 - 2026"),
	("Rodrigue", "Mensah", "Homme", "2018-10-11", "B3 - 2026"),
	# B4 / CE2
	("Priscille", "Sossou", "Femme", "2017-04-02", "B4 - 2026"),
	("David", "Gounou", "Homme", "2017-08-17", "B4 - 2026"),
	# B5 / CM1
	("Gloria", "Adjakpa", "Femme", "2016-02-28", "B5 - 2026"),
	("Isaac", "Fassinou", "Homme", "2016-12-09", "B5 - 2026"),
	# B6 / CM2
	("Ruth", "Amoussou", "Femme", "2015-05-16", "B6 - 2026"),
	("Paul", "Kpanou", "Homme", "2015-09-25", "B6 - 2026"),
]


def _gender(fr: str) -> str:
	return "Female" if fr.strip().lower().startswith("f") else "Male"


def _email(first: str, last: str) -> str:
	def slug(s: str) -> str:
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

	return f"{slug(first)}.{slug(last)}@{EMAIL_DOMAIN}"


def _ensure_category(name: str = "Régulier") -> str:
	if frappe.db.exists("Student Category", name):
		return name
	doc = frappe.get_doc({"doctype": "Student Category", "category": name})
	doc.insert(ignore_permissions=True)
	return doc.name


def seed():
	"""Create demo Students for each Citigems class (7.1 only)."""
	frappe.flags.ignore_permissions = True
	_ensure_category("Régulier")
	_ensure_category("Boursier")

	created, existing = [], []
	by_class: dict[str, list[str]] = {}
	for i, (first, last, gender_fr, dob, group) in enumerate(STUDENTS, start=1):
		if not frappe.db.exists("Student Group", group):
			frappe.throw(f"Student Group manquant: {group}")
		email = _email(first, last)
		name = frappe.db.get_value("Student", {"student_email_id": email}, "name")
		is_new = False
		if not name:
			doc = frappe.get_doc(
				{
					"doctype": "Student",
					"naming_series": "EDU-STU-.YYYY.-",
					"first_name": first,
					"last_name": last,
					"student_email_id": email,
					"gender": _gender(gender_fr),
					"date_of_birth": dob,
					"joining_date": JOINING_DATE,
					"enabled": 1,
					"country": "Benin",
					"city": "Cotonou",
					"address_line_2": f"Classe prévue: {group}",
				}
			)
			doc.insert(ignore_permissions=True)
			name = doc.name
			is_new = True
		(created if is_new else existing).append(name)
		by_class.setdefault(group, []).append(name)

	frappe.db.commit()
	return {
		"created": len(created),
		"existing": len(existing),
		"total": frappe.db.count("Student"),
		"by_class": by_class,
		"names": created + existing,
	}
