"""Seed Education Courses (matières) from school-config sources.

Sources:
  - docs/school-config/checklist_parametrage_education_lycee (1).xlsx → 04_Matieres
  - docs/school-config/SCORE_REPORTS.md
  - docs/school-config/class timetable 2026.docx (abbreviations mapped)

  bench --site <site> execute citigems_custom.scripts.seed_courses.seed
"""

from __future__ import annotations

import frappe

# (course_name unique, description) — intitulé seul, sans code
COURSES: list[tuple[str, str]] = [
	# --- Checklist 04_Matieres ---
	(
		"Mathématiques (Nursery)",
		"Initiation aux nombres, quantités et formes pour la maternelle. "
		"Jeux de comptage, classement et premiers calculs concrets.",
	),
	(
		"Français (Nursery)",
		"Éveil au français oral et écrit en maternelle : sons, vocabulaire, "
		"écoute d’histoires et premiers contacts avec les lettres.",
	),
	(
		"Éducation pour la santé",
		"Hygiène corporelle, alimentation, sécurité et bonnes habitudes de vie "
		"au quotidien pour les tout-petits.",
	),
	(
		"Éducation corporelle / PHE",
		"Activités physiques, motricité, jeux collectifs et sport. "
		"Développe coordination, endurance et esprit d’équipe (EN/FR).",
	),
	(
		"Écriture",
		"Graphisme et calligraphie : tenue du crayon, tracés, lettres et chiffres. "
		"Progression du trait libre à l’écriture lisible.",
	),
	(
		"Communication Orale",
		"Prise de parole, écoute active, expression claire en classe. "
		"Dialogues, récits et présentation orale (bilingue).",
	),
	(
		"Mathématiques",
		"Programme de mathématiques du primaire (voie francophone) : "
		"nombres, opérations, géométrie, mesures et résolution de problèmes.",
	),
	(
		"Français",
		"Langue française au primaire : oral, lecture, expression écrite, "
		"orthographe et grammaire selon le niveau de la classe.",
	),
	(
		"Éducation Science et Technologie",
		"Découverte du monde scientifique et technique : vivant, matière, "
		"énergie, objets techniques et méthode d’observation.",
	),
	(
		"Éducation Sociale",
		"Vie en société, règles de vie, respect d’autrui et citoyenneté. "
		"Éducation aux valeurs et au vivre-ensemble.",
	),
	(
		"Éducation Artistique",
		"Arts plastiques, chant, poésie, dessin et activités créatives "
		"(dont couture / travaux manuels selon le niveau).",
	),
	(
		"Mathematics",
		"Primary Mathematics (English stream): numbers, operations, geometry, "
		"measurement and problem-solving for each Basic class.",
	),
	(
		"English Language",
		"English language for primary: speaking, listening, reading and writing. "
		"Vocabulary, grammar and comprehension.",
	),
	(
		"Religious and National Values",
		"Religious and National Values (NRVS): faith education, civic values "
		"and social responsibility in a bilingual school context.",
	),
	(
		"Basic Science and Technology",
		"Elementary science and technology: living things, materials, "
		"simple machines and everyday scientific observation.",
	),
	(
		"Cultural and Creative Art",
		"Cultural and Creative Arts: drawing, crafts, colour, design and "
		"expression of Beninese and world cultures.",
	),
	(
		"Pre Vocational Studies",
		"Pre-vocational studies introducing practical skills: agriculture, "
		"home economics and simple craft for primary pupils.",
	),
	(
		"Verbal Reasoning",
		"Verbal reasoning and logic with words: analogies, sequences, "
		"comprehension puzzles and critical thinking in English.",
	),
	(
		"Quantitative Reasoning",
		"Quantitative reasoning: number patterns, word problems and "
		"logical thinking with quantities (primary).",
	),
	# --- Timetable / SCORE Primary extras ---
	(
		"Géographie",
		"Géographie du Bénin, de l’Afrique et du monde : milieux, cartes, "
		"ressources et cadre de vie des élèves.",
	),
	(
		"Histoire",
		"Histoire locale et générale : repères chronologiques, personnages "
		"et événements pour construire la mémoire collective.",
	),
	(
		"Lecture / Reading",
		"Atelier de lecture bilingue : fluidité, compréhension de textes "
		"et plaisir de lire (français et anglais).",
	),
	(
		"Civil Education",
		"Civic education: rights and duties of the child, respect for rules, "
		"community life and good citizenship.",
	),
	(
		"Computer Science",
		"Introduction to computers: keyboard, mouse, basic software and "
		"safe, responsible use of digital tools.",
	),
	(
		"Music",
		"Music education: songs, rhythm, listening and simple instruments. "
		"Supports memory, language and cultural expression.",
	),
	(
		"Agricultural Science",
		"Introduction to plants, soil, animals and school gardening. "
		"Practical awareness of food and the environment.",
	),
	(
		"Home Economics",
		"Home economics basics: hygiene at home, simple cooking notions, "
		"tidiness and family life skills for primary pupils.",
	),
	(
		"Social Studies",
		"Social Studies: family, community, culture and how people live "
		"and work together in society.",
	),
	(
		"Religious Instruction",
		"Religious instruction respectful of families’ beliefs: moral values, "
		"tolerance and spiritual awareness.",
	),
	(
		"Social Security",
		"Awareness of personal safety, solidarity and basic social protection "
		"concepts appropriate for primary age.",
	),
	# --- Nursery cognitive (EN) ---
	(
		"Reading of Alphabet",
		"Nursery: learning to say and sound out letters of the alphabet "
		"through songs, flashcards and guided reading.",
	),
	(
		"Writing of Alphabet",
		"Nursery: tracing and writing letters with correct strokes, "
		"from large patterns to small letter shapes.",
	),
	(
		"Recognition of Alphabet",
		"Nursery: recognising letters in print and in the environment "
		"(signs, books, name tags).",
	),
	(
		"Counting of Numbers",
		"Nursery: counting aloud, one-to-one correspondence and "
		"understanding quantities in play situations.",
	),
	(
		"Writing of Numbers",
		"Nursery: tracing and writing numerals with correct formation "
		"and direction.",
	),
	(
		"Recognition of Numbers",
		"Nursery: recognising written numbers and matching them to "
		"sets of objects.",
	),
	(
		"Creative Fine Art",
		"Nursery creative arts: colouring, tearing, pasting, modelling "
		"and free artistic expression.",
	),
	(
		"General Studies / General Knowledge",
		"General knowledge for nursery: seasons, animals, body parts, "
		"school and home — curiosity about the world.",
	),
	(
		"Nursery Rhymes",
		"Nursery rhymes and chants to build memory, rhythm, vocabulary "
		"and confidence in speaking.",
	),
	# --- Nursery FR ---
	(
		"Pré-Lecture",
		"Éveil à la lecture en maternelle : discrimination visuelle et "
		"auditive, sens de l’écrit, albums et imagiers.",
	),
	(
		"Pré-Mathématique",
		"Éveil mathématique : tri, comparaison, suites logiques, "
		"formes et premiers nombres en manipulation.",
	),
	(
		"Éducation Sensorielle",
		"Exploration des cinq sens, textures, couleurs et sons. "
		"Affine la perception et le vocabulaire descriptif.",
	),
	(
		"Travaux Manuels",
		"Travaux manuels adaptés à l’âge : découpage, collage, "
		"assemblage et petits objets fabriqués en classe.",
	),
	(
		"Expression Émotionnelle",
		"Reconnaissance et expression des émotions : joie, colère, "
		"tristesse, peur — pour mieux vivre ensemble.",
	),
	(
		"Expression Plastique",
		"Dessin, peinture, coloriage et création plastique libre. "
		"Développe imagination et motricité fine.",
	),
	(
		"Conte / Poésie / Chant",
		"Contes, poésies et chants : écoute, mémorisation, "
		"récitation et plaisir de la langue orale.",
	),
	(
		"Activité Loisir",
		"Temps de loisirs éducatifs : jeux calmes ou actifs, "
		"coins libres et activités au choix de l’enfant.",
	),
	(
		"Speech development",
		"Speech and language development: clear pronunciation, "
		"sentence building and confidence when speaking.",
	),
	(
		"Activité de vie pratique",
		"Vie pratique Montessori-inspired: pouring, tidying, "
		"dressing skills and care of the classroom environment.",
	),
]


def _strip_code_prefix(name: str) -> str | None:
	"""CODE — Intitulé → Intitulé ; None if already title-only."""
	sep = " — "
	if sep not in name:
		return None
	return name.split(sep, 1)[1].strip() or None


def _rename_coded_courses() -> list[str]:
	"""Rename existing Course docs that still use CODE — Title."""
	renamed = []
	for old in frappe.get_all("Course", pluck="name"):
		new = _strip_code_prefix(old)
		if not new or new == old:
			continue
		if frappe.db.exists("Course", new):
			continue
		frappe.rename_doc("Course", old, new, force=True, merge=False)
		renamed.append(f"{old} → {new}")
	return renamed


def _ensure_course(course_name: str, description: str) -> str:
	if frappe.db.exists("Course", course_name):
		doc = frappe.get_doc("Course", course_name)
		if description and doc.description != description:
			doc.description = description
			doc.save(ignore_permissions=True)
		return doc.name
	doc = frappe.get_doc(
		{
			"doctype": "Course",
			"course_name": course_name,
			"description": description,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def seed():
	"""Create all Courses from school-config subject lists."""
	frappe.flags.ignore_permissions = True
	renamed = _rename_coded_courses()
	created, updated = [], []
	for course_name, description in COURSES:
		existed = frappe.db.exists("Course", course_name)
		name = _ensure_course(course_name, description)
		(updated if existed else created).append(name)
	frappe.db.commit()
	return {
		"created": len(created),
		"updated": len(updated),
		"renamed": len(renamed),
		"renames": renamed,
		"total": frappe.db.count("Course"),
		"names": [c[0] for c in COURSES],
	}
