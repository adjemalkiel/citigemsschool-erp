/**
 * Soft rebrand: replace leftover ERPNext / Frappe labels with DevOps on Desk.
 * App product title remains Citigems School via branding.boot_session.
 */
(function () {
	function replaceText(node) {
		if (!node || node.nodeType !== Node.TEXT_NODE) return;
		var t = node.nodeValue;
		if (!t) return;
		var n = t
			.replace(/\bERPNext\b/g, "DevOps")
			.replace(/\bFrappe Framework\b/g, "DevOps")
			.replace(/\bFrappe\b/g, "DevOps");
		if (n !== t) node.nodeValue = n;
	}
	function walk(root) {
		if (!root) return;
		var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
		var n;
		while ((n = walker.nextNode())) replaceText(n);
	}
	function injectPoweredBy() {
		if (document.getElementById("citigems-powered-by")) return;
		var foot = document.querySelector(".footer-message, .login-footer, footer");
		var el = document.createElement("div");
		el.id = "citigems-powered-by";
		el.className = "citigems-powered-by";
		el.innerHTML = 'Powered by <a href="https://devopsflows.com" target="_blank" rel="noopener">DevOps</a>';
		if (foot) foot.appendChild(el);
		else if (document.body) document.body.appendChild(el);
	}
	document.addEventListener("DOMContentLoaded", function () {
		walk(document.body);
		injectPoweredBy();
	});
	if (window.frappe && frappe.router) {
		frappe.router.on("change", function () {
			setTimeout(function () {
				walk(document.body);
			}, 200);
		});
	}
})();
