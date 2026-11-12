#!/usr/bin/env python3
"""Generate Citigems Bilingual School — owner configuration questionnaire (Excel)."""

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

OUT = Path(__file__).resolve().parents[1] / "docs" / "Citigems_Bilingual_School_Configuration_Questionnaire.xlsx"

# Columns: Module | # | Information needed | Why / where used | Example | Owner answer | Status | Priority | Notes
HEADERS = [
	"Module",
	"#",
	"Information needed (ask the owner)",
	"Why / where it is used",
	"Example / format",
	"Owner answer",
	"Status",
	"Priority",
	"Notes / attachments",
]

STATUS_OPTS = '"Not started,In progress,Received,Validated,N/A"'
PRIORITY_OPTS = '"Must have (go-live),Should have (month 1-3),Later (phase 2),Optional"'

# (module, question, why, example, priority)
ROWS: list[tuple[str, str, str, str, str]] = [
	# —— 1. Legal / company ——
	(
		"1. Legal & company",
		"Official full legal name of the school",
		"Company master, invoices, MeCeF, website footer",
		"Citigems Bilingual School",
		"Must have (go-live)",
	),
	(
		"1. Legal & company",
		"Trading / brand name (if different)",
		"Website, portal, email headers",
		"Citigems",
		"Must have (go-live)",
	),
	(
		"1. Legal & company",
		"Company abbreviation (3–5 letters)",
		"ERPNext Company abbr., series prefixes",
		"CBS",
		"Must have (go-live)",
	),
	(
		"1. Legal & company",
		"Country of incorporation / operations",
		"Tax, address, currency defaults",
		"Benin (BJ)",
		"Must have (go-live)",
	),
	(
		"1. Legal & company",
		"Full postal / physical address (campus)",
		"Invoices, ID cards, website Contact",
		"Quartier …, Cotonou, Bénin",
		"Must have (go-live)",
	),
	(
		"1. Legal & company",
		"GPS / map link for campus (optional)",
		"Public website map",
		"Google Maps URL",
		"Later (phase 2)",
	),
	(
		"1. Legal & company",
		"Primary phone (reception)",
		"Website, invoices, SMS sender context",
		"+229 XX XX XX XX",
		"Must have (go-live)",
	),
	(
		"1. Legal & company",
		"WhatsApp business number (if any)",
		"Website CTAs, parent comms",
		"+229 …",
		"Should have (month 1-3)",
	),
	(
		"1. Legal & company",
		"Public email (admissions / contact)",
		"Website forms, ERP email accounts",
		"contact@citigemsschool.bj",
		"Must have (go-live)",
	),
	(
		"1. Legal & company",
		"Finance / billing email",
		"Fee receipts, MeCeF / accounting",
		"finance@…",
		"Must have (go-live)",
	),
	(
		"1. Legal & company",
		"Preferred working language(s)",
		"Desk + portal + website (FR default today)",
		"Français (primary), English (bilingual)",
		"Must have (go-live)",
	),
	(
		"1. Legal & company",
		"Academic year calendar (start / end dates)",
		"Education Academic Year, fees, report cards",
		"01/09/2026 – 30/06/2027",
		"Must have (go-live)",
	),
	(
		"1. Legal & company",
		"Terms / trimesters (names + date ranges)",
		"Academic Term, gradebooks, fee schedules",
		"T1 Sep–Dec; T2 Jan–Mar; T3 Apr–Jun",
		"Must have (go-live)",
	),
	(
		"1. Legal & company",
		"School logo (PNG/SVG, high-res) + favicon",
		"ERP branding, website, ID cards, print formats",
		"Attach files",
		"Must have (go-live)",
	),
	(
		"1. Legal & company",
		"Brand colours / fonts (if any guide)",
		"Website + portal chrome",
		"Hex codes or brand PDF",
		"Should have (month 1-3)",
	),
	# —— 2. Tax / MeCeF ——
	(
		"2. Tax compliance (DGI / e-MECeF)",
		"IFU (Identifiant Fiscal Unique)",
		"MeCef Settings — e-invoicing",
		"XXXXXXXXXXXX",
		"Must have (go-live)",
	),
	(
		"2. Tax compliance (DGI / e-MECeF)",
		"NIM / SFE device identifiers (sandbox + live)",
		"MeCef Settings, normalised invoices",
		"Attach DGI onboarding sheet",
		"Must have (go-live)",
	),
	(
		"2. Tax compliance (DGI / e-MECeF)",
		"MeCeF API host + Bearer token (Desk only — never email in clear if avoidable)",
		"MeCef Settings → invoice API",
		"Sandbox first, then production",
		"Must have (go-live)",
	),
	(
		"2. Tax compliance (DGI / e-MECeF)",
		"Default tax groups / VAT treatment for school fees vs shop sales",
		"MECeF tax templates A/B, Sales Invoice",
		"Fees exempt? Shop items taxable?",
		"Must have (go-live)",
	),
	(
		"2. Tax compliance (DGI / e-MECeF)",
		"Legal invoice footer text (required mentions)",
		"Print format Facture MECeF",
		"Attach sample paper invoice",
		"Should have (month 1-3)",
	),
	# —— 3. Banking & fees payments ——
	(
		"3. Fees & payments (FedaPay / banks)",
		"Bank account(s): bank name, IBAN/RIB, account name",
		"Accounting, reconciliation, fee deposits",
		"BOA / Ecobank / …",
		"Must have (go-live)",
	),
	(
		"3. Fees & payments (FedaPay / banks)",
		"FedaPay merchant account (Sandbox + Live API keys, webhook secret)",
		"FedaPay Settings + /edu-portal « Payer les frais »",
		"Desk only — never commit to git",
		"Must have (go-live)",
	),
	(
		"3. Fees & payments (FedaPay / banks)",
		"Accepted Mobile Money operators",
		"Mode of Payment, portal UX",
		"MTN MoMo, Moov, Celtiis, …",
		"Must have (go-live)",
	),
	(
		"3. Fees & payments (FedaPay / banks)",
		"Fee currency display preference",
		"Amounts show as 5,500 FCFA (ISO XOF)",
		"FCFA after amount (already default)",
		"Must have (go-live)",
	),
	(
		"3. Fees & payments (FedaPay / banks)",
		"Complete fee catalogue for next academic year",
		"Fee Structure / Fee Category / Sales Items",
		"Tuition, registration, transport, canteen, exam…",
		"Must have (go-live)",
	),
	(
		"3. Fees & payments (FedaPay / banks)",
		"Amounts per programme / class / term (XOF)",
		"Fee Structure amounts",
		"Attach Excel fee grid",
		"Must have (go-live)",
	),
	(
		"3. Fees & payments (FedaPay / banks)",
		"Payment plans (lump sum, termly, monthly) + due dates",
		"Payment Schedule, reminders",
		"30% at registration + 3 termly",
		"Must have (go-live)",
	),
	(
		"3. Fees & payments (FedaPay / banks)",
		"Discounts / scholarships / sibling rules",
		"Pricing rules, fee adjustments",
		"10% second child, staff children, …",
		"Should have (month 1-3)",
	),
	(
		"3. Fees & payments (FedaPay / banks)",
		"Late payment penalties / blocking rules (report card hold?)",
		"Portal + academic policies",
		"Describe policy in writing",
		"Should have (month 1-3)",
	),
	(
		"3. Fees & payments (FedaPay / banks)",
		"Receipt / invoice numbering preference",
		"Naming series",
		"CBS-FAC-.YYYY.-",
		"Should have (month 1-3)",
	),
	# —— 4. Student information ——
	(
		"4. Student information system",
		"List of programmes / streams offered",
		"Program, Course, website programmes",
		"Maternelle, Primaire, Collège, Lycée; FR/EN tracks",
		"Must have (go-live)",
	),
	(
		"4. Student information system",
		"Classes / levels for next year (name + capacity)",
		"Student Group / Batch",
		"CP1-A (30), 6ème B (35), …",
		"Must have (go-live)",
	),
	(
		"4. Student information system",
		"Student ID numbering scheme",
		"Student naming series / ID cards",
		"CBS-2026-0001",
		"Must have (go-live)",
	),
	(
		"4. Student information system",
		"Mandatory student fields beyond defaults",
		"Custom fields, admissions forms, ID cards",
		"Blood group, nationality, religion, allergies, …",
		"Must have (go-live)",
	),
	(
		"4. Student information system",
		"Guardian / parent data required",
		"Guardian, portal login, fee payer",
		"Name, phone, email, relationship, employer",
		"Must have (go-live)",
	),
	(
		"4. Student information system",
		"Initial student roster (or migration file)",
		"Bulk import Student + Guardians",
		"Excel: name, DOB, sex, class, guardians…",
		"Must have (go-live)",
	),
	(
		"4. Student information system",
		"Admissions workflow (steps, documents, fees)",
		"Admissions + website Apply",
		"Application → test → interview → deposit",
		"Should have (month 1-3)",
	),
	(
		"4. Student information system",
		"Required admission documents checklist",
		"Admissions portal / website",
		"Birth certificate, vaccine card, photos, …",
		"Should have (month 1-3)",
	),
	(
		"4. Student information system",
		"ID card layout preferences (photo, QR, fields)",
		"Student ID print format",
		"Attach sample card or sketch",
		"Later (phase 2)",
	),
	# —— 5. Academic ——
	(
		"5. Academic management",
		"Subjects per class / programme (+ coefficients)",
		"Course, Assessment criteria, report cards",
		"Maths ×4, English ×3, …",
		"Must have (go-live)",
	),
	(
		"5. Academic management",
		"Grading scale (min/max, pass mark, letter grades)",
		"Assessment, report cards",
		"0–20, pass ≥10; or A–F",
		"Must have (go-live)",
	),
	(
		"5. Academic management",
		"Assessment types (devoir, composition, oral…)",
		"Assessment Group / Plan",
		"Attach gradebook policy",
		"Must have (go-live)",
	),
	(
		"5. Academic management",
		"Report card template(s) + bilingual needs",
		"Student Report Generation / print",
		"Attach current bulletin PDF",
		"Must have (go-live)",
	),
	(
		"5. Academic management",
		"Transcript / attestation templates",
		"Academic certificates",
		"Attach samples",
		"Later (phase 2)",
	),
	(
		"5. Academic management",
		"Timetable rules (periods/day, days/week, breaks)",
		"Course Scheduling",
		"8 periods, Mon–Fri, lunch 12:00–13:00",
		"Should have (month 1-3)",
	),
	(
		"5. Academic management",
		"Rooms / teaching spaces list",
		"Room, timetable",
		"Salle A1, Labo Sciences, Terrain…",
		"Should have (month 1-3)",
	),
	(
		"5. Academic management",
		"Attendance rules (present/absent/late, half-day)",
		"Student Attendance, portal",
		"Describe policy",
		"Should have (month 1-3)",
	),
	# —— 6. Teacher portal ——
	(
		"6. Teacher portal",
		"Staff roster: teachers + roles + subjects taught",
		"Employee + Instructor + User accounts",
		"Excel: name, email, phone, subjects, classes",
		"Must have (go-live)",
	),
	(
		"6. Teacher portal",
		"Lesson plan template expectations",
		"Teacher portal content",
		"Attach current template if any",
		"Later (phase 2)",
	),
	(
		"6. Teacher portal",
		"Who may enter grades / attendance (rules)",
		"Role permissions",
		"Class teacher only vs subject teacher",
		"Must have (go-live)",
	),
	# —— 7. Parent & student portal ——
	(
		"7. Parent & student portal",
		"What parents must see at go-live",
		"/edu-portal + website login",
		"Fees + statements first; then grades/attendance",
		"Must have (go-live)",
	),
	(
		"7. Parent & student portal",
		"Student self-service scope (if any)",
		"Portal roles",
		"View-only grades? No fee pay for students?",
		"Should have (month 1-3)",
	),
	(
		"7. Parent & student portal",
		"Notification preferences (email / SMS / WhatsApp)",
		"Reminders for fees, announcements",
		"Email primary; SMS optional",
		"Should have (month 1-3)",
	),
	(
		"7. Parent & student portal",
		"SMS / email gateway credentials (if school provides)",
		"Notification settings",
		"Provider name + keys (Desk only)",
		"Later (phase 2)",
	),
	# —— 8. Admin dashboard ——
	(
		"8. School admin dashboard",
		"List of admin users + roles to create",
		"User + Role Profile (Director, Accountant, …)",
		"Name, email, role",
		"Must have (go-live)",
	),
	(
		"8. School admin dashboard",
		"KPI / reports leadership wants on dashboard",
		"Workspace, analytics",
		"Enrolment, fee collection %, attendance %",
		"Should have (month 1-3)",
	),
	(
		"8. School admin dashboard",
		"Announcement channels & approval workflow",
		"Website news + in-app notices",
		"Who publishes? Who approves?",
		"Should have (month 1-3)",
	),
	# —— 9. Accounting ——
	(
		"9. Accounting",
		"Chart of Accounts preference (ERPNext default vs custom)",
		"Company CoA",
		"Use standard BJ/XOF CoA + school cost centers",
		"Must have (go-live)",
	),
	(
		"9. Accounting",
		"Fiscal year start date",
		"Fiscal Year",
		"01/01 or 01/09?",
		"Must have (go-live)",
	),
	(
		"9. Accounting",
		"Cost centers / departments",
		"Accounting dimensions, budgets",
		"Primary, Secondary, Admin, Transport…",
		"Should have (month 1-3)",
	),
	(
		"9. Accounting",
		"Opening balances (bank, cash, receivables) at cutover",
		"Journal Entry / opening",
		"Attach trial balance",
		"Must have (go-live)",
	),
	(
		"9. Accounting",
		"Existing unpaid student balances to migrate",
		"Sales Invoice / Fee outstanding",
		"Excel: student, amount, due date",
		"Must have (go-live)",
	),
	(
		"9. Accounting",
		"Budget for next year (optional)",
		"Budget doctype",
		"Attach spreadsheet",
		"Later (phase 2)",
	),
	(
		"9. Accounting",
		"Bank statement access for reconciliation process",
		"Bank Reconciliation",
		"Who reconciles? Frequency?",
		"Should have (month 1-3)",
	),
	# —— 10. HRMS ——
	(
		"10. HRMS (employees)",
		"Full employee list (admin + teaching + support)",
		"Employee master",
		"Excel: name, DOB, ID, role, hire date, salary",
		"Must have (go-live)",
	),
	(
		"10. HRMS (employees)",
		"Contract types & leave policy",
		"HRMS Leave / Contract",
		"CDI/CDD; annual leave days",
		"Should have (month 1-3)",
	),
	(
		"10. HRMS (employees)",
		"Payroll basics (pay frequency, components, CNSS if applicable)",
		"Payroll Entry / Salary Structure",
		"Monthly; basic + allowances",
		"Should have (month 1-3)",
	),
	(
		"10. HRMS (employees)",
		"Organisational chart / reporting lines",
		"Department, reports_to",
		"Attach org chart",
		"Later (phase 2)",
	),
	# —— 11. Stock ——
	(
		"11. Stock & inventory",
		"Warehouses / stores locations",
		"Warehouse",
		"Main store, Uniform shop, Library",
		"Should have (month 1-3)",
	),
	(
		"11. Stock & inventory",
		"Item catalogue: textbooks, uniforms, supplies, assets",
		"Item + Item Group",
		"Excel with SKU, price, track serial/batch?",
		"Should have (month 1-3)",
	),
	(
		"11. Stock & inventory",
		"Opening stock quantities & valuations",
		"Stock Reconciliation",
		"Attach inventory count",
		"Later (phase 2)",
	),
	(
		"11. Stock & inventory",
		"Asset register (furniture, IT, vehicles) if managed in ERP",
		"Asset module",
		"Optional — list if in scope now",
		"Optional",
	),
	# —— 12. Public website ——
	(
		"12. Public website (citigemsschool-website)",
		"Preferred public domain name(s)",
		"DNS + SSL; links to ERP portal",
		"www.citigemsschool.bj / .com",
		"Must have (go-live)",
	),
	(
		"12. Public website (citigemsschool-website)",
		"ERP / portal hostname for login deep-links",
		"Website → Education portal + ERPNext",
		"edu.citigemsschool… or sslip test URL now",
		"Must have (go-live)",
	),
	(
		"12. Public website (citigemsschool-website)",
		"Homepage hero copy (FR ± EN) + photos/video",
		"Website landing",
		"Attach approved text + media",
		"Must have (go-live)",
	),
	(
		"12. Public website (citigemsschool-website)",
		"Programme pages content (per track/level)",
		"Website programmes showcase",
		"Word/PDF per programme",
		"Must have (go-live)",
	),
	(
		"12. Public website (citigemsschool-website)",
		"Admissions page content + online form fields",
		"Website admissions → ERP",
		"Deadlines, fees, required docs",
		"Must have (go-live)",
	),
	(
		"12. Public website (citigemsschool-website)",
		"News / blog: who writes, how often",
		"Website news",
		"Weekly? French only?",
		"Should have (month 1-3)",
	),
	(
		"12. Public website (citigemsschool-website)",
		"Social media links",
		"Website footer",
		"Facebook, Instagram, LinkedIn, YouTube",
		"Should have (month 1-3)",
	),
	(
		"12. Public website (citigemsschool-website)",
		"Legal pages: privacy, terms, cookies (GDPR-style)",
		"Website footer",
		"Provide text or ask us to draft",
		"Should have (month 1-3)",
	),
	(
		"12. Public website (citigemsschool-website)",
		"Portal login entry points to expose on site",
		"Wire to /edu-portal + Desk if needed",
		"Parent login, Staff login",
		"Must have (go-live)",
	),
	# —— 13. IT / access ——
	(
		"13. IT, security & go-live",
		"List of people who need Administrator / System Manager",
		"ERP User security",
		"Name + email",
		"Must have (go-live)",
	),
	(
		"13. IT, security & go-live",
		"Email sending domain + SMTP or relay",
		"Email Account (receipts, resets)",
		"mail.citigemsschool…",
		"Must have (go-live)",
	),
	(
		"13. IT, security & go-live",
		"Backup / hosting contacts on school side",
		"Ops escalation",
		"Name, phone",
		"Should have (month 1-3)",
	),
	(
		"13. IT, security & go-live",
		"Target go-live date + training windows",
		"Project plan",
		"e.g. before rentrée 2026",
		"Must have (go-live)",
	),
	(
		"13. IT, security & go-live",
		"Data migration cutover date (stop old Excel/tools)",
		"Import planning",
		"YYYY-MM-DD",
		"Must have (go-live)",
	),
	(
		"13. IT, security & go-live",
		"Existing systems to replace / integrate (Excel, other software)",
		"Avoid double entry",
		"List tools + export availability",
		"Must have (go-live)",
	),
]


def style_header(ws):
	fill = PatternFill("solid", fgColor="1F4E79")
	font = Font(color="FFFFFF", bold=True, name="Calibri", size=11)
	thin = Border(
		left=Side(style="thin", color="B0B0B0"),
		right=Side(style="thin", color="B0B0B0"),
		top=Side(style="thin", color="B0B0B0"),
		bottom=Side(style="thin", color="B0B0B0"),
	)
	for col, title in enumerate(HEADERS, 1):
		cell = ws.cell(1, col, title)
		cell.fill = fill
		cell.font = font
		cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
		cell.border = thin
	ws.row_dimensions[1].height = 32
	ws.freeze_panes = "A2"
	ws.auto_filter.ref = f"A1:{get_column_letter(len(HEADERS))}1"


def add_rows(ws):
	thin = Border(
		left=Side(style="thin", color="D0D0D0"),
		right=Side(style="thin", color="D0D0D0"),
		top=Side(style="thin", color="D0D0D0"),
		bottom=Side(style="thin", color="D0D0D0"),
	)
	alt = PatternFill("solid", fgColor="F5F9FC")
	must = PatternFill("solid", fgColor="FFF2CC")
	wrap = Alignment(wrap_text=True, vertical="top")
	for i, (module, question, why, example, priority) in enumerate(ROWS, 1):
		r = i + 1
		values = [
			module,
			i,
			question,
			why,
			example,
			"",  # owner answer
			"Not started",
			priority,
			"",
		]
		for c, val in enumerate(values, 1):
			cell = ws.cell(r, c, val)
			cell.border = thin
			cell.alignment = wrap
			if i % 2 == 0:
				cell.fill = alt
			if c == 8 and priority.startswith("Must"):
				cell.fill = must
		ws.row_dimensions[r].height = 36

	# validations
	dv_status = DataValidation(type="list", formula1=STATUS_OPTS, allow_blank=True)
	dv_prio = DataValidation(type="list", formula1=PRIORITY_OPTS, allow_blank=True)
	ws.add_data_validation(dv_status)
	ws.add_data_validation(dv_prio)
	last = len(ROWS) + 1
	dv_status.add(f"G2:G{last}")
	dv_prio.add(f"H2:H{last}")


def set_widths(ws):
	widths = [28, 5, 48, 36, 34, 32, 14, 22, 28]
	for i, w in enumerate(widths, 1):
		ws.column_dimensions[get_column_letter(i)].width = w


def write_readme(wb):
	ws = wb.create_sheet("0. Instructions", 0)
	ws["A1"] = "Citigems Bilingual School — Configuration questionnaire"
	ws["A1"].font = Font(bold=True, size=16, color="1F4E79")
	lines = [
		"",
		"Purpose",
		"Collect every piece of information needed to fully configure the integrated school management system",
		"(ERPNext Education + HRMS + Accounting + e-MECeF + FedaPay + parent portal) and the public website",
		"repo citigemsschool-website (wired to the Education portal and ERPNext).",
		"",
		"How to use",
		"1. Owner (or designate) fills column « Owner answer » on sheet « 1. Questionnaire ».",
		"2. Update Status: Not started → In progress → Received → Validated (or N/A).",
		"3. Attach supporting files (rosters, fee grids, logos, DGI docs) and note filenames in « Notes ».",
		"4. Yellow priority = Must have for go-live.",
		"",
		"Already seeded in ERP (do not re-ask unless changing)",
		"• Company: Citigems Bilingual School (CBS) — Benin, XOF/FCFA, French",
		"• Stack: ERPNext v16, Education, HRMS, Payments + citigems_custom",
		"• Fee portal path: /edu-portal « Payer les frais » (needs FedaPay keys)",
		"• Tax: MeCef Settings (needs IFU / NIM / API token)",
		"",
		"Website",
		"• Public site lives in /home/citigems/citigemsschool-website",
		"• Will deep-link to ERP Education portal and staff Desk after domains are confirmed",
		"",
		"Confidential",
		"• Never put live API secrets in shared chat if avoidable — deliver via secure channel into Desk settings.",
		"",
		"Scope reference (proposal §0)",
		"Student IS · Academic · Fees & billing · Accounting · Parent/student portal · Teacher portal ·",
		"Admin dashboard · HRMS · Stock · Tax (DGI API) · Public school website — all role-based and integrated.",
	]
	for i, line in enumerate(lines, 2):
		ws.cell(i, 1, line)
		if line in ("Purpose", "How to use", "Already seeded in ERP (do not re-ask unless changing)", "Website", "Confidential", "Scope reference (proposal §0)"):
			ws.cell(i, 1).font = Font(bold=True, color="1F4E79")
	ws.column_dimensions["A"].width = 110


def write_checklist(wb):
	ws = wb.create_sheet("2. Module checklist")
	ws["A1"] = "Module"
	ws["B1"] = "In proposal scope"
	ws["C1"] = "ERP / website surface"
	ws["D1"] = "Config ready when…"
	for cell in ws[1]:
		cell.fill = PatternFill("solid", fgColor="1F4E79")
		cell.font = Font(color="FFFFFF", bold=True)
	mods = [
		("Student information system", "Yes", "Education Student / Guardian / Admissions", "Roster + ID scheme + admission docs received"),
		("Academic management", "Yes", "Course, Assessment, Timetable, Report Card", "Subjects, scale, bulletin template received"),
		("Fee & billing + Mobile Money", "Yes", "Fee Structure, Sales Invoice, FedaPay, /edu-portal", "Fee grid + FedaPay keys + bank accounts"),
		("Accounting", "Yes", "ERPNext Accounts", "Fiscal year, CoA choice, opening balances"),
		("Parent & student portal", "Yes", "/edu-portal + website login", "Role matrix + go-live feature list"),
		("Teacher portal", "Yes", "Instructor users + grade/attendance entry", "Teacher roster + permission rules"),
		("School admin dashboard", "Yes", "Workspaces / roles", "Admin users + KPIs defined"),
		("HRMS", "Yes", "HRMS Employee / Leave / Payroll", "Employee file + leave/payroll policy"),
		("Stock & inventory", "Yes", "Stock Item / Warehouse", "Item list + warehouses (+ opening stock)"),
		("Tax compliance (DGI / MeCeF)", "Yes", "MeCef Settings + SI normalise", "IFU/NIM/token + tax treatment"),
		("Public school website", "Yes", "citigemsschool-website → portal/ERP", "Domain + content + portal URLs"),
	]
	for i, row in enumerate(mods, 2):
		for c, v in enumerate(row, 1):
			ws.cell(i, c, v)
	for col, w in enumerate([34, 16, 42, 48], 1):
		ws.column_dimensions[get_column_letter(col)].width = w


def write_attachments(wb):
	ws = wb.create_sheet("3. Attachments index")
	headers = ["#", "Expected file", "From owner?", "Received (Y/N)", "Filename / link", "Notes"]
	for c, h in enumerate(headers, 1):
		cell = ws.cell(1, c, h)
		cell.fill = PatternFill("solid", fgColor="1F4E79")
		cell.font = Font(color="FFFFFF", bold=True)
	files = [
		"School logo + favicon",
		"Brand guide (optional)",
		"Academic calendar PDF",
		"Fee grid Excel (by class/term)",
		"Student import Excel",
		"Guardian/parent import Excel",
		"Teacher/employee Excel",
		"Opening balances / trial balance",
		"Outstanding fees migration Excel",
		"Current report card (bulletin) sample",
		"Transcript / attestation sample",
		"ID card sample",
		"DGI / MeCeF onboarding pack",
		"FedaPay merchant confirmation",
		"Bank RIB(s)",
		"Website programme texts + photos",
		"Admissions policy + document checklist",
		"Org chart",
		"Inventory / uniform / textbook list",
		"Privacy / terms drafts (or approval to draft)",
	]
	for i, name in enumerate(files, 1):
		ws.cell(i + 1, 1, i)
		ws.cell(i + 1, 2, name)
		ws.cell(i + 1, 3, "Yes")
		ws.cell(i + 1, 4, "")
	for col, w in enumerate([5, 42, 14, 14, 36, 28], 1):
		ws.column_dimensions[get_column_letter(col)].width = w


def main():
	wb = Workbook()
	# questionnaire sheet
	ws = wb.active
	ws.title = "1. Questionnaire"
	style_header(ws)
	add_rows(ws)
	set_widths(ws)
	write_readme(wb)
	write_checklist(wb)
	write_attachments(wb)
	OUT.parent.mkdir(parents=True, exist_ok=True)
	wb.save(OUT)
	print(f"Wrote {OUT} ({len(ROWS)} questions)")


if __name__ == "__main__":
	main()
