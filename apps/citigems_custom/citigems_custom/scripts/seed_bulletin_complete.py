"""Fill missing CA / Nursery / Skills scores so the bulletin matches the school booklet.

Primary (B5): full Continuous Assessment subject grid + psychomotor/affective traits.
Nursery (Nur 1): mid-term + exam on literacy/numeracy activities + psychology/affective.

  bench --site <site> execute citigems_custom.scripts.seed_bulletin_complete.seed
"""

from __future__ import annotations

from datetime import date, timedelta

import frappe
from frappe.utils import flt

ACADEMIC_YEAR = "2026-2027"
ACADEMIC_TERM = "2026-2027 (T1)"
PRIMARY_GROUP = "B5 - 2026"
NURSERY_GROUP = "Nur 1 - 2026"
PRIMARY_INSTRUCTOR = "Emile"
NURSERY_INSTRUCTOR = "Tessy"
PRIMARY_ROOM = "Basic 5 / CM1"
NURSERY_ROOM = "Nursery 1"

# Continuous Assessment Report Booklet — subject order (EN side)
PRIMARY_CA_SUBJECTS = [
	"English Language",
	"Mathematics",
	"Civil Education",
	"Social Studies",
	"Religious Instruction",
	"Social Security",
	"Quantitative Reasoning",
	"Verbal Reasoning",
	"Éducation corporelle / PHE",
	"Basic Science and Technology",
	"Computer Science",
	"Cultural and Creative Art",
	"Music",
	"Agricultural Science",
	"Home Economics",
]

NURSERY_CA_SUBJECTS = [
	"Reading of Alphabet",
	"Writing of Alphabet",
	"Recognition of Alphabet",
	"Counting of Numbers",
	"Writing of Numbers",
	"Recognition of Numbers",
	"Music",
	"Creative Fine Art",
	"General Studies",
	"Nursery Rhymes",
]

PSYCHOMOTOR = [
	"Hand Writing",
	"Verbal Fluency",
	"Games",
	"Sport",
	"Handling Tools",
	"Drawing & Painting",
	"Musical Skills",
]
AFFECTIVE = [
	"Punctuality",
	"Neatness",
	"Politeness",
	"Honesty",
	"Co-operation with others",
	"Leadership",
	"Helping others",
	"Emotional Stability",
	"Health",
	"Attitude to school work",
	"Attentiveness",
	"Perseverance",
	"Speaking / Handwriting",
	"Obedience",
]
NURSERY_SKILLS = [
	"Able to Relate with Others",
	"Fluency",
	"Work Independently",
	"Sport",
	"Identifying / Sorting by Colours",
	"Handling of Tools / Toys",
	"Communication with others",
	"Able to Sort Shapes",
	"Musical Skills",
	"Punctuality",
	"Health",
	"Neatness",
	"Honesty",
	"Listen & Follow Instruction",
	"Body Exercise / Self Control",
	"Spirit of Cooperation",
	"Sense of Responsibility",
	"Attentiveness / Attention Span",
	"Doing things without assistance",
	"Initiative",
	"Organisation Ability",
	"Perseverance",
]

_BASE_100 = {
	"EDU-STU-2026-00013": 78,
	"EDU-STU-2026-00014": 65,
	"EDU-STU-2026-00001": 82,
	"EDU-STU-2026-00002": 71,
}
_BASE_5 = {
	"EDU-STU-2026-00013": 4,
	"EDU-STU-2026-00014": 3,
	"EDU-STU-2026-00001": 4,
	"EDU-STU-2026-00002": 3,
}


def _score100(student: str, group: str, course: str) -> float:
	base = _BASE_100.get(student, 70)
	bump = {"CA - Class Test": 0, "CA - Mid Term": 3, "CA - Examination": -2,
		"Nursery - Mid Term": 2, "Nursery - Examination": -1}.get(group, 0)
	# slight course jitter from name
	jitter = (sum(ord(c) for c in course) % 7) - 3
	return float(min(100, max(40, base + bump + jitter)))


def _score5(student: str, trait: str) -> float:
	base = _BASE_5.get(student, 3)
	jitter = (sum(ord(c) for c in trait) % 3) - 1
	return float(min(5, max(1, base + jitter)))


def _ensure_course(name: str) -> str:
	if frappe.db.exists("Course", name):
		return name
	frappe.get_doc({"doctype": "Course", "course_name": name}).insert(ignore_permissions=True)
	return name


def _ensure_criteria(names: list[str]) -> None:
	for n in names:
		if not frappe.db.exists("Assessment Criteria", n):
			frappe.get_doc({"doctype": "Assessment Criteria", "assessment_criteria": n}).insert(
				ignore_permissions=True
			)


def _room(room_name: str) -> str:
	name = frappe.db.get_value("Room", {"room_name": room_name}, "name")
	if not name:
		frappe.throw(f"Room manquante: {room_name}")
	return name


def _hour_of(from_time) -> int:
	if from_time is None:
		return -1
	if hasattr(from_time, "total_seconds"):
		return int(from_time.total_seconds() // 3600)
	if hasattr(from_time, "hour"):
		return int(from_time.hour)
	return int(str(from_time).split(":")[0])


def _free_slot(student_group: str, prefer: date) -> tuple[date, int]:
	"""Pick schedule_date + hour with no Assessment Plan overlap for the group."""
	occupied = {
		(r.schedule_date, _hour_of(r.from_time))
		for r in frappe.get_all(
			"Assessment Plan",
			filters={"student_group": student_group, "docstatus": ("<", 2)},
			fields=["schedule_date", "from_time"],
		)
	}
	for week in range(0, 60):
		d = prefer + timedelta(days=7 * week)
		for hour in range(8, 18):
			if (d, hour) not in occupied:
				return d, hour
	frappe.throw(f"No free Assessment Plan slot for {student_group}")


def _plan(
	*,
	student_group: str,
	assessment_group: str,
	course: str,
	grading_scale: str,
	max_score: float,
	schedule_date: date,
	hour: int,
	examiner: str,
	room_name: str,
	criteria: list[tuple[str, float]],
) -> str:
	existing = frappe.db.exists(
		"Assessment Plan",
		{
			"student_group": student_group,
			"course": course,
			"assessment_group": assessment_group,
			"docstatus": ("<", 2),
		},
	)
	if existing:
		doc = frappe.get_doc("Assessment Plan", existing)
		# refresh criteria if skills plan is thin — cancel linked results then plan
		if len(criteria) > 1 and len(doc.assessment_criteria) < len(criteria):
			for res in frappe.get_all(
				"Assessment Result",
				{"assessment_plan": doc.name, "docstatus": 1},
				pluck="name",
			):
				r = frappe.get_doc("Assessment Result", res)
				r.cancel()
				frappe.delete_doc("Assessment Result", res, force=True, ignore_permissions=True)
			if doc.docstatus == 1:
				doc.cancel()
			frappe.delete_doc("Assessment Plan", doc.name, force=True, ignore_permissions=True)
			existing = None
		else:
			if not doc.academic_term:
				frappe.db.set_value(
					"Assessment Plan", doc.name, "academic_term", ACADEMIC_TERM, update_modified=False
				)
			if doc.docstatus == 0:
				doc.submit()
			return doc.name

	d, hour = _free_slot(student_group, schedule_date)
	doc = frappe.get_doc(
		{
			"doctype": "Assessment Plan",
			"student_group": student_group,
			"assessment_name": f"{student_group} {assessment_group} — {course}",
			"assessment_group": assessment_group,
			"grading_scale": grading_scale,
			"course": course,
			"academic_year": ACADEMIC_YEAR,
			"academic_term": ACADEMIC_TERM,
			"schedule_date": d,
			"from_time": f"{hour:02d}:00:00",
			"to_time": f"{(hour+1):02d}:00:00",
			"maximum_assessment_score": sum(mx for _, mx in criteria),
			"examiner": examiner,
			"room": _room(room_name),
			"assessment_criteria": [
				{"assessment_criteria": cname, "maximum_score": mx} for cname, mx in criteria
			],
		}
	)
	doc.insert(ignore_permissions=True)
	doc.submit()
	# fetch_from / validate can clear term — force it
	frappe.db.set_value(
		"Assessment Plan", doc.name, "academic_term", ACADEMIC_TERM, update_modified=False
	)
	return doc.name


def _upsert_result(plan_name: str, student: str, detail_scores: list[tuple[str, float, float]]) -> str:
	"""detail_scores: (criteria, score, max)."""
	existing = frappe.db.exists(
		"Assessment Result",
		{"assessment_plan": plan_name, "student": student, "docstatus": ("<", 2)},
	)
	plan = frappe.get_doc("Assessment Plan", plan_name)
	payload_details = [
		{"assessment_criteria": c, "score": s, "maximum_score": m} for c, s, m in detail_scores
	]
	if existing:
		doc = frappe.get_doc("Assessment Result", existing)
		need = len(detail_scores) > 1 and len(doc.details) < len(detail_scores)
		if doc.docstatus == 1 and need:
			doc.cancel()
			frappe.delete_doc("Assessment Result", doc.name, force=True, ignore_permissions=True)
			existing = None
		elif doc.docstatus == 1:
			return doc.name
		elif doc.docstatus == 0:
			doc.details = []
			for row in payload_details:
				doc.append("details", row)
			doc.academic_term = ACADEMIC_TERM
			doc.save(ignore_permissions=True)
			doc.submit()
			return doc.name

	doc = frappe.get_doc(
		{
			"doctype": "Assessment Result",
			"assessment_plan": plan.name,
			"student": student,
			"student_name": frappe.db.get_value("Student", student, "student_name"),
			"student_group": plan.student_group,
			"program": plan.program,
			"course": plan.course,
			"academic_year": plan.academic_year or ACADEMIC_YEAR,
			"academic_term": ACADEMIC_TERM,
			"assessment_group": plan.assessment_group,
			"grading_scale": plan.grading_scale,
			"maximum_score": plan.maximum_assessment_score,
			"details": payload_details,
			"comment": "Saisie booklet Citigems (seed)",
		}
	)
	doc.insert(ignore_permissions=True)
	doc.submit()
	frappe.db.set_value(
		"Assessment Result",
		doc.name,
		{"academic_term": ACADEMIC_TERM, "academic_year": ACADEMIC_YEAR},
		update_modified=False,
	)
	return doc.name


def _students(group: str) -> list[str]:
	return frappe.get_all(
		"Student Group Student", filters={"parent": group, "active": 1}, pluck="student"
	) or frappe.get_all("Student Group Student", filters={"parent": group}, pluck="student")


def seed():
	frappe.flags.ignore_permissions = True
	_ensure_course("General Studies")
	_ensure_criteria(["Note obtenue", "Composition"] + PSYCHOMOTOR + AFFECTIVE + NURSERY_SKILLS)

	created = []
	# Unique schedule slots — Assessment Plan rejects overlaps per student_group
	slot_i = {"n": 0}

	def _slot(base: date) -> tuple[date, int]:
		i = slot_i["n"]
		slot_i["n"] += 1
		# spread across Saturdays + hours 8–16
		return base + timedelta(days=7 * (i // 8)), 8 + (i % 8)

	# --- Primary CA subjects ---
	ca_bases = {
		"CA - Class Test": date(2026, 10, 17),
		"CA - Mid Term": date(2026, 11, 14),
		"CA - Examination": date(2026, 12, 12),
	}
	for course in PRIMARY_CA_SUBJECTS:
		_ensure_course(course)
		for ag, base in ca_bases.items():
			crit = "Composition" if ag == "CA - Examination" else "Note obtenue"
			d, hour = _slot(base)
			plan = _plan(
				student_group=PRIMARY_GROUP,
				assessment_group=ag,
				course=course,
				grading_scale="Barème 100 points",
				max_score=100,
				schedule_date=d,
				hour=hour,
				examiner=PRIMARY_INSTRUCTOR,
				room_name=PRIMARY_ROOM,
				criteria=[(crit, 100.0)],
			)
			for stu in _students(PRIMARY_GROUP):
				sc = _score100(stu, ag, course)
				created.append(_upsert_result(plan, stu, [(crit, sc, 100.0)]))

	# --- Primary Skills ---
	skills_base = date(2027, 1, 9)
	for ag, traits, course in (
		("Skills - Psychomotor", PSYCHOMOTOR, "Éducation corporelle / PHE"),
		("Skills - Affective", AFFECTIVE, "Religious and National Values"),
	):
		d, hour = _slot(skills_base)
		plan = _plan(
			student_group=PRIMARY_GROUP,
			assessment_group=ag,
			course=course,
			grading_scale="Skills 1-5",
			max_score=5,
			schedule_date=d,
			hour=hour,
			examiner=PRIMARY_INSTRUCTOR,
			room_name=PRIMARY_ROOM,
			criteria=[(t, 5.0) for t in traits],
		)
		for stu in _students(PRIMARY_GROUP):
			details = [(t, _score5(stu, t), 5.0) for t in traits]
			created.append(_upsert_result(plan, stu, details))

	# --- Nursery cognitive ---
	slot_i["n"] = 0  # separate calendar space per group is enough; reset hours
	nur_bases = {
		"Nursery - Mid Term": date(2026, 11, 14),
		"Nursery - Examination": date(2026, 12, 12),
	}
	for course in NURSERY_CA_SUBJECTS:
		_ensure_course(course)
		for ag, base in nur_bases.items():
			d, hour = _slot(base)
			plan = _plan(
				student_group=NURSERY_GROUP,
				assessment_group=ag,
				course=course,
				grading_scale="Barème 100 points",
				max_score=100,
				schedule_date=d,
				hour=hour,
				examiner=NURSERY_INSTRUCTOR,
				room_name=NURSERY_ROOM,
				criteria=[("Note obtenue", 100.0)],
			)
			for stu in _students(NURSERY_GROUP):
				sc = _score100(stu, ag, course)
				created.append(_upsert_result(plan, stu, [("Note obtenue", sc, 100.0)]))

	d, hour = _slot(date(2027, 1, 16))
	plan = _plan(
		student_group=NURSERY_GROUP,
		assessment_group="Skills - Affective",
		course="Nursery Rhymes",
		grading_scale="Skills 1-5",
		max_score=5,
		schedule_date=d,
		hour=hour,
		examiner=NURSERY_INSTRUCTOR,
		room_name=NURSERY_ROOM,
		criteria=[(t, 5.0) for t in NURSERY_SKILLS],
	)
	for stu in _students(NURSERY_GROUP):
		details = [(t, min(4.0, _score5(stu, t)), 4.0) for t in NURSERY_SKILLS]
		created.append(_upsert_result(plan, stu, details))

	# Force term on everything for 2026-2027 pilots
	frappe.db.sql(
		"""
		update `tabAssessment Plan`
		set academic_term=%s
		where academic_year=%s and docstatus=1
		  and (academic_term is null or academic_term='')
		""",
		(ACADEMIC_TERM, ACADEMIC_YEAR),
	)
	frappe.db.sql(
		"""
		update `tabAssessment Result`
		set academic_term=%s
		where academic_year=%s and docstatus=1
		  and (academic_term is null or academic_term='')
		""",
		(ACADEMIC_TERM, ACADEMIC_YEAR),
	)
	frappe.db.commit()
	return {
		"results_touched": len(created),
		"primary_subjects": len(PRIMARY_CA_SUBJECTS),
		"nursery_subjects": len(NURSERY_CA_SUBJECTS),
		"gloria_results": frappe.db.count(
			"Assessment Result", {"student": "EDU-STU-2026-00013", "docstatus": 1}
		),
		"aicha_results": frappe.db.count(
			"Assessment Result", {"student": "EDU-STU-2026-00001", "docstatus": 1}
		),
	}
