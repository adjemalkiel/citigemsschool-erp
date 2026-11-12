# Citigems — student score / notes reports (source templates)

Scanned booklets provided by the school (Oct 2026). Used to configure **Assessment**, **Grading Scale**, **Courses**, and **Student Report Generation** print formats.

| File | Level | Role |
|------|--------|------|
| `continuous_assessment_report_booklet.pdf` | Primary / Primaire (+ FR évaluation) | Continuous Assessment Report Booklet |
| `nursery_maternelle_terminal_report.pdf` | Nursery / Maternelle | Terminal report + FR évaluation sommative |

School branding on cover: **CITIGEMS SCHOOLS** — C/ No 533 Agla Agongbomey (à côté de l’Église Pentecôte); TEL 67 34 98 66 / 94 83 58 73; Facebook / www.citigemsschools.com.

---

## Shared header fields (all reports)

Capture as Student / Assessment Plan / Fee context:

- Name of pupil / Nom  
- Class / Classe  
- Admission No / Numéro matricule  
- Age  
- Session / Année scolaire  
- No. of times school opened / present (attendance)  
- Next term begins  
- Next term bill + Terminal report arrears (fee link)  
- No. of pupils in class + Position in class  
- Class Teacher remarks + Headmistress / Directeur remarks + signatures  
- Parent response (FR forms)

---

## A. Nursery / Maternelle

### Cognitive (marks)

Columns: Marks Obtainable | Mid-term Test | Examination | Total | Remarks  

Subjects / activities:

1. Reading of Alphabet  
2. Writing of Alphabet  
3. Recognition of Alphabet  
4. Counting of Numbers  
5. Writing of Numbers  
6. Recognition of Numbers  
7. Music  
8. Creative Fine Art  
9. General Studies  
10. Nursery Rhymes  

Totals: Total Score, Percentage Score.

### Psychology skills + Affective skills

Remark / rating columns (scale ~1–4 on nursery form). Traits include relate with others, fluency, independence, sport, colours/shapes, tools/toys, communication, musical skills; punctuality, health, neatness, honesty, listen & follow, cooperation, responsibility, attentiveness, initiative, organisation, perseverance, etc.

### French side (Maternelle — Évaluation sommative)

Subjects (note + total): Éducation pour la santé, Éducation corporelle, Pré-Lecture, Pré-Mathématique, Éducation Sensorielle, Travaux Manuels, Expression Émotionnelle, Expression Plastique, Communication Orale, Conte/Poésie/Chant, Activité Loisir.

- Décision conseil: Admis(e) / Refusé(e)  
- Seuil de réussite (n matières / n) + Rang  
- Attitudes: Assiduité, Discipline, Défauts majeurs, Qualités remarquables  
- Symboles: Satisfaisant / Moyen / Insuffisant  
- Fiches **Résultats de fin d’année** (Oui/Non seuil, rang, observations, décision, signatures)

---

## B. Primary / Primaire (Continuous Assessment)

### Cognitive table columns

Marks Obtainable | Class Test | Mid Term Test | Examination | Total Scores | Class After Mark | Position | Remarks  

### Subjects

- English  
- Mathematics  
- Civil Education  
- **NRVS:** Social Studies, Religion Instruction, Social Security  
- Quantitative Reasoning  
- Verbal Reasoning  
- PHE  
- Elementary Science  
- Computer Science  
- Creative Arts & Crafts  
- Music  
- **PVS:** Agric Science, Home Economics  
- Total Score / Percentage  

### Psychomotor (1–5)

Hand Writing, Verbal Fluency, Games, Sport, Handling Tools, Drawing & Painting, Musical Skills  

Scale: 5 Excellent · 4 Very Good · 3 Good · 2 Fair · 1 Poor  

### Affective (1–5)

Punctuality, Neatness, Politeness, Honesty, Co-operation, Leadership, Helping others, Emotional Stability, Health, Attitude to school work, Attentiveness, Perseverance, Speaking/Handwriting, Obedience  

---

## C. French Primary — Évaluation sommative trimestrielle

Per matière: Note obtenue | Note minimale exigée | Note de perfection  

Domaines: Français (orale, lecture, expression écrite, graphisme, orthographe), Maths (écrite/orale), EST, ES, EA (chant/poésie, dessin, couture/conte), Anglais, EPS.

- Moyenne, Rang, moyenne max/min classe  
- Décision: a atteint / n’a pas atteint le seuil de réussite  
- Attitudes + analyse pédagogique  
- Symboles Satisfaisant / Moyen / Insuffisant  
- Bulletins fin d’année (découpes)

---

## ERPNext Education mapping (config implications)

| Report concept | Configure as |
|----------------|--------------|
| Continuous Assessment Booklet | Print Format(s) + Assessment Plan per term |
| Class Test / Mid-term / Exam | Assessment Groups (or criteria) with weights |
| Marks Obtainable | Max score on Assessment Criteria / Course |
| Subject list by level | Course + Program Course (Nursery vs Primary) |
| NRVS / PVS groups | Course groups or parent courses |
| Psychomotor / Affective 1–5 | Separate Assessment Group or custom fields; Grading Scale 1–5 |
| Nursery cognitive activities | Courses or assessment criteria under Nursery program |
| Seuil de réussite | Pass threshold on Grading Scale / custom logic |
| Rang / position | Class rank (Student Group size) |
| Attendance opened/present | Student Attendance → report fields |
| Next term bill / arrears | Fee Schedule + outstanding (portal) |
| Teacher / Head remarks | Assessment Result remarks + print |
| Conseil des maîtres Admis/Refusé | Promotion / custom status field |
| Bilingual EN+FR layout | Two print formats or bilingual Jinja template |

### Suggested Assessment Groups (go-live)

1. `CA - Class Test`  
2. `CA - Mid Term`  
3. `CA - Examination`  
4. `Skills - Psychomotor` (scale 1–5)  
5. `Skills - Affective` (scale 1–5)  
6. Nursery: Mid-term + Examination only (no Class Test column on that form)

### Programs to create first

1. **Nursery / Maternelle** (courses = alphabet/numbers/… + FR pré-lecture list)  
2. **Primary / Primaire** (English, Maths, NRVS, PVS, …)  
3. Later: Collège / Lycée (timetable 2026 + Education checklist)

---

## Next config steps

1. Enter school address/phones from cover into Company + Website.  
2. Create Programs + Courses from subject lists above.  
3. Create Grading Scales: percentage/marks + 1–5 skills + FR symbole map.  
4. Build Assessment Plans per term for one pilot Primary class and one Nursery class.  
5. Design print formats to match booklet layout (Continuous Assessment Report Booklet).  
