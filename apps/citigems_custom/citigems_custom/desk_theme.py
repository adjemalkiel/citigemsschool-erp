"""Desk UI theme: per-user preference with site-wide default fallback."""

from __future__ import annotations

import frappe

# Canonical values → User.desk_ui_theme / site_config desk_ui_theme
THEME_SAAS = "saas_theme"
THEME_DESK = "frappe_desk_theme"
THEME_FRAPPE = "frappe"  # stock / default Frappe Desk

THEMES = (THEME_SAAS, THEME_DESK, THEME_FRAPPE)

THEME_ALIASES = {
	"none": THEME_FRAPPE,
	"default": THEME_FRAPPE,
	"frappe_default": THEME_FRAPPE,
	"stock": THEME_FRAPPE,
}

THEME_LABELS = {
	THEME_SAAS: "SaaS Theme",
	THEME_DESK: "Frappe Desk Theme",
	THEME_FRAPPE: "Default Frappe",
}

DEFAULT_THEME = THEME_SAAS
USER_FIELD = "desk_ui_theme"
APPEARANCE_VALUES = {"light": "Light", "dark": "Dark", "automatic": "Automatic"}


def normalize_appearance(mode: str | None) -> str | None:
	key = (mode or "").strip().lower()
	if key in APPEARANCE_VALUES:
		return APPEARANCE_VALUES[key]
	title = (mode or "").strip().title()
	return title if title in APPEARANCE_VALUES.values() else None


@frappe.whitelist()
def set_appearance(mode: str) -> dict:
	"""Save light/dark/automatic on the current user (no User write role needed)."""
	if frappe.session.user in (None, "Guest"):
		frappe.throw(frappe._("Connectez-vous pour enregistrer vos préférences."))
	theme = normalize_appearance(mode)
	if not theme:
		frappe.throw(frappe._("Mode d'apparence invalide."))
	frappe.db.set_value("User", frappe.session.user, "desk_theme", theme, update_modified=False)
	frappe.clear_cache(user=frappe.session.user)
	return {"desk_theme": theme, "mode": theme.lower()}


def normalize_theme(theme: str | None) -> str:
	theme = (theme or "").strip()
	theme = THEME_ALIASES.get(theme, theme)
	return theme if theme in THEMES else DEFAULT_THEME


def get_site_default_theme() -> str:
	return normalize_theme(frappe.conf.get("desk_ui_theme"))


def get_desk_ui_theme(user: str | None = None) -> str:
	"""Active Desk UI theme for a user (profile → site default)."""
	user = user or getattr(frappe.session, "user", None) or "Guest"
	if user != "Guest" and frappe.get_meta("User").has_field(USER_FIELD):
		value = frappe.db.get_value("User", user, USER_FIELD)
		if value:
			return normalize_theme(value)
	return get_site_default_theme()


def inject_bootinfo(bootinfo) -> None:
	"""Expose active theme + options to Desk JS loader / switcher."""
	active = get_desk_ui_theme()
	bootinfo["desk_ui_theme"] = active
	bootinfo["desk_ui_themes"] = [
		{"value": t, "label": THEME_LABELS[t], "active": t == active} for t in THEMES
	]


@frappe.whitelist()
def set_desk_ui_theme(theme: str) -> dict:
	"""Save Desk UI theme on the current user's profile and reload."""
	if frappe.session.user in (None, "Guest"):
		frappe.throw(frappe._("Connectez-vous pour enregistrer vos préférences."))

	theme = normalize_theme(theme)
	if not frappe.get_meta("User").has_field(USER_FIELD):
		frappe.throw(frappe._("Champ profil manquant — exécutez bench migrate."))

	frappe.db.set_value("User", frappe.session.user, USER_FIELD, theme, update_modified=False)
	frappe.clear_cache(user=frappe.session.user)
	return {
		"desk_ui_theme": theme,
		"label": THEME_LABELS[theme],
		"message": frappe._("Interface {0} enregistrée pour votre profil.").format(
			THEME_LABELS[theme]
		),
	}


@frappe.whitelist()
def get_desk_ui_theme_api() -> dict:
	active = get_desk_ui_theme()
	return {
		"desk_ui_theme": active,
		"label": THEME_LABELS[active],
		"themes": [{"value": t, "label": THEME_LABELS[t]} for t in THEMES],
	}


def ensure_user_field() -> None:
	"""Custom Field on User — called from after_migrate."""
	if frappe.db.exists("Custom Field", f"User-{USER_FIELD}"):
		return
	frappe.get_doc(
		{
			"doctype": "Custom Field",
			"dt": "User",
			"fieldname": USER_FIELD,
			"label": "Desk UI Theme",
			"fieldtype": "Select",
			"options": "\n".join(THEMES),
			"insert_after": "desk_theme",
			"description": "Personal Desk interface (SaaS / Desk / Frappe). Empty = site default.",
		}
	).insert(ignore_permissions=True)


def _self_check() -> None:
	assert normalize_theme("frappe") == THEME_FRAPPE
	assert normalize_theme(None) == DEFAULT_THEME
	assert get_site_default_theme() in THEMES
