/**
 * Desk UI theme loader + appearance dock (Desk + login).
 * Desk UI: saas_theme | frappe_desk_theme | frappe (per-user profile).
 * Appearance: light | dark | automatic (per-user via User.desk_theme + localStorage).
 */
(function () {
	var THEME_SAAS = "saas_theme";
	var THEME_DESK = "frappe_desk_theme";
	var THEME_FRAPPE = "frappe";
	var STORAGE_KEY = "citigems_theme_mode";

	var ASSETS = {};
	ASSETS[THEME_SAAS] = {
		css: "/assets/saas_theme/css/saas_theme.css",
		js: "/assets/saas_theme/js/saas_theme.js",
	};
	ASSETS[THEME_DESK] = {
		css: "/assets/frappe_desk_theme/css/frappe_desk_theme.css",
		js: "/assets/frappe_desk_theme/js/frappe_desk_theme.js",
	};

	var LABELS = {};
	LABELS[THEME_SAAS] = "SaaS";
	LABELS[THEME_DESK] = "Desk";
	LABELS[THEME_FRAPPE] = "Frappe";

	var FULL_LABELS = {};
	FULL_LABELS[THEME_SAAS] = "SaaS Theme";
	FULL_LABELS[THEME_DESK] = "Frappe Desk Theme";
	FULL_LABELS[THEME_FRAPPE] = "Default Frappe";

	var APPEARANCE = [
		{ value: "light", label: "Light", title: "Light mode" },
		{ value: "dark", label: "Dark", title: "Dark mode" },
		{ value: "automatic", label: "Auto", title: "Match system" },
	];

	function t(msg) {
		if (typeof window.__ === "function") {
			try {
				return window.__(msg);
			} catch (e) {
				/* ignore */
			}
		}
		if (window.frappe && typeof frappe._ === "function") {
			try {
				return frappe._(msg);
			} catch (e) {
				/* ignore */
			}
		}
		return msg;
	}

	function uiLang() {
		try {
			if (window.frappe && frappe.boot && frappe.boot.lang) return frappe.boot.lang;
		} catch (e) {
			/* ignore */
		}
		return (document.documentElement.lang || "en").split("-")[0];
	}

	function normalize(theme) {
		if (theme === "none" || theme === "default" || theme === "stock") return THEME_FRAPPE;
		if (theme === THEME_SAAS || theme === THEME_DESK || theme === THEME_FRAPPE) return theme;
		return THEME_SAAS;
	}

	function isDesk() {
		return !!(window.frappe && frappe.boot && frappe.boot.sitename);
	}

	function isLoggedInDeskUser() {
		return !!(
			isDesk() &&
			window.frappe &&
			frappe.session &&
			frappe.session.user &&
			frappe.session.user !== "Guest"
		);
	}

	function bootTheme() {
		try {
			if (window.frappe && frappe.boot && frappe.boot.desk_ui_theme) {
				return normalize(frappe.boot.desk_ui_theme);
			}
		} catch (e) {
			/* ignore */
		}
		return THEME_SAAS;
	}

	function removeInjected() {
		document.querySelectorAll("[data-desk-ui-theme]").forEach(function (el) {
			el.remove();
		});
	}

	function inject(theme) {
		if (!isDesk()) return;
		theme = normalize(theme);
		var spec = ASSETS[theme];
		removeInjected();
		if (!spec) return;
		if (spec.css) {
			var link = document.createElement("link");
			link.rel = "stylesheet";
			link.href = spec.css;
			link.setAttribute("data-desk-ui-theme", theme);
			document.head.appendChild(link);
		}
		if (spec.js) {
			var script = document.createElement("script");
			script.src = spec.js;
			script.async = false;
			script.setAttribute("data-desk-ui-theme", theme);
			document.head.appendChild(script);
		}
	}

	function themeOptions() {
		if (window.frappe && frappe.boot && Array.isArray(frappe.boot.desk_ui_themes)) {
			return frappe.boot.desk_ui_themes.map(function (opt) {
				return {
					value: opt.value,
					label: LABELS[opt.value] || opt.label || opt.value,
					title: FULL_LABELS[opt.value] || opt.label || opt.value,
				};
			});
		}
		return [
			{ value: THEME_SAAS, label: LABELS[THEME_SAAS], title: FULL_LABELS[THEME_SAAS] },
			{ value: THEME_DESK, label: LABELS[THEME_DESK], title: FULL_LABELS[THEME_DESK] },
			{ value: THEME_FRAPPE, label: LABELS[THEME_FRAPPE], title: FULL_LABELS[THEME_FRAPPE] },
		];
	}

	function applyDeskTheme(theme) {
		if (!window.frappe || !frappe.call) return;
		frappe.call({
			method: "citigems_custom.desk_theme.set_desk_ui_theme",
			args: { theme: theme },
			freeze: true,
			freeze_message: t("Switching theme…"),
			callback: function (r) {
				if (r.message && r.message.message) {
					frappe.show_alert({ message: r.message.message, indicator: "green" });
				}
				setTimeout(function () {
					window.location.reload();
				}, 400);
			},
		});
	}

	function getAppearance() {
		var mode = document.documentElement.getAttribute("data-theme-mode");
		if (mode === "light" || mode === "dark" || mode === "automatic") return mode;
		try {
			var stored = localStorage.getItem(STORAGE_KEY);
			if (stored === "light" || stored === "dark" || stored === "automatic") return stored;
		} catch (e) {
			/* ignore */
		}
		return "light";
	}

	function resolveAppearance(mode) {
		if (mode === "automatic") {
			return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
		}
		return mode === "dark" ? "dark" : "light";
	}

	function applyAppearance(mode, persistUser) {
		if (mode !== "light" && mode !== "dark" && mode !== "automatic") mode = "light";
		document.documentElement.setAttribute("data-theme-mode", mode);
		document.documentElement.setAttribute("data-theme", resolveAppearance(mode));
		try {
			localStorage.setItem(STORAGE_KEY, mode);
		} catch (e) {
			/* ignore */
		}
		if (window.frappe && frappe.ui && typeof frappe.ui.set_theme === "function") {
			frappe.ui.set_theme(mode === "automatic" ? null : mode);
		}
		if (
			persistUser !== false &&
			window.frappe &&
			frappe.call &&
			frappe.session &&
			frappe.session.user &&
			frappe.session.user !== "Guest"
		) {
			frappe.call({
				method: "citigems_custom.desk_theme.set_appearance",
				args: { mode: mode },
				async: true,
				error: function () {
					/* local theme already applied; ignore stale-worker / offline save errors */
				},
			});
		}
		syncDockState();
	}

	function initAppearance() {
		var existing = document.documentElement.getAttribute("data-theme-mode");
		if (existing === "light" || existing === "dark" || existing === "automatic") {
			try {
				localStorage.setItem(STORAGE_KEY, existing);
			} catch (e) {
				/* ignore */
			}
			document.documentElement.setAttribute("data-theme", resolveAppearance(existing));
			return;
		}
		applyAppearance(getAppearance(), false);
	}

	function removeLegacyTablerDocks() {
		[
			"devops-web-controls-dock",
			"devops-web-controls",
			"devops-web-controls-pin",
			"devops-desk-controls-dock",
			"devops-desk-controls-style",
			"devops-ui-toggle-zone",
			"devops-ui-toggle-styles",
			"devops-appearance-styles",
			"devops-appearance-nav-btn",
		].forEach(function (id) {
			var el = document.getElementById(id);
			if (el) el.remove();
		});
		["devops-web-ui-toggle", "devops-web-theme-toggle", "devops-desk-ui-toggle", "devops-desk-theme-toggle"].forEach(
			function (id) {
				var el = document.getElementById(id);
				if (el) el.remove();
			}
		);
	}

	function ensureDockStyles() {
		if (document.getElementById("devops-desk-theme-dock-style")) return;
		var style = document.createElement("style");
		style.id = "devops-desk-theme-dock-style";
		style.textContent =
			"#devops-desk-theme-dock{position:fixed!important;left:16px!important;bottom:16px!important;z-index:2147483000!important;font-family:inherit;pointer-events:none}" +
			"#devops-desk-theme-dock *{box-sizing:border-box}" +
			"#devops-desk-theme-dock .devops-theme-fab{pointer-events:auto;display:inline-flex;align-items:center;gap:8px;margin:0;padding:10px 14px;border-radius:999px;border:1px solid var(--border-color,rgba(15,23,42,.12));background:var(--fg-color,var(--card-bg,#fff));color:var(--text-color,#0f172a);box-shadow:0 8px 24px rgba(15,23,42,.12);font-size:13px;font-weight:600;line-height:1;cursor:pointer}" +
			"#devops-desk-theme-dock .devops-theme-fab svg{width:16px;height:16px;flex:none}" +
			"#devops-desk-theme-dock .devops-theme-panel{pointer-events:auto;display:none;position:absolute;left:0;bottom:calc(100% + 10px);width:min(280px,calc(100vw - 32px));padding:12px;border-radius:14px;border:1px solid var(--border-color,rgba(15,23,42,.12));background:var(--fg-color,var(--card-bg,#fff));color:var(--text-color,#0f172a);box-shadow:0 16px 40px rgba(15,23,42,.16)}" +
			"#devops-desk-theme-dock.is-open .devops-theme-panel{display:block}" +
			"#devops-desk-theme-dock .devops-theme-section{margin:0 0 12px}" +
			"#devops-desk-theme-dock .devops-theme-section:last-child{margin-bottom:0}" +
			"#devops-desk-theme-dock .devops-theme-label{display:block;margin:0 0 8px;font-size:11px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;color:var(--text-muted,#64748b)}" +
			"#devops-desk-theme-dock .devops-theme-row{display:flex;flex-wrap:wrap;gap:6px}" +
			"#devops-desk-theme-dock .devops-desk-theme-btn{flex:1 1 0;min-width:72px;margin:0;padding:8px 10px;border-radius:10px;border:1px solid var(--border-color,rgba(15,23,42,.12));background:transparent;color:inherit;font-size:12px;font-weight:600;line-height:1.2;cursor:pointer}" +
			"#devops-desk-theme-dock .devops-desk-theme-btn:hover{background:var(--subtle-fg,rgba(15,23,42,.04))}" +
			"#devops-desk-theme-dock .devops-desk-theme-btn.is-active{background:var(--primary,#2563eb);border-color:var(--primary,#2563eb);color:#fff}" +
			"#devops-desk-theme-dock .devops-theme-hint{margin:8px 0 0;font-size:11px;color:var(--text-muted,#64748b)}" +
			"html[data-theme='dark'] #devops-desk-theme-dock .devops-theme-fab,html[data-theme='dark'] #devops-desk-theme-dock .devops-theme-panel{box-shadow:0 12px 32px rgba(0,0,0,.45)}" +
			"@media (max-width:520px){#devops-desk-theme-dock{left:12px;bottom:12px}#devops-desk-theme-dock .devops-theme-fab span{display:none}}";
		document.head.appendChild(style);
	}

	function syncDockState() {
		var dock = document.getElementById("devops-desk-theme-dock");
		if (!dock) return;
		var appearance = getAppearance();
		var desk = bootTheme();
		dock.querySelectorAll("[data-appearance]").forEach(function (btn) {
			btn.classList.toggle("is-active", btn.getAttribute("data-appearance") === appearance);
		});
		dock.querySelectorAll("[data-theme]").forEach(function (btn) {
			btn.classList.toggle("is-active", btn.getAttribute("data-theme") === desk);
		});
	}

	function ensureSwitcher() {
		removeLegacyTablerDocks();
		ensureDockStyles();
		initAppearance();

		var dock = document.getElementById("devops-desk-theme-dock");
		if (!dock) {
			dock = document.createElement("div");
			dock.id = "devops-desk-theme-dock";
			document.body.appendChild(dock);
		}

		var wantDeskUi = isLoggedInDeskUser();
		var marker = (wantDeskUi ? "with-desk" : "appearance-only") + ":" + uiLang();
		if (dock.getAttribute("data-built") === marker) {
			syncDockState();
			return;
		}

		dock.innerHTML = "";
		dock.setAttribute("data-built", marker);

		var panel = document.createElement("div");
		panel.className = "devops-theme-panel";
		panel.setAttribute("role", "dialog");
		panel.setAttribute("aria-label", t("Theme"));

		var appearanceSection = document.createElement("div");
		appearanceSection.className = "devops-theme-section";
		var appearanceLabel = document.createElement("span");
		appearanceLabel.className = "devops-theme-label";
		appearanceLabel.textContent = t("Appearance");
		appearanceSection.appendChild(appearanceLabel);
		var appearanceRow = document.createElement("div");
		appearanceRow.className = "devops-theme-row";
		APPEARANCE.forEach(function (opt) {
			var btn = document.createElement("button");
			btn.type = "button";
			btn.className = "devops-desk-theme-btn";
			btn.setAttribute("data-appearance", opt.value);
			btn.textContent = t(opt.label);
			btn.title = t(opt.title);
			btn.setAttribute("aria-label", t(opt.title));
			btn.addEventListener("click", function (e) {
				e.preventDefault();
				e.stopPropagation();
				applyAppearance(opt.value, true);
			});
			appearanceRow.appendChild(btn);
		});
		appearanceSection.appendChild(appearanceRow);
		panel.appendChild(appearanceSection);

		if (wantDeskUi) {
			var deskSection = document.createElement("div");
			deskSection.className = "devops-theme-section";
			var deskLabel = document.createElement("span");
			deskLabel.className = "devops-theme-label";
			deskLabel.textContent = t("Desk UI");
			deskSection.appendChild(deskLabel);
			var deskRow = document.createElement("div");
			deskRow.className = "devops-theme-row";
			var active = bootTheme();
			themeOptions().forEach(function (opt) {
				var btn = document.createElement("button");
				btn.type = "button";
				btn.className = "devops-desk-theme-btn" + (opt.value === active ? " is-active" : "");
				btn.setAttribute("data-theme", opt.value);
				btn.textContent = opt.label;
				btn.title = t(opt.title || opt.label);
				btn.setAttribute("aria-label", t(opt.title || opt.label));
				btn.addEventListener("click", function (e) {
					e.preventDefault();
					e.stopPropagation();
					if (opt.value === bootTheme()) return;
					applyDeskTheme(opt.value);
				});
				deskRow.appendChild(btn);
			});
			deskSection.appendChild(deskRow);
			var hint = document.createElement("p");
			hint.className = "devops-theme-hint";
			hint.textContent = t("Saved to your profile. Reloads this page only.");
			deskSection.appendChild(hint);
			panel.appendChild(deskSection);
		}

		var fab = document.createElement("button");
		fab.type = "button";
		fab.className = "devops-theme-fab";
		fab.setAttribute("aria-expanded", "false");
		fab.setAttribute("aria-controls", "devops-theme-panel");
		fab.title = t("Theme");
		fab.innerHTML =
			'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">' +
			'<circle cx="12" cy="12" r="4"></circle>' +
			'<path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"></path>' +
			"</svg><span>" +
			t("Theme") +
			"</span>";
		fab.addEventListener("click", function (e) {
			e.preventDefault();
			e.stopPropagation();
			var open = !dock.classList.contains("is-open");
			dock.classList.toggle("is-open", open);
			fab.setAttribute("aria-expanded", open ? "true" : "false");
		});

		panel.id = "devops-theme-panel";
		dock.appendChild(panel);
		dock.appendChild(fab);

		document.addEventListener(
			"click",
			function (e) {
				if (!dock.classList.contains("is-open")) return;
				if (dock.contains(e.target)) return;
				dock.classList.remove("is-open");
				fab.setAttribute("aria-expanded", "false");
			},
			true
		);

		if (!window.__devopsThemeMediaBound) {
			window.__devopsThemeMediaBound = true;
			try {
				window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function () {
					if (getAppearance() === "automatic") applyAppearance("automatic", false);
				});
			} catch (e) {
				/* ignore */
			}
		}

		syncDockState();
	}

	function onReady(fn) {
		var n = 0;
		var tmr = setInterval(function () {
			n += 1;
			if (document.body || n > 100) {
				clearInterval(tmr);
				fn();
			}
		}, 50);
	}

	// Apply appearance ASAP (login FOUC + Desk before boot finishes).
	if (document.documentElement) initAppearance();

	onReady(function () {
		removeLegacyTablerDocks();
		if (isDesk()) inject(bootTheme());
		ensureSwitcher();
		if (window.frappe && frappe.router && frappe.router.on) {
			frappe.router.on("change", function () {
				setTimeout(ensureSwitcher, 200);
			});
		}
		var obs = new MutationObserver(function () {
			removeLegacyTablerDocks();
			ensureSwitcher();
		});
		if (document.body) {
			obs.observe(document.body, { childList: true, subtree: false });
		}
	});
})();
