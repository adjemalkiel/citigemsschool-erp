"""Sync French Translations catalog into the Translation DocType."""

import frappe


def _import(name, attr, default=None):
	try:
		mod = __import__(f"citigems_custom.french_translations.{name}", fromlist=[attr])
		return getattr(mod, attr)
	except (ImportError, AttributeError):
		return default if default is not None else {}


def _upsert_translations(language, catalog):
	for src, tr in catalog.items():
		if not src or not tr:
			continue
		name = frappe.db.get_value("Translation", {"language": language, "source_text": src})
		if name:
			frappe.db.set_value("Translation", name, "translated_text", tr)
		else:
			frappe.get_doc(
				{
					"doctype": "Translation",
					"language": language,
					"source_text": src,
					"translated_text": tr,
				}
			).insert(ignore_permissions=True)


def patch_onboarding_titles() -> None:
	onboarding = _import("onboarding", "FR_ONBOARDING_TRANSLATIONS", {})
	if not onboarding or not frappe.db.exists("DocType", "Onboarding Step"):
		return
	for name in frappe.get_all("Onboarding Step", pluck="name"):
		fr = onboarding.get(name)
		if not fr:
			continue
		action_label = frappe.db.get_value("Onboarding Step", name, "action_label")
		fields = {"title": fr}
		if action_label and action_label in onboarding:
			fields["action_label"] = onboarding[action_label]
		elif action_label == name or not action_label:
			fields["action_label"] = fr
		frappe.db.set_value("Onboarding Step", name, fields, update_modified=False)

	for row in frappe.get_all("Module Onboarding", fields=["name", "title"]):
		fr = onboarding.get(row.title)
		if fr:
			frappe.db.set_value("Module Onboarding", row.name, "title", fr, update_modified=False)


def sync_translations():
	catalog = {}
	for mod, attr in (
		("catalog", "FR_DESK_TRANSLATIONS"),
		("stock", "FR_STOCK_TRANSLATIONS"),
		("education", "FR_EDUCATION_TRANSLATIONS"),
		("login", "FR_LOGIN_TRANSLATIONS"),
		("onboarding", "FR_ONBOARDING_TRANSLATIONS"),
		("school", "FR_SCHOOL_TRANSLATIONS"),
	):
		catalog.update(_import(mod, attr, {}))

	_upsert_translations("fr", catalog)
	patch_onboarding_titles()
	frappe.db.commit()
	frappe.clear_cache()
