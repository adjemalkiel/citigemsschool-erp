"""Seed Rooms (salles) for Course Schedule — guide 5.1.

Timetable (class timetable 2026.docx) has no room labels; Citigems uses
homeroom classes → one Room per Student Group + shared spaces.

  bench --site <site> execute citigems_custom.scripts.seed_rooms.seed
"""

from __future__ import annotations

import frappe

# (room_name, room_number, seating_capacity)
ROOMS: list[tuple[str, str, str]] = [
	# Homerooms ↔ Student Groups 2026
	("Nursery 1", "N1", "25"),
	("Nursery 2", "N2", "25"),
	("Basic 1 / CI", "B1", "35"),
	("Basic 2 / CP", "B2", "35"),
	("Basic 3 / CE1", "B3", "35"),
	("Basic 4 / CE2", "B4", "35"),
	("Basic 5 / CM1", "B5", "35"),
	("Basic 6 / CM2", "B6", "35"),
	# Shared (timetable: EPS, club, assembly, outdoor)
	("Cour / EPS", "EPS", "60"),
	("Salle polyvalente / Club", "CLUB", "40"),
	("Assemblée / Assembly", "ASM", "120"),
]


def _ensure_room(room_name: str, room_number: str, seating_capacity: str) -> tuple[str, bool]:
	existing = frappe.db.get_value("Room", {"room_name": room_name}, "name")
	if existing:
		doc = frappe.get_doc("Room", existing)
		changed = False
		if room_number and doc.room_number != room_number:
			doc.room_number = room_number
			changed = True
		if seating_capacity and doc.seating_capacity != seating_capacity:
			doc.seating_capacity = seating_capacity
			changed = True
		if changed:
			doc.save(ignore_permissions=True)
		return doc.name, False

	doc = frappe.get_doc(
		{
			"doctype": "Room",
			"room_name": room_name,
			"room_number": room_number,
			"seating_capacity": seating_capacity,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name, True


def seed():
	"""Create school rooms for timetable scheduling."""
	frappe.flags.ignore_permissions = True
	created, updated = [], []
	for room_name, number, capacity in ROOMS:
		name, is_new = _ensure_room(room_name, number, capacity)
		(created if is_new else updated).append(name)
	frappe.db.commit()
	return {
		"created": len(created),
		"updated": len(updated),
		"total": frappe.db.count("Room"),
		"rooms": [
			{"name": n, "room_name": frappe.db.get_value("Room", n, "room_name")}
			for n in created + updated
		],
	}
