# Copyright (c) 2026, Malkiel Adje and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import cint


class MeCefSettings(Document):
	def validate(self):
		if self.company and frappe.db.exists(
			"MeCef Settings",
			{"company": self.company, "name": ["!=", self.name or ""]},
		):
			frappe.throw(
				frappe._("MeCef Settings existe déjà pour la société {0}.").format(
					self.company
				)
			)
		self._validate_unique_active_ifu()

	def _validate_unique_active_ifu(self):
		"""Un seul MeCef Settings actif par IFU (lookup FACNO / multi-société)."""
		ifu = (self.ifu or "").strip()
		if not ifu or not cint(self.is_active):
			return

		duplicates = frappe.get_all(
			"MeCef Settings",
			filters={
				"ifu": ifu,
				"is_active": 1,
				"name": ["!=", self.name or ""],
			},
			pluck="name",
			limit=1,
		)
		if duplicates:
			frappe.throw(
				frappe._(
					"Un MeCef Settings actif existe déjà pour l'IFU {0} ({1})."
				).format(ifu, duplicates[0])
			)
