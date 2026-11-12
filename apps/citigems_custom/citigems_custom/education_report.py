"""Report card fixes for Frappe v16 + Education + Citigems bulletin layout.

1. Attendance query: dict-syntax COUNT (v16 rejects ``count(x) as y`` strings).
2. ``preview_report_card``: robust ``doc`` parsing + Citigems booklet HTML.
3. Expand Assessment Group trees to leaf groups (stock helper skips nested groups).
"""

from __future__ import annotations

import json
from datetime import date

_INSTALLED = False

# Display order for CA / Nursery columns on the bulletin grid
_COL_META = [
	("CA - Class Test", "Class Test"),
	("CA - Mid Term", "Mid Term Test"),
	("CA - Examination", "Examination"),
	("Nursery - Mid Term", "Mid-Term Test"),
	("Nursery - Examination", "Examination"),
]
_SKILL_GROUPS = ("Skills - Psychomotor", "Skills - Affective")

# Exact subject order from Continuous Assessment Report Booklet
_PRIMARY_SUBJECTS = [
	("English Language", ""),
	("Mathematics", ""),
	("Civil Education", ""),
	("Social Studies", "NRVS"),
	("Religious Instruction", "NRVS"),
	("Social Security", "NRVS"),
	("Quantitative Reasoning", ""),
	("Verbal Reasoning", ""),
	("Éducation corporelle / PHE", ""),
	("Basic Science and Technology", ""),
	("Computer Science", ""),
	("Cultural and Creative Art", ""),
	("Music", ""),
	("Agricultural Science", "PVS"),
	("Home Economics", "PVS"),
]
_NURSERY_SUBJECTS = [
	("Reading of Alphabet", "Literacy"),
	("Writing of Alphabet", "Literacy"),
	("Recognition of Alphabet", "Literacy"),
	("Counting of Numbers", "Numeracy"),
	("Writing of Numbers", "Numeracy"),
	("Recognition of Numbers", "Numeracy"),
	("Music", ""),
	("Creative Fine Art", ""),
	("General Studies", ""),
	("Nursery Rhymes", ""),
]
_PSYCHOMOTOR_ORDER = [
	"Hand Writing",
	"Verbal Fluency",
	"Games",
	"Sport",
	"Handling Tools",
	"Drawing & Painting",
	"Musical Skills",
]
_AFFECTIVE_ORDER = [
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


def get_attendance_count(student, academic_year, academic_term=None):
	import frappe
	from frappe import _

	attendance = frappe._dict()
	attendance.total = 0
	from_date = to_date = None

	if academic_year:
		from_date, to_date = frappe.db.get_value(
			"Academic Year", academic_year, ["year_start_date", "year_end_date"]
		)
	elif academic_term:
		from_date, to_date = frappe.db.get_value(
			"Academic Term", academic_term, ["term_start_date", "term_end_date"]
		)

	if not (from_date and to_date):
		frappe.throw(_("Please enter the Academic Year and set the Start and End date."))

	data = frappe.get_all(
		"Student Attendance",
		filters={"student": student, "docstatus": 1, "date": ["between", (from_date, to_date)]},
		fields=["status", {"COUNT": "student", "as": "count"}],
		group_by="status",
	)
	for row in data:
		n = row.get("count") or 0
		if row.status == "Present":
			attendance.present = n
		if row.status == "Absent":
			attendance.absent = n
		attendance.total += n
	return attendance


def _parse_doc(doc):
	import frappe
	from frappe import _

	if doc is None or doc == "":
		doc = frappe.form_dict.get("doc")
	# JSON body may nest under "data"
	if (doc is None or doc == "") and isinstance(frappe.form_dict.get("data"), dict):
		doc = frappe.form_dict.data.get("doc") or frappe.form_dict.data
	if isinstance(doc, str):
		doc = doc.strip()
		if not doc:
			doc = None
		else:
			try:
				doc = json.loads(doc)
			except json.JSONDecodeError as e:
				frappe.throw(_("Invalid report payload: {0}").format(str(e)))
	if isinstance(doc, dict) and doc.get("doc") and not doc.get("student"):
		# accidental double-wrap {"doc": {...}}
		inner = doc.get("doc")
		if isinstance(inner, str):
			try:
				inner = json.loads(inner)
			except json.JSONDecodeError:
				inner = None
		if isinstance(inner, dict):
			doc = inner
	if not doc:
		fd = frappe.form_dict
		if fd.get("student") and fd.get("assessment_group") and fd.get("program"):
			doc = {
				k: fd.get(k)
				for k in (
					"student",
					"student_name",
					"program",
					"student_batch",
					"academic_year",
					"academic_term",
					"assessment_group",
					"letter_head",
					"add_letterhead",
					"show_marks",
					"terms",
					"assessment_criteria",
					"parents_meeting",
					"doctype",
				)
				if fd.get(k) is not None
			}
	if not doc:
		frappe.throw(
			_("Missing report data. Fill the form and click Print Report Card again."),
			title=_("Report Card"),
		)
	return frappe._dict(doc)


def _leaf_assessment_groups(root: str) -> list[str]:
	"""All non-group Assessment Groups under ``root`` (recursive)."""
	import frappe
	from frappe.desk.treeview import get_children

	if not root or not frappe.db.exists("Assessment Group", root):
		return []
	if not frappe.db.get_value("Assessment Group", root, "is_group"):
		return [root]

	leaves: list[str] = []

	def walk(name: str):
		for c in get_children("Assessment Group", name) or []:
			val = c.get("value")
			if not val:
				continue
			if c.get("expandable"):
				walk(val)
			else:
				leaves.append(val)

	walk(root)
	return leaves


def _default_assessment_group(doc) -> str:
	"""Infer booklet root group from program when the form field is empty."""
	prog = (doc.program or "").lower()
	batch = (doc.student_batch or "").lower()
	if "nursery" in prog or "maternelle" in prog or "nur" in batch:
		return "Nursery"
	return "Continuous Assessment"


def _fetch_results(doc) -> list:
	"""Assessment Result rows for student, expanding group tree; term optional."""
	import frappe

	if not doc.assessment_group:
		doc.assessment_group = _default_assessment_group(doc)

	groups = _leaf_assessment_groups(doc.assessment_group)
	prog = (doc.program or "").lower()
	# Booklet always includes Skills alongside cognitive columns
	if doc.assessment_group in (
		"Continuous Assessment",
		"Nursery",
		"All Assessment Groups",
	) or "primary" in prog or "primaire" in prog or "nursery" in prog or "maternelle" in prog:
		for g in _SKILL_GROUPS:
			if g not in groups:
				groups.append(g)

	fields = [
		"name",
		"course",
		"assessment_group",
		"total_score",
		"grade",
		"maximum_score",
		"academic_term",
	]

	def _query(extra_filters: dict) -> list:
		return frappe.get_all("Assessment Result", filters=extra_filters, fields=fields)

	base = {"docstatus": 1, "student": doc.student}
	if doc.academic_year:
		base["academic_year"] = doc.academic_year

	rows = []
	if groups:
		rows = _query({**base, "assessment_group": ["in", groups]})
	# Fallback: any submitted results for this student/year (wrong/empty group on form)
	if not rows:
		rows = _query(base)

	if doc.academic_term:
		# Include rows with matching term OR blank term (legacy / fetch_from gaps)
		with_term = [
			r
			for r in rows
			if (not r.academic_term) or r.academic_term == doc.academic_term
		]
		if with_term:
			rows = with_term

	for r in rows:
		r["details"] = frappe.get_all(
			"Assessment Result Detail",
			{"parent": r.name},
			["assessment_criteria", "maximum_score", "grade", "score"],
		)
	return rows


def _course_name(course: str) -> str:
	import frappe

	return frappe.db.get_value("Course", course, "course_name") or course


def _skill_rows_from_results(results: list, group: str, order: list[str]) -> list[dict]:
	"""Prefer Assessment Result Detail criteria (booklet traits) over course name."""
	from frappe.utils import flt

	by_trait: dict[str, dict] = {}
	for r in results:
		if r.assessment_group != group:
			continue
		if r.details and len(r.details) > 1:
			for d in r.details:
				by_trait[d.assessment_criteria] = {
					"course_name": d.assessment_criteria,
					"score": d.score,
					"grade": d.grade or "",
				}
		else:
			by_trait[_course_name(r.course)] = {
				"course_name": _course_name(r.course),
				"score": r.total_score,
				"grade": r.grade or "",
			}
	rows = []
	seen = set()
	for trait in order:
		if trait in by_trait:
			rows.append(by_trait[trait])
			seen.add(trait)
	for k, v in by_trait.items():
		if k not in seen:
			rows.append(v)
	return rows


def _peer_totals(student_group: str, academic_year: str, academic_term: str | None, groups: list[str]) -> dict:
	"""course -> list of total scores across classmates (for avg + position)."""
	import frappe
	from frappe.utils import flt

	if not student_group:
		return {}
	peers = frappe.get_all(
		"Student Group Student", filters={"parent": student_group, "active": 1}, pluck="student"
	)
	if not peers:
		return {}
	filters = {
		"docstatus": 1,
		"student": ["in", peers],
		"academic_year": academic_year,
		"assessment_group": ["in", groups],
	}
	rows = frappe.get_all(
		"Assessment Result", filters=filters, fields=["student", "course", "total_score", "academic_term"]
	)
	if academic_term:
		trows = [r for r in rows if r.academic_term == academic_term]
		if trows:
			rows = trows
	by_student_course: dict[tuple, float] = {}
	for r in rows:
		key = (r.student, r.course)
		by_student_course[key] = by_student_course.get(key, 0.0) + flt(r.total_score)
	course_scores: dict[str, list[float]] = {}
	for (_stu, course), total in by_student_course.items():
		course_scores.setdefault(course, []).append(total)
	return course_scores


def _build_matrix(results: list, doc=None):
	"""Booklet-ordered cognitive grid + psychomotor/affective traits."""
	from frappe.utils import flt

	present_groups = {r.assessment_group for r in results}
	cognitive_columns = [
		{"key": key, "label": label}
		for key, label in _COL_META
		if key in present_groups
	]

	by_course: dict = {}
	for r in results:
		if r.assessment_group in _SKILL_GROUPS:
			continue
		slot = by_course.setdefault(
			r.course,
			{"max_score": 0, "scores": {}, "grades": [], "total": 0.0},
		)
		mx = flt(r.maximum_score)
		if r.details:
			mx = max((flt(d.maximum_score) for d in r.details), default=mx)
		slot["max_score"] = max(slot["max_score"], mx)
		slot["scores"][r.assessment_group] = r.total_score
		if r.grade:
			slot["grades"].append(r.grade)
		slot["total"] += flt(r.total_score)

	prog = ((doc.program if doc else "") or "").lower()
	is_nursery = "nursery" in prog or "maternelle" in prog
	order = _NURSERY_SUBJECTS if is_nursery else _PRIMARY_SUBJECTS

	# Class averages / positions from peers in the same student group
	ca_groups = [c["key"] for c in cognitive_columns]
	peer_map = {}
	if doc and ca_groups:
		sg = frappe_db_student_group(doc.student, doc.academic_year)
		peer_map = _peer_totals(sg, doc.academic_year, doc.academic_term, ca_groups)

	cognitive_rows = []
	tot_max = tot_sum = 0.0
	by_col = {c["key"]: 0.0 for c in cognitive_columns}
	n_cols = max(len(cognitive_columns), 1)
	used = set()

	def _append_row(course: str, banner: str = ""):
		nonlocal tot_max, tot_sum
		slot = by_course.get(course)
		if not slot:
			return
		used.add(course)
		scores_list = peer_map.get(course) or [slot["total"]]
		avg = round(sum(scores_list) / len(scores_list), 1) if scores_list else ""
		# position: 1 = highest total
		ranked = sorted(scores_list, reverse=True)
		try:
			pos = ranked.index(slot["total"]) + 1
		except ValueError:
			pos = ""
		grade = slot["grades"][-1] if slot["grades"] else ""
		label = _course_name(course)
		if banner:
			label = f"{banner}: {label}" if banner in ("NRVS", "PVS", "Literacy", "Numeracy") else label
		cognitive_rows.append(
			{
				"course_name": label,
				"max_score": int(slot["max_score"]) if slot["max_score"] else 100,
				"scores": slot["scores"],
				"total": slot["total"],
				"grade": grade,
				"class_avg": avg,
				"position": pos,
			}
		)
		tot_max += flt(slot["max_score"]) * n_cols
		tot_sum += slot["total"]
		for k, v in slot["scores"].items():
			if k in by_col:
				by_col[k] += flt(v)

	seen_banner = set()
	for course, banner in order:
		if banner and banner not in seen_banner and any(c in by_course for c, b in order if b == banner):
			cognitive_rows.append(
				{
					"course_name": banner,
					"max_score": "",
					"scores": {},
					"total": "",
					"grade": "",
					"class_avg": "",
					"position": "",
					"is_section": True,
				}
			)
			seen_banner.add(banner)
		_append_row(course, "")

	# Extra courses not on the paper booklet: keep FR bilingual extras off the EN CA page
	skip_extra = set() if is_nursery else {"Français", "Mathématiques"}
	for course in by_course:
		if course not in used and course not in skip_extra:
			_append_row(course)

	cognitive_totals = None
	if any(not r.get("is_section") for r in cognitive_rows):
		percent = round(100.0 * tot_sum / tot_max, 1) if tot_max else None
		cognitive_totals = {
			"max": int(tot_max) if tot_max else "",
			"total": tot_sum,
			"percent": percent,
			"by_col": {k: (v if v else "") for k, v in by_col.items()},
		}

	psychomotor_rows = _skill_rows_from_results(results, "Skills - Psychomotor", _PSYCHOMOTOR_ORDER)
	affective_rows = _skill_rows_from_results(
		results, "Skills - Affective", _AFFECTIVE_ORDER if not is_nursery else []
	)
	# Nursery psychology+affective landed in Skills - Affective with many traits
	if is_nursery and not affective_rows:
		affective_rows = _skill_rows_from_results(results, "Skills - Affective", [])

	return cognitive_columns, cognitive_rows, cognitive_totals, psychomotor_rows, affective_rows


def frappe_db_student_group(student: str, academic_year: str | None) -> str:
	import frappe

	row = frappe.db.sql(
		"""
		select sgs.parent
		from `tabStudent Group Student` sgs
		inner join `tabStudent Group` sg on sg.name=sgs.parent
		where sgs.student=%s and ifnull(sgs.active,1)=1
		  and (%s is null or sg.academic_year=%s or ifnull(sg.academic_year,'')='')
		order by sg.modified desc limit 1
		""",
		(student, academic_year, academic_year),
	)
	return row[0][0] if row else ""


def _student_extras(student: str) -> dict:
	import frappe
	from frappe.utils import getdate

	dob = frappe.db.get_value("Student", student, "date_of_birth")
	age = None
	if dob:
		d = getdate(dob)
		today = date.today()
		age = today.year - d.year - ((today.month, today.day) < (d.month, d.day))
	return {"admission_no": student, "age": age}


def _school_chrome() -> dict:
	import frappe

	logo = "/assets/citigems_custom/images/citigems-logo.png"
	company = frappe.db.get_single_value("Global Defaults", "default_company") or "Citigems Bilingual School"
	phone = frappe.db.get_value("Company", company, "phone_no") or ""
	addr = frappe.db.get_value(
		"Address",
		{"link_doctype": "Company", "link_name": company},
		["address_line1", "city", "phone"],
		as_dict=True,
	)
	# fallback company address link table
	if not addr:
		addr = frappe.db.sql(
			"""
			select a.address_line1, a.city, a.phone
			from `tabAddress` a
			inner join `tabDynamic Link` l on l.parent=a.name
			where l.link_doctype='Company' and l.link_name=%s
			limit 1
			""",
			company,
			as_dict=True,
		)
		addr = addr[0] if addr else None

	line = (addr.address_line1 if addr else "") or "C/ No 533 Agla Agongbomey"
	city = (addr.city if addr else "") or "Cotonou"
	addr_phone = (addr.phone if addr else "") or ""
	phones = ", ".join(p for p in [phone, addr_phone] if p) or "67 34 98 66 / 94 83 58 73"
	return {
		"logo_url": logo,
		"school_address": f"{line}, {city}",
		"school_phones": phones,
		"school_web": "www.citigemsschools.com · facebook.com/citigemsschools",
	}


def _booklet_titles(doc) -> tuple[str, str]:
	ag = (doc.assessment_group or "").lower()
	prog = (doc.program or "").lower()
	if "nursery" in ag or "maternelle" in prog or "nursery" in prog:
		return ("REPORT BOOKLET", "NURSERY / MATERNELLE — TERMINAL REPORT")
	return ("REPORT BOOKLET", "CONTINUOUS ASSESSMENT")


def _pupils_in_class(student: str, academic_year: str | None) -> int | str:
	import frappe

	sg = frappe.db.sql(
		"""
		select sgs.parent
		from `tabStudent Group Student` sgs
		inner join `tabStudent Group` sg on sg.name=sgs.parent
		where sgs.student=%s and ifnull(sgs.active,1)=1
		  and (%s is null or sg.academic_year=%s or ifnull(sg.academic_year,'')='')
		order by sg.modified desc
		limit 1
		""",
		(student, academic_year, academic_year),
	)
	if not sg:
		return ""
	return frappe.db.count("Student Group Student", {"parent": sg[0][0], "active": 1}) or ""


def preview_report_card(doc=None):
	"""Citigems booklet PDF (whitelisted at bottom of module)."""
	import frappe
	from frappe.utils.pdf import get_pdf

	install_report_card_patch()
	doc = _parse_doc(doc)
	doc.students = [doc.student]
	if not doc.student_name:
		doc.student_name = frappe.db.get_value("Student", doc.student, "student_name")
	if not doc.assessment_group:
		doc.assessment_group = _default_assessment_group(doc)

	results = _fetch_results(doc)
	(
		cognitive_columns,
		cognitive_rows,
		cognitive_totals,
		psychomotor_rows,
		affective_rows,
	) = _build_matrix(results, doc)
	doc.attendance = get_attendance_count(doc.student, doc.academic_year, doc.academic_term)
	extras = _student_extras(doc.student)
	chrome = _school_chrome()
	title, subtitle = _booklet_titles(doc)

	html = frappe.render_template(
		"citigems_custom/templates/report_card/citigems_bulletin.html",
		{
			"doc": doc,
			"cognitive_columns": cognitive_columns,
			"cognitive_rows": cognitive_rows,
			"cognitive_totals": cognitive_totals,
			"psychomotor_rows": psychomotor_rows,
			"affective_rows": affective_rows,
			"attendance": doc.attendance,
			"booklet_title": title,
			"booklet_subtitle": subtitle,
			"pupils_in_class": _pupils_in_class(doc.student, doc.academic_year),
			"next_term_begins": "",
			**extras,
			**chrome,
		},
	)
	final_template = frappe.render_template(
		"frappe/www/printview.html", {"body": html, "title": "Bulletin Citigems"}
	)
	frappe.response.filename = f"Bulletin_{doc.student}.pdf"
	frappe.response.filecontent = get_pdf(
		final_template,
		options={"orientation": "Landscape", "page-size": "A4"},
	)
	frappe.response.type = "pdf"


def backfill_assessment_terms(term: str = "2026-2027 (T1)") -> dict:
	"""Set academic_term on submitted pilot plans/results that were saved without it."""
	import frappe

	frappe.flags.ignore_permissions = True
	n_plans = frappe.db.sql(
		"""
		update `tabAssessment Plan`
		set academic_term=%s
		where docstatus=1 and academic_year='2026-2027'
		  and (academic_term is null or academic_term='')
		""",
		term,
	)
	n_res = frappe.db.sql(
		"""
		update `tabAssessment Result`
		set academic_term=%s
		where docstatus=1 and academic_year='2026-2027'
		  and (academic_term is null or academic_term='')
		""",
		term,
	)
	frappe.db.commit()
	return {
		"term": term,
		"plans_updated": n_plans,
		"results_updated": n_res,
		"results_with_term": frappe.db.count(
			"Assessment Result", {"docstatus": 1, "academic_term": term}
		),
	}


def install_report_card_patch() -> None:
	global _INSTALLED
	if _INSTALLED:
		return
	try:
		from education.education.doctype.student_report_generation_tool import (
			student_report_generation_tool as mod,
		)
	except Exception:
		return
	mod.get_attendance_count = get_attendance_count
	_INSTALLED = True


# Whitelist after def — avoids importing frappe at module top during hooks bootstrap
import frappe as _frappe

preview_report_card = _frappe.whitelist()(preview_report_card)
