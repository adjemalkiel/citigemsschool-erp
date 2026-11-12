"""Citigems School branding with Powered by DevOps chrome."""

import frappe

BRAND_REPLACEMENTS = (
	("ERPNext", "DevOps"),
	("Frappe", "DevOps"),
)
PRODUCT_NAME = "Citigems School"
# Login / marketing chrome (product short name stays PRODUCT_NAME on Desk)
MARKETING_NAME = "Citigems Bilingual School"
DEFAULT_MARKETING_URL = "https://www.citigemsschool.com"
BRAND_TO = "DevOps"
SCHOOL_LOGO = "/assets/citigems_custom/images/citigems-logo.png"
SCHOOL_FAVICON = "/assets/citigems_custom/images/citigems-favicon.png"
DEVOPS_LOGO = "/assets/citigems_custom/images/devops-logo.svg"
DEVOPS_FAVICON = "/assets/citigems_custom/images/devops-favicon.svg"


def get_marketing_url() -> str:
	"""Public site origin from site_config ``citigems_marketing_url``, else default."""
	url = (frappe.conf.get("citigems_marketing_url") or "").strip().rstrip("/")
	return url or DEFAULT_MARKETING_URL


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
			app["app_logo_url"] = DEVOPS_LOGO
			continue
		if app.get("app_name") == "citigems_custom":
			app["app_title"] = PRODUCT_NAME
			app["app_logo_url"] = SCHOOL_LOGO
			continue
		if isinstance(app.get("app_title"), str):
			app["app_title"] = _rebrand_text(app["app_title"])
		logo = _as_logo_url(app.get("app_logo_url"))
		if not logo or "frappe-framework-logo" in logo or "erpnext-logo" in logo:
			logo = SCHOOL_LOGO
		app["app_logo_url"] = logo

	sysdefaults = bootinfo.get("sysdefaults")
	if isinstance(sysdefaults, dict):
		if isinstance(sysdefaults.get("app_name"), str):
			sysdefaults["app_name"] = PRODUCT_NAME

	bootinfo["app_logo_url"] = SCHOOL_LOGO
	bootinfo["citigems_powered_by"] = "Powered by DevOps"


def update_website_context(context):
	"""Login / website chrome: Citigems logo + marketing name; DevOps powered-by."""
	marketing_url = get_marketing_url()
	context["app_name"] = MARKETING_NAME
	context["splash_image"] = SCHOOL_LOGO
	context["favicon"] = SCHOOL_FAVICON
	context["app_logo"] = SCHOOL_LOGO
	context["citigems_powered_by"] = "Powered by DevOps"
	context["citigems_marketing_url"] = marketing_url
	# Login overrides head_include; body_include still renders from base.html
	meta = (
		f'<meta name="citigems-marketing-url" content="{frappe.utils.escape_html(marketing_url)}">'
	)
	fonts = (
		'<link rel="preconnect" href="https://fonts.googleapis.com">'
		'<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
		'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Baloo+2:wght@500;600;700;800&family=Quicksand:wght@400;500;600;700&display=swap">'
	)
	context["body_include"] = (context.get("body_include") or "") + meta
	# Prefer head; login.html replaces head_include so also put fonts in body_include.
	context["body_include"] += fonts


def ensure_website_branding():
	"""Persist Citigems app name + school logo for login, navbar, website."""
	ws = frappe.get_single("Website Settings")
	changed = False
	if ws.app_name != PRODUCT_NAME:
		ws.app_name = PRODUCT_NAME
		changed = True
	if ws.meta.has_field("app_logo") and ws.app_logo != SCHOOL_LOGO:
		ws.app_logo = SCHOOL_LOGO
		changed = True
	if ws.meta.has_field("splash_image") and ws.splash_image != SCHOOL_LOGO:
		ws.splash_image = SCHOOL_LOGO
		changed = True
	if ws.meta.has_field("favicon") and ws.favicon != SCHOOL_FAVICON:
		ws.favicon = SCHOOL_FAVICON
		changed = True
	if changed:
		ws.flags.ignore_mandatory = True
		ws.save(ignore_permissions=True)

	try:
		nav = frappe.get_single("Navbar Settings")
		if getattr(nav, "app_logo", None) != SCHOOL_LOGO:
			nav.app_logo = SCHOOL_LOGO
			nav.flags.ignore_mandatory = True
			nav.save(ignore_permissions=True)
	except Exception:
		frappe.log_error(title="ensure_website_branding Navbar Settings")

	frappe.db.commit()
	frappe.clear_cache()
