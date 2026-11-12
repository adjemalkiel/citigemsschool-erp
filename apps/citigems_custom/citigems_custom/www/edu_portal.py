"""Boot the Education SPA at /edu-portal (default template + Citigems chrome)."""

import frappe

from citigems_custom.branding import MARKETING_NAME, SCHOOL_LOGO

no_cache = 1


def get_context(context):
	logo = None
	try:
		logo = frappe.db.get_single_value("Education Settings", "school_college_logo")
	except Exception:
		pass

	context.no_cache = 1
	context.abbr = MARKETING_NAME
	context.logo = logo or SCHOOL_LOGO
	# Stock {{ frappe.session.csrf_token }} can render None for Website Users.
	context.csrf_token = frappe.sessions.get_csrf_token()
