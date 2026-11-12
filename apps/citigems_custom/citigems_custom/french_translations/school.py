"""Citigems school CSV overrides (élève, scolarité, bulletin, frais, tuteur).

XOF stays the ISO code in data; French UI labels/amounts use FCFA
(``5,500 FCFA`` — see ``locale.ensure_xof_fcfa_display``).
"""

FR_SCHOOL_TRANSLATIONS = {
	"Citigems School": "Citigems School",
	"Citigems Bilingual School": "Citigems Bilingual School",
	"Powered by DevOps": "Propulsé par DevOps",
	"Pay Fees": "Payer les frais",
	"Payer les frais": "Payer les frais",
	"Outstanding Fees": "Frais à régler",
	"Fee Statement": "Relevé de frais",
	"School Fees": "Frais de scolarité",
	"Tuition": "Scolarité",
	"Report Card": "Bulletin",
	"Student": "Élève",
	"Guardian": "Tuteur",
	"MeCef Settings": "Paramètres MeCef",
	"FedaPay Settings": "Paramètres FedaPay",
	"FedaPay Payment": "Paiement FedaPay",
	"Demande Facture Normalisée": "Demande Facture Normalisée",
	"Normalized Invoice": "Facture normalisée",
	# Currency: ISO XOF → French display FCFA (symbol sits after the amount)
	"XOF": "FCFA",
	"FCFA": "FCFA",
	"CFA Franc": "Franc CFA",
	"CFA Franc BCEAO": "Franc CFA (BCEAO)",
	"West African CFA franc": "Franc CFA ouest-africain",
	"Currency": "Devise",
	"Amount": "Montant",
	# Student/Guardian option values stored in EN
	"Beninese": "Béninoise",
	"Female": "Femelle",
	"Male": "Mâle",
}
