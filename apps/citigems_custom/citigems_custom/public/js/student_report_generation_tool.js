/**
 * Student Report Generation Tool — Citigems bulletin print.
 *
 * Education's refresh also sets "Print Report Card" via open_url_post; that POST
 * often arrives without ``doc`` on Frappe v16. We re-bind after Education and
 * send a JSON body (make_form_dict parses it reliably).
 */
frappe.ui.form.on("Student Report Generation Tool", {
	refresh: function (frm) {
		frm.disable_save();
		frm.page.clear_indicator();
		bind_citigems_print(frm);
		// Win the primary-action race against education's own refresh handler
		setTimeout(function () {
			bind_citigems_print(frm);
		}, 200);
	},
});

function bind_citigems_print(frm) {
	frm.page.set_primary_action(__("Print Report Card"), () => print_citigems_bulletin(frm));
}

function print_citigems_bulletin(frm) {
	const d = frm.doc;
	if (!d.student || !d.program || !d.academic_year) {
		frappe.throw(__("Please fill in all the mandatory fields."));
	}
	// Default group from program when the Link is empty (common on Single form)
	let assessment_group = d.assessment_group;
	if (!assessment_group) {
		const prog = (d.program || "").toLowerCase();
		assessment_group =
			prog.indexOf("nursery") >= 0 || prog.indexOf("maternelle") >= 0
				? "Nursery"
				: "Continuous Assessment";
	}
	const payload = {
		doctype: d.doctype,
		student: d.student,
		student_name: d.student_name,
		program: d.program,
		student_batch: d.student_batch,
		academic_year: d.academic_year,
		academic_term: d.academic_term,
		assessment_group: assessment_group,
		letter_head: d.letter_head,
		add_letterhead: d.add_letterhead,
		show_marks: d.show_marks,
		terms: d.terms,
		assessment_criteria: d.assessment_criteria,
		parents_meeting: d.parents_meeting,
	};

	frappe.dom.freeze(__("Generating Report Card..."));
	fetch("/api/method/citigems_custom.education_report.preview_report_card", {
		method: "POST",
		credentials: "same-origin",
		headers: {
			"Content-Type": "application/json",
			Accept: "application/pdf, application/json",
			"X-Frappe-CSRF-Token": frappe.csrf_token,
		},
		body: JSON.stringify({ doc: payload }),
	})
		.then(async (res) => {
			const ct = (res.headers.get("Content-Type") || "").toLowerCase();
			if (!res.ok || ct.indexOf("pdf") === -1) {
				let msg = __("Print failed");
				try {
					const data = await res.json();
					if (data._server_messages) {
						const raw = JSON.parse(data._server_messages);
						const first = typeof raw[0] === "string" ? JSON.parse(raw[0]) : raw[0];
						msg = (first && first.message) || msg;
					} else if (data.message) {
						msg = data.message;
					} else if (data.exc) {
						msg = String(data.exc).split("\n")[0];
					}
				} catch (e) {
					/* keep default */
				}
				throw new Error(msg);
			}
			return res.blob();
		})
		.then((blob) => {
			const url = URL.createObjectURL(blob);
			window.open(url, "_blank");
			setTimeout(function () {
				URL.revokeObjectURL(url);
			}, 60_000);
		})
		.catch((err) => {
			frappe.msgprint({
				title: __("Report Card"),
				indicator: "red",
				message: err.message || String(err),
			});
		})
		.finally(() => {
			frappe.dom.unfreeze();
		});
}
