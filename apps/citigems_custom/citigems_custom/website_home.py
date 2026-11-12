"""Post-login home for portal roles (Guardian / Student → edu-portal).

Stock Education already sets ``role_home_page`` for Guardian/Student. This hook
runs *before* that map in Frappe ``get_home_page_via_hooks``, so we must return
``desk`` when a user also has non-portal roles — otherwise Administrator (or any
staff user accidentally given Guardian/Student) lands on edu-portal.

Stock login honors ``redirect-to`` before home_page is used (login.js).
"""

from __future__ import annotations

PORTAL_ROLES = frozenset({"Guardian", "Student"})
# Frappe injects these; System Users also get Desk User — ignore when detecting staff.
IGNORE_ROLES = frozenset({"All", "Guest", "Desk User"})
PORTAL_HOME = "edu-portal"
DESK_HOME = "desk"


def home_page_for_roles(roles) -> str | None:
	"""Return portal or desk route (no leading slash), or None for stock default."""
	roles = set(roles or ())
	if not PORTAL_ROLES.intersection(roles):
		return None
	# Portal + any other role → Desk (beats Education role_home_page).
	if roles - PORTAL_ROLES - IGNORE_ROLES:
		return DESK_HOME
	return PORTAL_HOME


def get_website_user_home_page(user: str) -> str | None:
	"""hooks.get_website_user_home_page — called with the logged-in user."""
	if not user or user == "Guest":
		return None
	import frappe

	return home_page_for_roles(frappe.get_roles(user))


def redirect_website_users_from_desk():
	"""Parents/students hitting /desk|/app (stale last_visited) → edu-portal.

	Must raise a Werkzeug HTTPException — ``frappe.Redirect`` in before_request
	becomes a Server Error (handle_exception has no Redirect branch).
	"""
	import frappe
	from werkzeug.routing import RequestRedirect

	user = getattr(frappe.session, "user", None)
	if not user or user in ("Guest", "Administrator"):
		return
	path = (frappe.request.path if getattr(frappe, "request", None) else "") or ""
	if not (path.startswith("/desk") or path.startswith("/app")):
		return
	if frappe.get_cached_value("User", user, "user_type") != "Website User":
		return
	raise RequestRedirect(f"/{PORTAL_HOME}")


def ensure_portal_roles_no_desk() -> dict:
	"""Education ships Guardian/Student with desk_access=1 → Frappe promotes
	those users to System User and opens Desk. Portal parents/students must
	stay Website User only.
	"""
	import frappe

	fixed_roles = []
	for role in PORTAL_ROLES:
		if not frappe.db.exists("Role", role):
			continue
		if frappe.db.get_value("Role", role, "desk_access"):
			frappe.db.set_value("Role", role, "desk_access", 0, update_modified=False)
			fixed_roles.append(role)

	# Users whose effective roles are only portal (+ ignore list) → Website User
	fixed_users = []
	candidates = set(
		frappe.get_all(
			"Has Role",
			filters={"role": ("in", list(PORTAL_ROLES)), "parenttype": "User"},
			pluck="parent",
		)
	)
	for email in candidates:
		if email in ("Administrator", "Guest"):
			continue
		roles = set(frappe.get_roles(email))
		if roles - PORTAL_ROLES - IGNORE_ROLES:
			continue  # staff (Instructor, etc.) — keep Desk
		user = frappe.get_doc("User", email)
		changed = False
		if user.user_type != "Website User":
			user.user_type = "Website User"
			changed = True
		# Desk User is injected for System Users; drop it for portal-only
		desk_rows = [r for r in user.roles if r.role == "Desk User"]
		for row in desk_rows:
			user.remove(row)
			changed = True
		if changed:
			user.flags.ignore_permissions = True
			user.save()
			fixed_users.append(email)

	frappe.db.commit()
	return {"roles_no_desk": fixed_roles, "users_website": fixed_users}


def _self_check() -> None:
	"""ponytail: role matrix for redirect helper — fails if portal routing breaks."""
	assert home_page_for_roles(["Guardian"]) == PORTAL_HOME
	assert home_page_for_roles(["Student"]) == PORTAL_HOME
	assert home_page_for_roles(["Guardian", "Student"]) == PORTAL_HOME
	assert home_page_for_roles(["Guardian", "All", "Guest", "Desk User"]) == PORTAL_HOME
	assert home_page_for_roles(["System Manager"]) is None
	assert home_page_for_roles(["Accounts User", "Education Manager"]) is None
	assert home_page_for_roles(["System Manager", "Guardian"]) == DESK_HOME
	assert home_page_for_roles(["Accounts User", "Student"]) == DESK_HOME
	assert home_page_for_roles([]) is None
	assert home_page_for_roles(None) is None


if __name__ == "__main__":
	_self_check()
	print("website_home ok")
