"""Citigems School branding with Powered by DevOps chrome."""

import frappe

BRAND_REPLACEMENTS = (
	("ERPNext", "DevOps"),
	("Frappe", "DevOps"),
)
PRODUCT_NAME = "Citigems School"
BRAND_TO = "DevOps"
DEVOPS_LOGO = "/assets/citigems_custom/images/devops-logo.svg"
DEVOPS_FAVICON = "/assets/citigems_custom/images/devops-favicon.svg"


def _rebrand_text(value):
	if not isinstance(value, str):
		return value
	for old, new in BRAND_REPLACEMENTS:
		if old in value:
			value = value.replace(old, new)
	return value


def _as_logo_url(value):
	"""Hooks often return a list; Desk expects a string (else img src=undefined)."""
	if isinstance(value, (list, tuple)):
		return value[0] if value else None
	return value if isinstance(value, str) else None


def boot_session(bootinfo):
	"""Patch boot payload: product = Citigems School, engine chrome = DevOps."""
	for app in bootinfo.get("app_data") or []:
		if not isinstance(app, dict):
			continue
		if app.get("app_name") == "erpnext":
			app["app_title"] = BRAND_TO
		elif app.get("app_name") == "citigems_custom":
			app["app_title"] = PRODUCT_NAME
		elif isinstance(app.get("app_title"), str):
			app["app_title"] = _rebrand_text(app["app_title"])
		logo = _as_logo_url(app.get("app_logo_url"))
		if not logo or "frappe-framework-logo" in logo or "erpnext-logo" in logo:
			logo = DEVOPS_LOGO
		app["app_logo_url"] = logo

	sysdefaults = bootinfo.get("sysdefaults")
	if isinstance(sysdefaults, dict):
		if isinstance(sysdefaults.get("app_name"), str):
			sysdefaults["app_name"] = PRODUCT_NAME

	bootinfo["app_logo_url"] = DEVOPS_LOGO
	bootinfo["citigems_powered_by"] = "Powered by DevOps"


def update_website_context(context):
	"""Login / website chrome: Citigems product name + DevOps mark."""
	context["app_name"] = PRODUCT_NAME
	context["splash_image"] = DEVOPS_LOGO
	context["favicon"] = DEVOPS_FAVICON
	context["app_logo"] = DEVOPS_LOGO
	context["citigems_powered_by"] = "Powered by DevOps"


def ensure_website_branding():
	"""Persist Citigems app name + DevOps logo for login, navbar, website."""
	ws = frappe.get_single("Website Settings")
	changed = False
	if ws.app_name != PRODUCT_NAME:
		ws.app_name = PRODUCT_NAME
		changed = True
	if ws.meta.has_field("app_logo") and ws.app_logo != DEVOPS_LOGO:
		ws.app_logo = DEVOPS_LOGO
		changed = True
	if ws.meta.has_field("splash_image") and ws.splash_image != DEVOPS_LOGO:
		ws.splash_image = DEVOPS_LOGO
		changed = True
	if ws.meta.has_field("favicon") and ws.favicon != DEVOPS_FAVICON:
		ws.favicon = DEVOPS_FAVICON
		changed = True
	if changed:
		ws.flags.ignore_mandatory = True
		ws.save(ignore_permissions=True)

	try:
		nav = frappe.get_single("Navbar Settings")
		if getattr(nav, "app_logo", None) != DEVOPS_LOGO:
			nav.app_logo = DEVOPS_LOGO
			nav.flags.ignore_mandatory = True
			nav.save(ignore_permissions=True)
	except Exception:
		frappe.log_error(title="ensure_website_branding Navbar Settings")

	frappe.db.commit()
	frappe.clear_cache()
