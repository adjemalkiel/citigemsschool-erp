// Applique automatiquement le modèle de taxe MECeF (groupe B, TVA 18%)
// lorsque la case « Demande Facture Normalisée » est cochée, et le retire
// lorsqu'elle est décochée.
frappe.ui.form.on("Sales Invoice", {
	demande_facture_normalisee(frm) {
		frappe.db
			.get_value(
				"Sales Taxes and Charges Template",
				{ company: frm.doc.company, mecef_tax_group: "B" },
				"name"
			)
			.then((r) => {
				const template = r && r.message && r.message.name;
				if (!template) {
					return;
				}
				if (frm.doc.demande_facture_normalisee) {
					if (frm.doc.taxes_and_charges !== template) {
						frm.set_value("taxes_and_charges", template);
					}
				} else if (frm.doc.taxes_and_charges === template) {
					frm.set_value("taxes_and_charges", "");
				}
			});
	},

	refresh(frm) {
		toggleMobileMoneyFields(frm);
	},
});

frappe.ui.form.on("Sales Invoice Payment", {
	amount(frm) {
		toggleMobileMoneyFields(frm);
	},
	mode_of_payment(frm) {
		toggleMobileMoneyFields(frm);
	},
});

function hasMobileMoneyPayment(frm) {
	return (frm.doc.payments || []).some(
		(row) => row.mode_of_payment === "Mobile Money" && flt(row.amount) > 0
	);
}

function toggleMobileMoneyFields(frm) {
	const show = hasMobileMoneyPayment(frm);
	const fields = ["mobile_money_operator", "mobile_money_phone"];

	fields.forEach((fieldname) => {
		frm.toggle_display(fieldname, show);
		if (frm.fields_dict[fieldname]) {
			frm.fields_dict[fieldname].df.reqd = show && frm.doc.docstatus === 0;
			frm.refresh_field(fieldname);
		}
	});

	if (!show && frm.doc.docstatus === 0) {
		if (frm.doc.mobile_money_operator) {
			frm.set_value("mobile_money_operator", "");
		}
		if (frm.doc.mobile_money_phone) {
			frm.set_value("mobile_money_phone", "");
		}
	}
}
