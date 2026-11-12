app_name = "citigems_custom"
app_title = "Citigems School"
app_publisher = "Malkiel Adje"
app_description = "Citigems Bilingual School — e-MECeF, FedaPay, French branding (Powered by DevOps)"
app_email = "adjemalkiel@gmail.com"
app_license = "mit"
app_version = "0.0.1"

website_route_rules = [
	{"from_route": "/edu-portal", "to_route": "edu_portal"},
	{"from_route": "/edu-portal/<path:app_path>", "to_route": "edu_portal"},
]

doc_events = {
	"Sales Invoice": {
		"on_submit": [
			"citigems_custom.api.sales_invoice.on_submit",
		]
	},
}

doctype_js = {
	"Sales Invoice": "public/js/sales_invoice.js",
	"Student Report Generation Tool": "public/js/student_report_generation_tool.js",
}

override_whitelisted_methods = {
	"education.education.doctype.student_report_generation_tool.student_report_generation_tool.preview_report_card":
		"citigems_custom.education_report.preview_report_card",
	"education.education.api.get_student_invoices":
		"citigems_custom.api.education_portal.get_student_invoices",
	"education.education.api.get_course_schedule_for_student":
		"citigems_custom.api.education_portal.get_course_schedule_for_student",
	"education.education.api.get_student_attendance":
		"citigems_custom.api.education_portal.get_student_attendance",
}

jinja = {
	"methods": [
		"citigems_custom.api.sales_invoice.mecef_qr_base64",
		"citigems_custom.api.sales_invoice.file_to_data_uri",
	]
}

fixtures = [
	{
		"dt": "Custom Field",
		"filters": [
			[
				"fieldname",
				"in",
				[
					"demande_facture_normalisee",
					"mecef_section",
					"mecef_numero",
					"mecef_qr_code",
					"mecef_nim",
					"mecef_envoye",
					"mecef_tax_group",
					"fedapay_section",
					"fedapay_payment",
					"mobile_money_operator",
					"mobile_money_phone",
					"fedapay_transaction_id",
					"desk_ui_theme",
				],
			]
		],
	},
	{
		"dt": "Mode of Payment",
		"filters": [["name", "in", ["Mobile Money", "Espèces"]]],
	},
	{
		"dt": "Print Format",
		"filters": [["name", "in", ["Facture MECeF Citigems"]]],
	},
]

app_include_css = [
	"/assets/citigems_custom/css/citigems_brand.css?v=20261111q",
]
app_include_js = [
	"/assets/citigems_custom/js/citigems_rebrand.js?v=20261111q",
	"/assets/citigems_custom/js/desk_theme_loader.js",
]

web_include_css = [
	"/assets/citigems_custom/css/citigems_brand.css?v=20261111q",
]
web_include_js = [
	"/assets/citigems_custom/js/citigems_rebrand.js?v=20261111q",
	"/assets/citigems_custom/js/desk_theme_loader.js",
]

update_website_context = [
	"citigems_custom.branding.update_website_context",
]

# Website Users with Guardian/Student → /edu-portal; Desk stays stock /app.
# Stock login honors redirect-to before this hook.
get_website_user_home_page = "citigems_custom.website_home.get_website_user_home_page"

boot_session = [
	"citigems_custom.branding.boot_session",
	"citigems_custom.desk_theme.inject_bootinfo",
]

app_logo_url = "/assets/citigems_custom/images/citigems-logo.png"
website_context = {
	"favicon": "/assets/citigems_custom/images/citigems-favicon.png",
	"splash_image": "/assets/citigems_custom/images/citigems-logo.png",
	"app_name": "Citigems School",
}

after_migrate = [
	"citigems_custom.french_translations.sync.sync_translations",
	"citigems_custom.branding.ensure_website_branding",
	"citigems_custom.locale.ensure_site_language",
	"citigems_custom.locale.ensure_xof_fcfa_display",
	"citigems_custom.desk_theme.ensure_user_field",
	"citigems_custom.education_workspace.ensure_education_workspace",
	"citigems_custom.website_home.ensure_portal_roles_no_desk",
]

after_install = "citigems_custom.install.after_install"

before_request = [
	"citigems_custom.website_routes.patch_edu_portal_deep_routes",
	"citigems_custom.locale.force_site_language_for_guests",
	"citigems_custom.website_home.redirect_website_users_from_desk",
]

try:
	from citigems_custom.education_report import install_report_card_patch

	install_report_card_patch()
except Exception:
	pass
