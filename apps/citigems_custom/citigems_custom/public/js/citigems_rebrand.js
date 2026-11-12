/**
 * Soft rebrand: replace leftover ERPNext / Frappe labels with DevOps on Desk.
 * Login chrome matches the public Citigems site (red bar + Accueil).
 */
(function () {
	var SCHOOL_LOGO = "/assets/citigems_custom/images/citigems-logo.png";
	var SCHOOL_NAME = "Citigems Bilingual School";

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

	function marketingUrl() {
		var meta = document.querySelector('meta[name="citigems-marketing-url"]');
		var url = (meta && meta.getAttribute("content")) || "";
		return url.replace(/\/$/, "") || "https://www.citigemsschool.com";
	}

	function isLoginPage() {
		if (!document.body) return false;
		if (document.body.classList.contains("for-login")) return true;
		if (document.querySelector("section.for-login, .login-content")) return true;
		var path = (window.location && window.location.pathname) || "";
		return path === "/login" || path.indexOf("/login") === 0;
	}

	function injectPoweredBy() {
		var el = document.getElementById("citigems-powered-by");
		var powered =
			guestLang() === "en"
				? 'Powered by <a href="https://devopserp.africa" target="_blank" rel="noopener">DevOps</a>'
				: 'Propulsé par <a href="https://devopserp.africa" target="_blank" rel="noopener">DevOps</a>';
		if (!el) {
			el = document.createElement("div");
			el.id = "citigems-powered-by";
			el.className = "citigems-powered-by";
		}
		el.innerHTML = powered;
		var loginFoot = document.querySelector(
			".for-login .login-footer, .for-login .footer-message, .login-content .login-footer"
		);
		var card = document.querySelector(
			"section.for-login .login-content, .login-content.page-card"
		);
		if (loginFoot) {
			el.style.cssText = "";
			if (el.parentNode !== loginFoot) loginFoot.appendChild(el);
		} else if (isLoginPage() && card) {
			el.style.cssText = "";
			if (el.parentNode !== card) card.appendChild(el);
		} else if (document.body) {
			el.style.cssText =
				"position:fixed;top:auto;left:0;right:0;bottom:0;width:100%;" +
				"z-index:100;margin:0;padding:6px 12px;text-align:center;" +
				"font-size:12px;line-height:1.3;opacity:0.75;pointer-events:none;" +
				"box-sizing:border-box;background:transparent;";
			if (el.parentNode !== document.body) document.body.appendChild(el);
		}
	}

	function injectFonts() {
		if (document.getElementById("citigems-fonts")) return;
		var link = document.createElement("link");
		link.id = "citigems-fonts";
		link.rel = "stylesheet";
		link.href =
			"https://fonts.googleapis.com/css2?family=Baloo+2:wght@500;600;700;800&family=Quicksand:wght@400;500;600;700&display=swap";
		document.head.appendChild(link);
	}

	function guestLang() {
		var m = document.cookie.match(/(?:^|;\s*)preferred_language=([^;]*)/);
		var c = m ? decodeURIComponent(m[1]).toLowerCase() : "";
		if (c === "fr" || c === "en") return c;
		var html = (document.documentElement.getAttribute("lang") || "").toLowerCase();
		if (html.indexOf("fr") === 0) return "fr";
		if (html.indexOf("en") === 0) return "en";
		return "fr";
	}

	function setGuestLang(code) {
		document.cookie =
			"preferred_language=" +
			code +
			";path=/;max-age=31536000;SameSite=Lax";
		window.location.reload();
	}

	function injectLoginBar() {
		if (!isLoginPage() || !document.body) return;
		injectFonts();
		var lang = guestLang();
		var homeLabel = lang === "en" ? "Home" : "Accueil";
		var bar = document.getElementById("citigems-login-bar");
		if (!bar) {
			bar = document.createElement("header");
			bar.id = "citigems-login-bar";
			bar.className = "citigems-login-bar";
			document.body.insertBefore(bar, document.body.firstChild);
		}
		bar.innerHTML =
			'<a class="citigems-login-bar__plate" href="' +
			marketingUrl() +
			'" aria-label="' +
			SCHOOL_NAME +
			'">' +
			'<img src="' +
			SCHOOL_LOGO +
			'" alt="' +
			SCHOOL_NAME +
			'" />' +
			"</a>" +
			'<span class="citigems-login-bar__name">' +
			SCHOOL_NAME +
			"</span>" +
			'<nav class="citigems-login-bar__langs" aria-label="Language">' +
			'<button type="button" class="citigems-login-bar__lang' +
			(lang === "fr" ? " is-active" : "") +
			'" data-lang="fr">FR</button>' +
			'<span class="citigems-login-bar__lang-sep" aria-hidden="true">/</span>' +
			'<button type="button" class="citigems-login-bar__lang' +
			(lang === "en" ? " is-active" : "") +
			'" data-lang="en">EN</button>' +
			"</nav>" +
			'<a class="citigems-login-bar__accueil" href="' +
			marketingUrl() +
			'">' +
			homeLabel +
			"</a>";
		bar.querySelectorAll(".citigems-login-bar__lang").forEach(function (btn) {
			btn.addEventListener("click", function () {
				var next = btn.getAttribute("data-lang");
				if (next && next !== lang) setGuestLang(next);
			});
		});
		var dock = document.getElementById("devops-desk-theme-dock");
		if (dock) dock.style.display = "none";
	}

	function clearDeskLastVisited() {
		// Stock login "No App" prefers localStorage.last_visited over home_page.
		// Stale /desk|/app from a prior System User session → Not Permitted.
		if (!isLoginPage()) return;
		try {
			var lv = localStorage.getItem("last_visited") || "";
			if (/^\/?(desk|app)(\/|$)/i.test(lv)) {
				localStorage.removeItem("last_visited");
			}
		} catch (e) {}
	}

	function run() {
		clearDeskLastVisited();
		walk(document.body);
		injectLoginBar();
		injectPoweredBy();
	}

	document.addEventListener("DOMContentLoaded", run);
	if (document.readyState !== "loading") run();

	if (window.frappe && frappe.router) {
		frappe.router.on("change", function () {
			setTimeout(run, 200);
		});
	}
	window.addEventListener("hashchange", function () {
		setTimeout(run, 50);
	});
})();
