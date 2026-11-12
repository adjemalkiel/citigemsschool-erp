"""Sync French Translations catalog into the Translation DocType."""

from __future__ import annotations

import csv
from pathlib import Path

import frappe


def _import(name, attr, default=None):
	try:
		mod = __import__(f"citigems_custom.french_translations.{name}", fromlist=[attr])
		return getattr(mod, attr)
	except (ImportError, AttributeError):
		return default if default is not None else {}


def _load_berakha_csv() -> dict[str, str]:
	"""Full FR dump from Berakha/DevOps ERPNext (POS / URY / Maya already filtered out)."""
	path = Path(__file__).with_name("berakha_fr.csv")
	if not path.is_file():
		return {}
	out: dict[str, str] = {}
	with path.open(newline="", encoding="utf-8") as f:
		for row in csv.DictReader(f):
			if (row.get("language") or "").strip() != "fr":
				continue
			src = (row.get("source_text") or "").strip()
			tr = (row.get("translated_text") or "").strip()
			if src and tr:
				out[src] = tr
	return out


def _upsert_translations(language, catalog):
	for src, tr in catalog.items():
		if not src or not tr:
			continue
		# BINARY match — keep both "Forgot password?" and "Forgot Password?" rows
		# (MariaDB CI would otherwise treat them as one for non-binary lookups).
		exact = frappe.db.sql(
			"SELECT name FROM `tabTranslation` WHERE language=%s AND BINARY source_text=%s LIMIT 1",
			(language, src),
		)
		if exact:
			frappe.db.set_value("Translation", exact[0][0], "translated_text", tr)
			continue
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
	# Layer: Berakha dump → module catalogs → school overrides (last wins).
	catalog = _load_berakha_csv()
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
	return {"count": len(catalog)}
