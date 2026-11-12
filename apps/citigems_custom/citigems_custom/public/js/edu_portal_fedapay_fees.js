/**
 * Overlay for Education SPA Fees « Pay Now » — Mobile Money (FedaPay) instead of Razorpay.
 * Loaded from edu_portal.html; hooks ListView pay buttons after Vue mounts.
 */
(function () {
	function ready(fn) {
		if (document.readyState !== "loading") fn();
		else document.addEventListener("DOMContentLoaded", fn);
	}

	function api(method, args) {
		return fetch("/api/method/" + method, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				"X-Frappe-CSRF-Token": window.csrf_token,
			},
			body: JSON.stringify(args || {}),
			credentials: "same-origin",
		}).then(function (r) {
			return r.json();
		});
	}

	function ensureModal() {
		var el = document.getElementById("cg-fedapay-modal");
		if (el) return el;
		el = document.createElement("div");
		el.id = "cg-fedapay-modal";
		el.hidden = true;
		el.innerHTML =
			'<div class="cg-fp-backdrop"></div>' +
			'<div class="cg-fp-card" role="dialog" aria-modal="true">' +
			"<h2>Payer — Mobile Money</h2>" +
			'<p class="cg-fp-label" id="cg-fp-invoice"></p>' +
			'<label>Opérateur<select id="cg-fp-op"><option>MTN</option><option>MOOV</option><option>CELTIIS</option></select></label>' +
			'<label>Téléphone<input id="cg-fp-phone" type="tel" placeholder="0197123456" /></label>' +
			'<div class="cg-fp-actions">' +
			'<button type="button" id="cg-fp-cancel">Annuler</button>' +
			'<button type="button" id="cg-fp-pay">Payer</button></div>' +
			'<p class="cg-fp-status" id="cg-fp-status"></p></div>';
		document.body.appendChild(el);
		el.querySelector(".cg-fp-backdrop").addEventListener("click", close);
		el.querySelector("#cg-fp-cancel").addEventListener("click", close);
		el.querySelector("#cg-fp-pay").addEventListener("click", pay);
		return el;
	}

	var currentInvoice = null;

	function open(invoice, amountLabel) {
		ensureModal();
		currentInvoice = invoice;
		document.getElementById("cg-fp-invoice").textContent =
			invoice + (amountLabel ? " — " + amountLabel : "");
		document.getElementById("cg-fp-status").textContent = "";
		document.getElementById("cg-fedapay-modal").hidden = false;
	}

	function close() {
		var el = document.getElementById("cg-fedapay-modal");
		if (el) el.hidden = true;
		currentInvoice = null;
	}

	function pay() {
		if (!currentInvoice) return;
		var btn = document.getElementById("cg-fp-pay");
		var status = document.getElementById("cg-fp-status");
		btn.disabled = true;
		status.textContent = "…";
		api("citigems_custom.api.fedapay.create_fee_payment", {
			sales_invoice: currentInvoice,
			operator: document.getElementById("cg-fp-op").value,
			phone_number: document.getElementById("cg-fp-phone").value,
		})
			.then(function (res) {
				if (res.exc || (res._server_messages && !res.message)) {
					throw new Error(String(res._server_messages || res.exc || "Erreur"));
				}
				var msg = res.message || {};
				status.textContent = msg.message || "OK";
				var paymentName = msg.payment_name;
				if (!paymentName) return;
				var tries = 0;
				var timer = setInterval(function () {
					tries += 1;
					api("citigems_custom.api.fedapay.get_payment_status", {
						payment_name: paymentName,
					}).then(function (st) {
						var s = (st.message || {}).status;
						if (s === "Approved") {
							clearInterval(timer);
							status.textContent = "Payé";
							setTimeout(function () {
								close();
								window.location.reload();
							}, 800);
						} else if (s && s !== "Pending") {
							clearInterval(timer);
							status.textContent = s;
						}
					});
					if (tries > 40) clearInterval(timer);
				}, 3000);
			})
			.catch(function (err) {
				status.textContent = err.message || "Error";
			})
			.finally(function () {
				btn.disabled = false;
			});
	}

	// Intercept Education SPA « Pay Now » clicks; invoice is on the row.
	ready(function () {
		ensureModal();
		document.body.addEventListener(
			"click",
			function (e) {
				var btn = e.target.closest("button");
				if (!btn) return;
				var label = (btn.textContent || "").trim();
				if (label !== "Pay Now" && label !== "Payer") return;
				// Try to find invoice name from nearby row text (ACC-SINV-…)
				var row = btn.closest("[class*='row'], tr, li, div");
				var text = (row && row.textContent) || "";
				var m = text.match(/ACC-SINV-\d{4}-\d+/);
				if (!m) return;
				e.preventDefault();
				e.stopPropagation();
				open(m[0], "");
			},
			true
		);
	});
})();
