# Proposal backlog (post-foundation)

Modules from the Citigems school ERP proposal that are **not** built in the foundation pass (Docker stack + `citigems_custom` with FR branding, e-MECeF, FedaPay fee pay). Track here for later configuration / sibling work.

| Module | Later configuration |
|--------|---------------------|
| Student Information System | Admissions workflows, ID cards, class lists beyond Education defaults |
| Academic management | Timetables, gradebook depth, report cards, transcripts |
| Teacher portal | Lesson plans, attendance UX |
| Parent & student portal | Full grades/attendance UX beyond fee pay (`/edu-portal` fees + statements first) |
| School admin dashboard | Analytics, announcements |
| Stock & inventory | Textbooks, uniforms, assets |
| Public school website | Sibling repo `citigemsschool-website` |
| Accounting depth | Budgets, bank reconciliation, cost centers |
| HRMS depth | Contracts, leave, payroll beyond HRMS defaults |
| Tax compliance ops | DGI production SFE certification (test cases), live NIM |

## Foundation already covering

- ERPNext Education + HRMS + Payments (Docker `apps.json`)
- Company **Citigems Bilingual School**, BJ, XOF, language `fr` (seed script)
- French desk + DevOps branding
- MeCef Settings + Sales Invoice normalise (POST then PUT confirm) + QR print helpers
- FedaPay Settings / Payment + portal « Payer les frais » + webhook
