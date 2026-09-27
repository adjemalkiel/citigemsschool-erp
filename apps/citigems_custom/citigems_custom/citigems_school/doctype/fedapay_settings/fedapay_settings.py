# Copyright (c) 2026, Malkiel Adje and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class FedaPaySettings(Document):
	def validate(self):
		self.webhook_url_help = (
			frappe.utils.get_url()
			+ "/api/method/citigems_custom.api.fedapay.webhook"
		)
		if self.company and frappe.db.exists(
			"FedaPay Settings",
			{"company": self.company, "name": ["!=", self.name or ""]},
		):
			frappe.throw(
				frappe._("FedaPay Settings existe déjà pour la société {0}.").format(
					self.company
				)
			)
