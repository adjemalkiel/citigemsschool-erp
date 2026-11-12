/**
 * Edu-portal chrome: same red bar as /login (logo, FR/EN, Accueil, logout).
 * Mobile: menu toggle + overlay drawer; schedule time → FR-ish (8h00).
 * Loaded only from www/edu_portal.html — SPA shell has no Desk web_include_js.
 */
(function () {
	var SCHOOL_LOGO = "/assets/citigems_custom/images/citigems-logo.png";
	var SCHOOL_NAME = "Citigems Bilingual School";
	var MQ = "(max-width: 1023px)";
	var TIME_RE = /\b(\d{1,2}):(\d{2})(?::\d{2})?\b/g;

	function marketingUrl() {
		var meta = document.querySelector('meta[name="citigems-marketing-url"]');
		var url = (meta && meta.getAttribute("content")) || "";
		return url.replace(/\/$/, "") || "https://www.citigemsschool.com";
	}

	function guestLang() {
		if (window.citigemsLang === "fr" || window.citigemsLang === "en") {
			return window.citigemsLang;
		}
		var m = document.cookie.match(/(?:^|;\s*)preferred_language=([^;]*)/);
		var c = m ? decodeURIComponent(m[1]).toLowerCase() : "";
		if (c === "fr" || c === "en") return c;
		var html = (document.documentElement.getAttribute("lang") || "").toLowerCase();
		if (html.indexOf("en") === 0) return "en";
		return "fr";
	}

	function setGuestLang(code) {
		document.cookie =
			"preferred_language=" + code + ";path=/;max-age=31536000;SameSite=Lax";
		window.location.reload();
	}

	function isMobile() {
		return window.matchMedia(MQ).matches;
	}

	function setNavOpen(open) {
		if (!document.body) return;
		document.body.classList.toggle("citigems-portal-nav-open", !!open);
		var btn = document.getElementById("citigems-portal-menu");
		if (btn) btn.setAttribute("aria-expanded", open ? "true" : "false");
	}

	function closeNav() {
		setNavOpen(false);
	}

	function toggleNav() {
		if (!isMobile()) return;
		setNavOpen(!document.body.classList.contains("citigems-portal-nav-open"));
	}

	function ensureBackdrop() {
		var el = document.getElementById("citigems-portal-nav-backdrop");
		if (el) return el;
		el = document.createElement("button");
		el.type = "button";
		el.id = "citigems-portal-nav-backdrop";
		el.className = "citigems-portal-nav-backdrop";
		el.setAttribute("aria-label", "Close menu");
		el.addEventListener("click", closeNav);
		document.body.appendChild(el);
		return el;
	}

	function menuIconSvg() {
		return (
			'<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">' +
			'<path d="M4 7h16M4 12h16M4 17h16"/>' +
			"</svg>"
		);
	}

	function closeIconSvg() {
		return (
			'<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round">' +
			'<path d="M6 6l12 12M18 6L6 18"/>' +
			"</svg>"
		);
	}

	function logoutIconSvg() {
		return (
			'<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
			'<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>' +
			'<path d="M16 17l5-5-5-5"/>' +
			'<path d="M21 12H9"/>' +
			"</svg>"
		);
	}

	function doLogout(e) {
		if (e) e.preventDefault();
		var headers = { Accept: "application/json" };
		if (window.csrf_token && window.csrf_token !== "None") {
			headers["X-Frappe-CSRF-Token"] = window.csrf_token;
		}
		fetch("/api/method/logout", {
			method: "POST",
			credentials: "same-origin",
			headers: headers,
		}).finally(function () {
			window.location.href = "/login";
		});
	}

	/** Logo + red close — mirrors public-site offcanvas top bar */
	function ensureDrawerChrome() {
		var side = document.querySelector("#app .border-r.bg-gray-50");
		if (!side) return false;
		side.classList.add("citigems-portal-drawer");
		if (!side.querySelector(".citigems-portal-drawer__top")) {
			var top = document.createElement("div");
			top.className = "citigems-portal-drawer__top";
			top.innerHTML =
				'<a class="citigems-portal-drawer__logo" href="' +
				marketingUrl() +
				'" aria-label="' +
				SCHOOL_NAME +
				'">' +
				'<img src="' +
				SCHOOL_LOGO +
				'" alt="' +
				SCHOOL_NAME +
				'" /></a>' +
				'<button type="button" class="citigems-portal-drawer__close" aria-label="Close menu">' +
				closeIconSvg() +
				"</button>";
			side.insertBefore(top, side.firstChild);
			var closeBtn = top.querySelector(".citigems-portal-drawer__close");
			if (closeBtn) closeBtn.addEventListener("click", closeNav);
		}
		if (!side.querySelector(".citigems-portal-drawer__logout")) {
			var logoutLabel = guestLang() === "en" ? "Log out" : "Déconnexion";
			var foot = document.createElement("button");
			foot.type = "button";
			foot.className = "citigems-portal-drawer__logout";
			foot.setAttribute("aria-label", logoutLabel);
			foot.innerHTML = logoutIconSvg() + "<span>" + logoutLabel + "</span>";
			foot.addEventListener("click", doLogout);
			side.appendChild(foot);
		}
		return true;
	}

	function injectPortalBar() {
		if (!document.body) return;
		var lang = guestLang();
		var homeLabel = lang === "en" ? "Home" : "Accueil";
		var logoutLabel = lang === "en" ? "Log out" : "Déconnexion";
		var menuLabel = "Menu";
		var bar = document.getElementById("citigems-login-bar");
		if (!bar) {
			bar = document.createElement("header");
			bar.id = "citigems-login-bar";
			bar.className = "citigems-login-bar citigems-portal-bar";
			document.body.insertBefore(bar, document.body.firstChild);
		}
		bar.innerHTML =
			'<button type="button" class="citigems-portal-bar__menu" id="citigems-portal-menu" aria-label="' +
			menuLabel +
			'" aria-expanded="false" aria-controls="app">' +
			menuIconSvg() +
			"</button>" +
			'<a class="citigems-login-bar__plate" href="' +
			marketingUrl() +
			'" aria-label="' +
			SCHOOL_NAME +
			'">' +
			'<img src="' +
			SCHOOL_LOGO +
			'" alt="' +
			SCHOOL_NAME +
			'" /></a>' +
			'<span class="citigems-login-bar__name">' +
			SCHOOL_NAME +
			"</span>" +
			'<nav class="citigems-login-bar__langs" aria-label="Language">' +
			'<button type="button" class="citigems-login-bar__lang' +
			(lang === "fr" ? " is-active" : "") +
			'" data-lang="fr" aria-pressed="' +
			(lang === "fr" ? "true" : "false") +
			'">FR</button>' +
			'<span class="citigems-login-bar__lang-sep" aria-hidden="true">/</span>' +
			'<button type="button" class="citigems-login-bar__lang' +
			(lang === "en" ? " is-active" : "") +
			'" data-lang="en" aria-pressed="' +
			(lang === "en" ? "true" : "false") +
			'">EN</button>' +
			"</nav>" +
			'<a class="citigems-login-bar__accueil" href="' +
			marketingUrl() +
			'">' +
			homeLabel +
			"</a>" +
			'<a class="citigems-portal-bar__logout" href="/login" id="citigems-portal-logout" aria-label="' +
			logoutLabel +
			'" title="' +
			logoutLabel +
			'">' +
			logoutIconSvg() +
			"</a>";

		ensureBackdrop();
		var menuBtn = document.getElementById("citigems-portal-menu");
		if (menuBtn) menuBtn.addEventListener("click", toggleNav);

		bar.querySelectorAll(".citigems-login-bar__lang").forEach(function (btn) {
			btn.addEventListener("click", function () {
				var next = btn.getAttribute("data-lang");
				if (next && next !== lang) setGuestLang(next);
			});
		});
		var logoutLink = document.getElementById("citigems-portal-logout");
		if (logoutLink) logoutLink.addEventListener("click", doLogout);
	}

	function bindSidebarClose() {
		var app = document.getElementById("app");
		if (!app || app.dataset.citigemsNavBound) return;
		app.dataset.citigemsNavBound = "1";
		app.addEventListener(
			"click",
			function (e) {
				if (!isMobile() || !document.body.classList.contains("citigems-portal-nav-open")) {
					return;
				}
				var a = e.target && e.target.closest ? e.target.closest("a") : null;
				if (!a) return;
				var side = a.closest(".border-r.bg-gray-50");
				if (side) closeNav();
			},
			true
		);
	}

	function fmtFrTimeChunk(match, h, m) {
		return parseInt(h, 10) + "h" + m;
	}

	function formatTimesIn(root) {
		if (!root) return;
		var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
		var node;
		var nodes = [];
		while ((node = walker.nextNode())) {
			if (TIME_RE.test(node.nodeValue || "")) nodes.push(node);
			TIME_RE.lastIndex = 0;
		}
		nodes.forEach(function (n) {
			var next = (n.nodeValue || "").replace(TIME_RE, fmtFrTimeChunk);
			if (next !== n.nodeValue) n.nodeValue = next;
		});
	}

	function watchScheduleTimes() {
		var app = document.getElementById("app");
		if (!app || app.dataset.citigemsTimeWatch) return;
		app.dataset.citigemsTimeWatch = "1";
		formatTimesIn(app);
		var t = null;
		var mo = new MutationObserver(function () {
			if (t) clearTimeout(t);
			t = setTimeout(function () {
				formatTimesIn(app);
			}, 80);
		});
		mo.observe(app, { childList: true, subtree: true, characterData: true });
	}

	function onViewportChange() {
		if (!isMobile()) closeNav();
	}

	function run() {
		document.documentElement.setAttribute("lang", guestLang());
		injectPortalBar();
		ensureBackdrop();
		ensureDrawerChrome();
		bindSidebarClose();
		watchScheduleTimes();
		closeNav();
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", run);
	} else {
		run();
	}
	window.addEventListener("resize", onViewportChange);
	document.addEventListener("keydown", function (e) {
		if (e.key === "Escape") closeNav();
	});
	// SPA mounts async — re-bind once #app fills
	var boot = 0;
	var bootTimer = setInterval(function () {
		boot += 1;
		ensureDrawerChrome();
		bindSidebarClose();
		watchScheduleTimes();
		if (document.querySelector("#app .border-r.bg-gray-50") || boot > 40) {
			clearInterval(bootTimer);
		}
	}, 250);

	/* Thermal MECeF receipt: no letterhead + portal FR/EN language. */
	var _open = window.open;
	window.open = function (url, target, features) {
		if (typeof url === "string" && url.indexOf("download_pdf") !== -1) {
			var join = url.indexOf("?") >= 0 ? "&" : "?";
			if (url.indexOf("no_letterhead=") === -1) {
				url += join + "no_letterhead=1";
				join = "&";
			}
			if (url.indexOf("language=") === -1) {
				url += join + "language=" + encodeURIComponent(guestLang());
			}
		}
		return _open.call(window, url, target, features);
	};

	/* SPA prints Student fields raw (EN). Map known values when UI is FR. */
	var FIELD_FR = {
		Beninese: "Béninoise",
		Female: "Femelle",
		Male: "Mâle",
	};
	function localizeFieldValues(root) {
		if (!root || !root.querySelectorAll || guestLang() !== "fr") return;
		root.querySelectorAll("p").forEach(function (el) {
			if (el.childElementCount) return;
			var t = (el.textContent || "").trim();
			if (FIELD_FR[t]) el.textContent = FIELD_FR[t];
		});
	}

	/* Fees list: mark Download Invoice so CSS can paint it Paid-green. */
	function paintFeeCtas(root) {
		if (!root || !root.querySelectorAll) return;
		root.querySelectorAll('button[class*="hover:bg-gray-900"]').forEach(function (btn) {
			var t = (btn.textContent || "").toLowerCase();
			if (
				t.indexOf("download") >= 0 ||
				t.indexOf("télécharger") >= 0 ||
				t.indexOf("telecharger") >= 0
			) {
				btn.classList.add("citigems-fee-download");
			}
		});
	}
	function paintPortal(root) {
		paintFeeCtas(root);
		localizeFieldValues(root);
	}
	function watchPortalDom() {
		var app = document.getElementById("app");
		if (app) paintPortal(app);
		var portals = document.getElementById("headlessui-portal-root");
		if (portals) paintPortal(portals);
		if (!window.MutationObserver) return;
		var mo = new MutationObserver(function (muts) {
			muts.forEach(function (m) {
				if (m.target && m.target.querySelectorAll) paintPortal(m.target);
			});
			if (app) paintFeeCtas(app);
			var pr = document.getElementById("headlessui-portal-root");
			if (pr) localizeFieldValues(pr);
		});
		if (app) mo.observe(app, { childList: true, subtree: true });
		if (document.body) {
			mo.observe(document.body, { childList: true, subtree: false });
		}
		/* Dialogs mount under body → watch for portal root creation */
		var boot = 0;
		var t = setInterval(function () {
			boot += 1;
			var pr = document.getElementById("headlessui-portal-root");
			if (pr) {
				paintPortal(pr);
				mo.observe(pr, { childList: true, subtree: true });
				clearInterval(t);
			} else if (boot > 40) clearInterval(t);
		}, 250);
	}
	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", watchPortalDom);
	} else {
		watchPortalDom();
	}
})();
