"""Fix Education's broken deep-link rule for /edu-portal/*.

education.hooks maps ``/edu-portal/<path>`` → endpoint ``edu-portal`` (hyphen),
but the www page is ``edu_portal`` (underscore). First match wins → 404 on
reload / language change when the SPA URL is e.g. ``/edu-portal/fees``.
"""

from __future__ import annotations

import frappe

_patched = False


def patch_edu_portal_deep_routes():
	"""Drop the hyphen endpoint rule so citigems ``edu_portal`` handles deep paths."""
	global _patched
	if _patched:
		return
	from frappe.website import path_resolver

	_orig = path_resolver.get_website_rules

	def get_website_rules():
		return [
			r
			for r in _orig()
			if not (
				r.get("from_route") == "/edu-portal/<path:app_path>"
				and r.get("to_route") == "edu-portal"
			)
		]

	path_resolver.get_website_rules = get_website_rules
	try:
		frappe.cache.delete_value("website_route_rules")
	except Exception:
		pass
	_patched = True


def _selfcheck_filters_hyphen_rule():
	rules = [
		{"from_route": "/edu-portal/<path:app_path>", "to_route": "edu-portal"},
		{"from_route": "/edu-portal", "to_route": "edu_portal"},
		{"from_route": "/edu-portal/<path:app_path>", "to_route": "edu_portal"},
	]
	out = [
		r
		for r in rules
		if not (
			r.get("from_route") == "/edu-portal/<path:app_path>"
			and r.get("to_route") == "edu-portal"
		)
	]
	assert len(out) == 2
	assert all(r["to_route"] == "edu_portal" for r in out)
	return out
