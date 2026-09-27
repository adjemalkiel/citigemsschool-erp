"""Post-install hooks for citigems_custom."""

import frappe


def after_install():
	"""Ensure French locale + branding after first install."""
	try:
		from citigems_custom.locale import ensure_site_language, ensure_xof_fcfa_display

		ensure_site_language()
		ensure_xof_fcfa_display()
	except Exception:
		frappe.log_error(title="citigems_custom after_install locale")

	try:
		from citigems_custom.branding import ensure_website_branding

		ensure_website_branding()
	except Exception:
		frappe.log_error(title="citigems_custom after_install branding")

	try:
		from citigems_custom.french_translations.sync import sync_translations

		sync_translations()
	except Exception:
		frappe.log_error(title="citigems_custom after_install translations")
