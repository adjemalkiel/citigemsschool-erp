"""Seed Course Schedules from docs/school-config/class timetable 2026.docx — guide 5.2.

Repeats the weekly timetable across the Academic Year (Mon–Fri), skipping Noël break.
One color per Student Group so the calendar distinguishes classes.
Instructor required by Education → class teachers as Instructors (no Employee yet).
Each class uses its own Room (no shared-room overlaps).

  bench --site <site> execute citigems_custom.scripts.seed_course_schedules.seed
"""

from __future__ import annotations

from datetime import date, timedelta

import frappe

YEAR_START = date(2026, 9, 14)
YEAR_END = date(2027, 6, 30)
# Checklist Noël break (approx.)
HOLIDAY_START = date(2026, 12, 21)
HOLIDAY_END = date(2027, 1, 4)

COLOR_HEX = {
	"blue": "#EDF6FD",
	"green": "#E4F5E9",
	"red": "#FFF0F0",
	"orange": "#FFF1E7",
	"yellow": "#FFF7D3",
	"teal": "#E6F7F4",
	"violet": "#F5F2FF",
	"cyan": "#E0F8FF",
	"amber": "#FCF3CF",
	"pink": "#FEEEF8",
	"purple": "#F9F0FF",
}

# Student Group → (room_name, instructor_name, class_schedule_color)
CLASS_META: dict[str, tuple[str, str, str]] = {
	"Nur 1 - 2026": ("Nursery 1", "Tessy", "pink"),
	"Nur 2 - 2026": ("Nursery 2", "Geraldine", "violet"),
	"B1 - 2026": ("Basic 1 / CI", "Joy", "blue"),
	"B2 - 2026": ("Basic 2 / CP", "Ulysse", "teal"),
	"B3 - 2026": ("Basic 3 / CE1", "Blessing", "orange"),
	"B4 - 2026": ("Basic 4 / CE2", "Habib", "cyan"),
	"B5 - 2026": ("Basic 5 / CM1", "Emile", "amber"),
	"B6 - 2026": ("Basic 6 / CM2", "Samuel", "purple"),
}

# Timetable abbreviations → Course.course_name
SUBJECT_MAP: dict[str, str] = {
	"francais": "Français",
	"mathematique": "Mathématiques",
	"mathematiques": "Mathématiques",
	"mathematics": "Mathematics",
	"maths": "Mathematics",
	"english": "English Language",
	"est": "Éducation Science et Technologie",
	"es": "Éducation Sociale",
	"geo": "Géographie",
	"hist": "Histoire",
	"histoire": "Histoire",
	"ea": "Éducation Artistique",
	"ea - couture": "Éducation Artistique",
	"basic science": "Basic Science and Technology",
	"rnv": "Religious and National Values",
	"verbal": "Verbal Reasoning",
	"quantitative": "Quantitative Reasoning",
	"pvs": "Pre Vocational Studies",
	"cca": "Cultural and Creative Art",
	"reading": "Lecture / Reading",
	"lecture": "Lecture / Reading",
	"ecriture": "Écriture",
	"dictee": "Français",
	"eps": "Éducation corporelle / PHE",
	"sport": "Éducation corporelle / PHE",
	# Nursery
	"alphabets & numbers reading & recognition": "Reading of Alphabet",
	"lecture et recogn. des alphabets & numbers": "Reading of Alphabet",
	"pre lecture": "Pré-Lecture",
	"pre mathematique": "Pré-Mathématique",
	"activite de vie pratique": "Activité de vie pratique",
	"education pour la sante": "Éducation pour la santé",
	"education de movement": "Éducation corporelle / PHE",
	"communication orale": "Communication Orale",
	"drawing/colouring/creative art": "Creative Fine Art",
	"writing": "Writing of Alphabet",
	"recognition and writing": "Recognition of Alphabet",
	"movement activities /songs": "Nursery Rhymes",
	"general knowledge": "General Studies / General Knowledge",
	"maths nursery": "Mathématiques (Nursery)",
	"speech development": "Speech development",
}

SKIP_TOKENS = (
	"drill",
	"break",
	"siesta",
	"cleaning",
	"assembly",
	"club",
	"play time",
	"toilet",
	"resting",
	"watch video",
	"homework",
)


# day index 0=Mon … 4=Fri → list of (from_time, to_time, subject_label)
# Primary periods (aligned to Word headers); non-teaching slots omitted.
# Source: class timetable 2026.docx main tables (odd-week Wednesday row).

B5: dict[int, list[tuple[str, str, str]]] = {
	0: [  # Monday
		("08:00:00", "09:00:00", "Francais"),
		("09:00:00", "10:00:00", "Francais"),
		("10:15:00", "11:00:00", "Mathematique"),
		("11:00:00", "12:00:00", "EST"),
		("14:00:00", "14:45:00", "ES"),
		("14:45:00", "15:30:00", "ES"),
		("15:30:00", "16:15:00", "Geo"),
	],
	1: [
		("08:00:00", "09:00:00", "Mathematics"),
		("09:00:00", "10:00:00", "English"),
		("10:15:00", "11:00:00", "English"),
		("11:00:00", "12:00:00", "Basic Science"),
		("14:00:00", "14:45:00", "RNV"),
		("14:45:00", "15:30:00", "RNV"),
		("15:30:00", "16:15:00", "Verbal"),
	],
	2: [
		("07:45:00", "08:00:00", "Dictee"),
		("08:00:00", "09:00:00", "EPS"),
		("09:00:00", "10:00:00", "Francais"),
	],
	3: [
		("07:45:00", "08:00:00", "Dictee"),
		("08:00:00", "09:00:00", "Francais"),
		("09:00:00", "10:00:00", "Francais"),
		("10:15:00", "11:00:00", "Mathematique"),
		("11:00:00", "12:00:00", "Mathematique"),
		("14:00:00", "14:45:00", "EST"),
		("14:45:00", "15:30:00", "HIST"),
		("15:30:00", "16:15:00", "EA"),
	],
	4: [
		("08:00:00", "09:00:00", "English"),
		("09:00:00", "10:00:00", "Mathematics"),
		("10:15:00", "11:00:00", "Mathematics"),
		("11:00:00", "12:00:00", "Basic Science"),
		("14:00:00", "14:45:00", "PVS"),
		("14:45:00", "15:30:00", "CCA"),
		("15:30:00", "16:15:00", "Quantitative"),
	],
}

B3: dict[int, list[tuple[str, str, str]]] = {
	0: [
		("08:00:00", "09:00:00", "Francais"),
		("09:00:00", "10:00:00", "Francais"),
		("10:15:00", "11:00:00", "Mathematique"),
		("11:00:00", "12:00:00", "EST"),
		("14:00:00", "14:45:00", "ES"),
		("14:45:00", "15:30:00", "ES"),
		("15:30:00", "16:15:00", "Geo"),
	],
	1: [
		("08:00:00", "09:00:00", "Mathematics"),
		("09:00:00", "10:00:00", "English"),
		("10:15:00", "11:00:00", "Reading"),
		("11:00:00", "12:00:00", "Basic Science"),
		("14:00:00", "14:45:00", "Reading"),
		("14:45:00", "15:30:00", "RNV"),
		("15:30:00", "16:15:00", "Verbal"),
	],
	2: [
		("07:45:00", "08:00:00", "Dictee"),
		("08:00:00", "09:00:00", "EPS"),
		("09:00:00", "10:00:00", "Francais"),
	],
	3: [
		("07:45:00", "08:00:00", "Dictee"),
		("08:00:00", "09:00:00", "Francais"),
		("09:00:00", "10:00:00", "Francais"),
		("10:15:00", "11:00:00", "Mathematique"),
		("11:00:00", "12:00:00", "Mathematique"),
		("14:00:00", "14:45:00", "EST"),
		("14:45:00", "15:30:00", "HIST"),
		("15:30:00", "16:15:00", "EA"),
	],
	4: [
		("08:00:00", "09:00:00", "English"),
		("09:00:00", "10:00:00", "Mathematics"),
		("10:15:00", "11:00:00", "Mathematics"),
		("11:00:00", "12:00:00", "Basic Science"),
		("14:00:00", "14:45:00", "Reading"),
		("14:45:00", "15:30:00", "CCA"),
		("15:30:00", "16:15:00", "Quantitative"),
	],
}

B1: dict[int, list[tuple[str, str, str]]] = {
	0: [
		("08:00:00", "09:00:00", "Francais"),
		("09:00:00", "10:00:00", "Francais"),
		("10:15:00", "11:00:00", "Mathematique"),
		("11:00:00", "12:00:00", "Mathematique"),
		("14:00:00", "14:45:00", "ES"),
		("14:45:00", "15:30:00", "ES"),
		("15:30:00", "16:15:00", "Lecture"),
	],
	1: [
		("08:00:00", "09:00:00", "Mathematics"),
		("09:00:00", "10:00:00", "Mathematics"),
		("10:15:00", "11:00:00", "Reading"),
		("11:00:00", "12:00:00", "Reading"),
		("14:00:00", "14:45:00", "Basic Science"),
		("14:45:00", "15:30:00", "RNV"),
		("15:30:00", "16:15:00", "Verbal"),
	],
	2: [
		("07:45:00", "08:00:00", "Dictee"),
		("08:00:00", "09:00:00", "EPS"),
		("09:00:00", "10:00:00", "Francais"),
	],
	3: [
		("07:45:00", "08:00:00", "Dictee"),
		("08:00:00", "09:00:00", "Lecture"),
		("09:00:00", "10:00:00", "Francais"),
		("10:15:00", "11:00:00", "Mathematique"),
		("11:00:00", "12:00:00", "EST"),
		("14:00:00", "14:45:00", "EST"),
		("14:45:00", "15:30:00", "EA"),
		("15:30:00", "16:15:00", "Lecture"),
	],
	4: [
		("08:00:00", "09:00:00", "Reading"),
		("09:00:00", "10:00:00", "English"),
		("10:15:00", "11:00:00", "Mathematics"),
		("11:00:00", "12:00:00", "Mathematics"),
		("14:00:00", "14:45:00", "Basic Science"),
		("14:45:00", "15:30:00", "CCA"),
		("15:30:00", "16:15:00", "Quantitative"),
	],
}

B6: dict[int, list[tuple[str, str, str]]] = {
	0: [
		("08:00:00", "09:00:00", "Mathematics"),
		("09:00:00", "10:00:00", "English"),
		("10:15:00", "11:00:00", "English"),
		("11:00:00", "12:00:00", "Basic Science"),
		("14:00:00", "14:45:00", "RNV"),
		("14:45:00", "15:30:00", "RNV"),
		("15:30:00", "16:15:00", "Verbal"),
	],
	1: [
		("07:45:00", "08:00:00", "Dictee"),
		("08:00:00", "09:00:00", "Francais"),
		("09:00:00", "10:00:00", "Francais"),
		("10:15:00", "11:00:00", "Mathematique"),
		("11:00:00", "12:00:00", "EST"),
		("14:00:00", "14:45:00", "ES"),
		("14:45:00", "15:30:00", "ES"),
		("15:30:00", "16:15:00", "EA - couture"),
	],
	2: [
		("08:00:00", "09:00:00", "English"),
		("09:00:00", "10:00:00", "Mathematics"),
	],
	3: [
		("08:00:00", "09:00:00", "English"),
		("09:00:00", "10:00:00", "Mathematics"),
		("10:15:00", "11:00:00", "Mathematics"),
		("11:00:00", "12:00:00", "Basic Science"),
		("14:00:00", "14:45:00", "PVS"),
		("14:45:00", "15:30:00", "CCA"),
		("15:30:00", "16:15:00", "Quantitative"),
	],
	4: [
		("08:00:00", "09:00:00", "Francais"),
		("09:00:00", "10:00:00", "Francais"),
		("10:15:00", "11:00:00", "Mathematique"),
		("11:00:00", "12:00:00", "EST"),
		("14:00:00", "14:45:00", "HIST"),
		("14:45:00", "15:30:00", "Geo"),
		("15:30:00", "16:15:00", "EA"),
	],
}

B4: dict[int, list[tuple[str, str, str]]] = {
	0: [
		("08:00:00", "09:00:00", "Mathematics"),
		("09:00:00", "10:00:00", "Mathematics"),
		("10:15:00", "11:00:00", "English"),
		("11:00:00", "12:00:00", "Basic Science"),
		("14:00:00", "14:45:00", "Reading"),
		("14:45:00", "15:30:00", "RNV"),
		("15:30:00", "16:15:00", "Verbal"),
	],
	1: [
		("07:45:00", "08:00:00", "Dictee"),
		("08:00:00", "09:00:00", "Francais"),
		("09:00:00", "10:00:00", "Francais"),
		("10:15:00", "11:00:00", "Mathematique"),
		("11:00:00", "12:00:00", "EST"),
		("14:00:00", "14:45:00", "ES"),
		("14:45:00", "15:30:00", "ES"),
		("15:30:00", "16:15:00", "EA - couture"),
	],
	2: [
		("08:00:00", "09:00:00", "English"),
		("09:00:00", "10:00:00", "Mathematics"),
	],
	3: [
		("08:00:00", "09:00:00", "Mathematics"),
		("09:00:00", "10:00:00", "English"),
		("10:15:00", "11:00:00", "Reading"),
		("11:00:00", "12:00:00", "Basic Science"),
		("14:00:00", "14:45:00", "PVS"),
		("14:45:00", "15:30:00", "CCA"),
		("15:30:00", "16:15:00", "Quantitative"),
	],
	4: [
		("08:00:00", "09:00:00", "Francais"),
		("09:00:00", "10:00:00", "Mathematique"),
		("10:15:00", "11:00:00", "Mathematique"),
		("11:00:00", "12:00:00", "EST"),
		("14:00:00", "14:45:00", "HIST"),
		("14:45:00", "15:30:00", "Geo"),
		("15:30:00", "16:15:00", "EA"),
	],
}

B2: dict[int, list[tuple[str, str, str]]] = {
	0: [
		("08:00:00", "09:00:00", "Mathematics"),
		("09:00:00", "10:00:00", "English"),
		("10:15:00", "11:00:00", "Reading"),
		("11:00:00", "12:00:00", "Basic Science"),
		("14:00:00", "14:45:00", "Reading"),
		("14:45:00", "15:30:00", "RNV"),
		("15:30:00", "16:15:00", "Verbal"),
	],
	1: [
		("07:45:00", "08:00:00", "Dictee"),
		("08:00:00", "09:00:00", "Francais"),
		("09:00:00", "10:00:00", "Lecture"),
		("10:15:00", "11:00:00", "Mathematique"),
		("11:00:00", "12:00:00", "EST"),
		("14:00:00", "14:45:00", "ES"),
		("14:45:00", "15:30:00", "ES"),
		("15:30:00", "16:15:00", "Ecriture"),
	],
	2: [
		("08:00:00", "09:00:00", "Reading"),
		("09:00:00", "10:00:00", "Mathematics"),
	],
	3: [
		("08:00:00", "09:00:00", "English"),
		("09:00:00", "10:00:00", "Reading"),
		("10:15:00", "11:00:00", "Mathematics"),
		("11:00:00", "12:00:00", "Mathematics"),
		("14:00:00", "14:45:00", "Basic Science"),
		("14:45:00", "15:30:00", "CCA"),
		("15:30:00", "16:15:00", "Quantitative"),
	],
	4: [
		("08:00:00", "09:00:00", "Mathematique"),
		("09:00:00", "10:00:00", "Francais"),
		("10:15:00", "11:00:00", "ES"),
		("11:00:00", "12:00:00", "EST"),
		("14:00:00", "14:45:00", "Lecture"),
		("14:45:00", "15:30:00", "EA"),
		("15:30:00", "16:15:00", "EA"),
	],
}

# Nursery Word table — applied to Nur 1 and Nur 2
NURSERY: dict[int, list[tuple[str, str, str]]] = {
	0: [
		("08:00:00", "08:45:00", "Alphabets & Numbers Reading & Recognition"),
		("08:45:00", "09:45:00", "Pre lecture"),
		("10:30:00", "11:30:00", "Ecriture"),
		("11:30:00", "12:00:00", "Activite de vie pratique"),
		("13:00:00", "13:45:00", "Education pour la sante"),
	],
	1: [
		("08:45:00", "09:45:00", "Pre mathematique"),
		("10:30:00", "11:30:00", "Ecriture"),
		("11:30:00", "12:00:00", "Education de movement"),
		("13:00:00", "13:45:00", "Communication Orale"),
	],
	2: [
		("10:30:00", "11:30:00", "Drawing/Colouring/creative art"),
	],
	3: [
		("08:45:00", "09:45:00", "Writing"),
		("10:30:00", "11:30:00", "Recognition and Writing"),
		("11:30:00", "12:00:00", "Movement activities /songs"),
		("13:00:00", "13:45:00", "GENERAL KNOWLEDGE"),
	],
	4: [
		("08:45:00", "09:45:00", "Writing"),
		("10:30:00", "11:30:00", "maths nursery"),
		("13:00:00", "13:45:00", "Speech development"),
	],
}

GROUP_TIMETABLES: dict[str, dict[int, list[tuple[str, str, str]]]] = {
	"B5 - 2026": B5,
	"B3 - 2026": B3,
	"B1 - 2026": B1,
	"B6 - 2026": B6,
	"B4 - 2026": B4,
	"B2 - 2026": B2,
	"Nur 1 - 2026": NURSERY,
	"Nur 2 - 2026": NURSERY,
}


def _norm(label: str) -> str:
	return " ".join(label.lower().replace("é", "e").replace("è", "e").split())


def _map_course(label: str) -> str | None:
	n = _norm(label)
	if not n or any(tok in n for tok in SKIP_TOKENS):
		return None
	if "eps" in n or n.endswith("/ sport") or "/sport" in n.replace(" ", ""):
		return SUBJECT_MAP["eps"]
	if n in SUBJECT_MAP:
		return SUBJECT_MAP[n]
	# strip trailing notes
	for key, course in SUBJECT_MAP.items():
		if n.startswith(key):
			return course
	return None


def _ensure_instructor(name: str) -> str:
	existing = frappe.db.get_value("Instructor", {"instructor_name": name}, "name")
	if existing:
		return existing
	doc = frappe.get_doc(
		{
			"doctype": "Instructor",
			"instructor_name": name,
			"status": "Active",
			"naming_series": "EDU-INS-.YYYY.-",
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _room_name_to_id(room_name: str) -> str:
	name = frappe.db.get_value("Room", {"room_name": room_name}, "name")
	if not name:
		frappe.throw(f"Room manquante: {room_name}")
	return name


def _is_holiday(d: date) -> bool:
	return HOLIDAY_START <= d <= HOLIDAY_END


def _teaching_days() -> list[date]:
	days = []
	d = YEAR_START
	while d <= YEAR_END:
		if d.weekday() < 5 and not _is_holiday(d):
			days.append(d)
		d += timedelta(days=1)
	return days


def _clear_group_schedules(groups: list[str]) -> int:
	"""Delete all Course Schedules for these classes (idempotent re-seed)."""
	names = frappe.get_all(
		"Course Schedule",
		filters={"student_group": ("in", groups)},
		pluck="name",
	)
	if names:
		frappe.db.delete("Course Schedule", {"name": ("in", names)})
	return len(names)


def _short_class(group: str) -> str:
	# "B5 - 2026" → "B5"; "Nur 1 - 2026" → "Nur 1"
	return group.split(" - ")[0].strip()


def seed():
	"""Create Instructors + year-long Course Schedules (color per class)."""
	frappe.flags.ignore_permissions = True
	missing_groups = [g for g in GROUP_TIMETABLES if not frappe.db.exists("Student Group", g)]
	if missing_groups:
		frappe.throw(f"Student Groups manquants: {missing_groups}")

	# Allow schedules across T1–T3 (term on group would clamp dates to T1 only)
	for group in GROUP_TIMETABLES:
		frappe.db.set_value("Student Group", group, "academic_term", None, update_modified=False)

	meta = {}
	for group, (room_name, teacher, color) in CLASS_META.items():
		meta[group] = (
			_ensure_instructor(teacher),
			frappe.db.get_value("Instructor", {"instructor_name": teacher}, "instructor_name")
			or teacher,
			_room_name_to_id(room_name),
			color,
		)

	# Resolve weekly template → (day_i, from, to, course) once
	templates: dict[str, list[tuple[int, str, str, str]]] = {}
	unmapped: set[str] = set()
	for group, days in GROUP_TIMETABLES.items():
		slots = []
		for day_i, day_slots in days.items():
			for from_time, to_time, label in day_slots:
				course = _map_course(label)
				if not course:
					if label.strip():
						unmapped.add(label)
					continue
				if not frappe.db.exists("Course", course):
					frappe.throw(f"Course manquant: {course} (from {label!r})")
				slots.append((day_i, from_time, to_time, course))
		templates[group] = slots

	deleted = _clear_group_schedules(list(GROUP_TIMETABLES))
	teaching = _teaching_days()
	now = frappe.utils.now()
	user = frappe.session.user or "Administrator"
	rows = []
	seq = 0
	for d in teaching:
		day_i = d.weekday()
		for group, slots in templates.items():
			instructor, instructor_name, room, color = meta[group]
			short = _short_class(group)
			for slot_day, from_time, to_time, course in slots:
				if slot_day != day_i:
					continue
				seq += 1
				row = [
					f"EDU-CSH-2026-{seq:05d}",
					now,
					now,
					user,
					user,
					0,
					0,
					group,
					instructor,
					instructor_name,
					"EDU-CSH-.YYYY.-",
					None,
					course,
					COLOR_HEX[color],
					color,
					d,
					room,
					from_time,
					to_time,
					f"{course} · {short}",
				]
				rows.append(row)

	fields = [
		"name",
		"creation",
		"modified",
		"modified_by",
		"owner",
		"docstatus",
		"idx",
		"student_group",
		"instructor",
		"instructor_name",
		"naming_series",
		"program",
		"course",
		"color",
		"class_schedule_color",
		"schedule_date",
		"room",
		"from_time",
		"to_time",
		"title",
	]
	# Education v16 Course Schedule has no company column on some builds
	if frappe.get_meta("Course Schedule").has_field("company"):
		fields.append("company")
		for row in rows:
			row.append(None)
	# Chunked bulk insert
	chunk = 500
	for i in range(0, len(rows), chunk):
		frappe.db.bulk_insert("Course Schedule", fields=fields, values=rows[i : i + chunk])
	frappe.db.commit()
	return {
		"deleted_old": deleted,
		"created": len(rows),
		"teaching_days": len(teaching),
		"range": f"{YEAR_START} → {YEAR_END}",
		"holiday_skip": f"{HOLIDAY_START} → {HOLIDAY_END}",
		"unmapped_labels": sorted(unmapped),
		"colors": {g: CLASS_META[g][2] for g in CLASS_META},
		"total": frappe.db.count("Course Schedule"),
	}
