import frappe

no_cache = 1


def get_context(context):
	"""Edu portal: fees + statements first (Guardian / Student)."""
	abbr = None
	logo = None
	try:
		abbr = frappe.db.get_single_value(
			"Education Settings", "school_college_name_abbreviation"
		)
		logo = frappe.db.get_single_value("Education Settings", "school_college_logo")
	except Exception:
		pass

	context.no_cache = 1
	context.abbr = abbr or "Citigems"
	context.logo = logo or "/assets/citigems_custom/images/devops-logo.svg"
	context.powered_by = "Powered by DevOps"
	context.user = frappe.session.user
	context.is_guest = frappe.session.user == "Guest"
