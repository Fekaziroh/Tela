"use strict";
// Tela! window logic. Talks to Python through window.pywebview.api (or the local bridge in a browser).

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
let api = null;
const S = { init: null, settings: {}, lang: "pt", frameNo: -1, logCount: -1, tab: "home", logos: null, state: null };

// ------------------------------------------------------------------ texts
function t(key, vars) {
  const d = STRINGS[S.lang] || STRINGS.en;
  let s = d[key] ?? STRINGS.en[key] ?? key;
  if (vars) for (const [k, v] of Object.entries(vars)) s = s.split("{" + k + "}").join(v);
  return s;
}
function applyTexts() {
  document.documentElement.lang = S.lang === "pt" ? "pt-BR" : S.lang;
  $$("[data-i18n]").forEach(el => { el.textContent = t(el.dataset.i18n); });
  $$("[data-placeholder]").forEach(el => { el.placeholder = t(el.dataset.placeholder); });
  $$("[data-label]").forEach(el => el.setAttribute("aria-label", t(el.dataset.label)));
  $("#title").textContent = t("tab." + S.tab);
  $("#logo-search").placeholder = t("look.search", { n: S.logos ? S.logos.items.length : "" }).replace("  ", " ");
  renderLangMenu();
  renderThemes();
  renderColors();
  renderScreenThemes();
  if (typeof stRender === "function") stRender();
  renderIntervals();
  renderNight();
  renderDisks();
  if (S.tab === "settings") { renderWords(); pollWeather(); }
  renderPorts();
  if (S.logos) renderLogos();
  if (S.tab === "layout" && E.lay) edRender();
  if (S.state) renderState(S.state, true);
}
const num = (v, d = 0) => Number(v).toLocaleString(S.lang === "pt" ? "pt-BR" : "en-US", { maximumFractionDigits: d });

// ------------------------------------------------------------------ settings helpers
function getSetting(path) {
  const [sec, key] = path.split(".");
  return sec ? (S.settings[sec] || {})[key] : S.settings[key];
}
let toastTimer = null;
function toast(msg) {
  const el = $("#toast");
  el.textContent = msg;
  el.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove("show"), 1400);
}
async function setSetting(path, value, quiet) {
  const [sec, key] = path.split(".");
  if (sec) (S.settings[sec] = S.settings[sec] || {})[key] = value; else S.settings[key] = value;
  try {
    await api.set(sec || null, key, value);
    if (!quiet) toast(t("toast.saved"));
  } catch (e) { toast(String(e)); }
  if (path === "ui.theme") applyTheme();
  if (path === "updates.test" && value) setTimeout(() => checkUpdate(true), 1500);
  if (path === "display.orientation") { E.lay = null; setTimeout(() => { if (S.tab === "layout") edLoad(); stLoad(); }, 900); }
  if (path === "ui.language") { S.lang = effectiveLang(); applyTexts(); }
  if (path.startsWith("display.night") || path.startsWith("display.off_") || path.startsWith("alerts.") || path.startsWith("history.")
      || path.startsWith("weather.") || path.startsWith("session.")) renderNight();
  if (path.startsWith("weather.")) { setTimeout(pollWeather, 2500); setTimeout(pollWeather, 7000); }
  if (path.startsWith("theme.")) stRender();
  if (path === "ui.language") setTimeout(renderWords, 1500);
  syncControls();
  refreshPreset();
}
function effectiveLang() {
  const l = (S.settings.ui || {}).language || "auto";
  const sys = (S.init && S.init.system_language) || ((navigator.language || "en").slice(0, 2) === "pt" ? "pt" : "en");
  return STRINGS[l] ? l : (STRINGS[sys] ? sys : "en");
}

// ------------------------------------------------------------------ generic controls ([data-set])
function syncControls() {
  document.body.classList.toggle("portrait", String(getSetting("display.orientation") || "").startsWith("portrait"));
  $$("[data-set]").forEach(el => {
    const v = getSetting(el.dataset.set);
    if (el.classList.contains("sw")) {
      el.setAttribute("aria-checked", String(el.dataset.on ? v === el.dataset.on : !!v));
    } else if (el.classList.contains("seg")) {
      $$("button", el).forEach(b => b.setAttribute("aria-pressed", String(String(v) === b.dataset.v)));
    } else if (el.type === "range") {
      if (document.activeElement !== el) el.value = v ?? 0;
    } else if (el.tagName === "SELECT") {
      el.value = v ?? (el.dataset.default || "auto");
    } else if (document.activeElement !== el) {
      el.value = v ?? "";
    }
  });
  $("#rotate").setAttribute("aria-checked", String(String(getSetting("display.orientation") || "").endsWith("_flipped")));
  const ori = String(getSetting("display.orientation") || "landscape");
  $$("#home-orient button").forEach(b => b.setAttribute("aria-pressed", String(ori.startsWith(b.dataset.v))));
  $("#logos-auto").setAttribute("aria-checked", String(((S.settings.logos || {}).mode || "auto") === "auto"));
  $("#brightness").value = getSetting("display.brightness") ?? 40;
  $("#brightness-v").textContent = $("#brightness").value + "%";
  $("#night-b-v").textContent = (getSetting("display.night_brightness") ?? 15) + "%";
  $("#bg-dim-v").textContent = (getSetting("background.dim") ?? 40) + "%";
  $("#bg-op-v").textContent = (getSetting("background.panel_opacity") ?? 85) + "%";
  const img = getSetting("background.image") || "";
  $("#bg-name").textContent = img ? img.split("/").pop() : t("bg.none");
  $("#bg-remove").hidden = !img;
  ["#bg-dim", "#bg-op"].forEach(s => { $(s).disabled = !img; });
}
function bindControls() {
  $$("[data-set]").forEach(el => {
    const path = el.dataset.set;
    if (el.classList.contains("sw")) {
      el.addEventListener("click", () => {
        const on = el.getAttribute("aria-checked") !== "true";
        setSetting(path, el.dataset.on ? (on ? el.dataset.on : el.dataset.off) : on);
      });
    } else if (el.classList.contains("seg")) {
      $$("button", el).forEach(b => b.addEventListener("click", () => setSetting(path, b.dataset.v)));
    } else if (el.type === "range") {
      el.addEventListener("input", () => { const v = $("#" + el.id + "-v"); if (v) v.textContent = el.value + "%"; });
      el.addEventListener("change", () => setSetting(path, Number(el.value)));
    } else if (el.type === "number") {
      el.addEventListener("change", () => {
        let v = Number(String(el.value).replace(",", "."));
        if (!isFinite(v)) { syncControls(); return; }
        if (el.min !== "") v = Math.max(Number(el.min), v);
        if (el.max !== "") v = Math.min(Number(el.max), v);
        el.value = v;
        setSetting(path, v);
      });
    } else if (el.classList.contains("time24")) {
      el.addEventListener("change", () => {
        const m = el.value.trim().replace(/[.h]/, ":").match(/^(\d{1,2})(?::?(\d{2}))?$/);
        if (!m || +m[1] > 23 || +(m[2] || 0) > 59) { syncControls(); toast(t("set.bad_time")); return; }
        const v = `${m[1].padStart(2, "0")}:${(m[2] || "00")}`;
        el.value = v;
        setSetting(path, v);
      });
    } else {
      el.addEventListener("change", () => setSetting(path, el.value.trim()));
    }
  });
  // brightness: the screen follows the slider; saved when released
  let last = 0;
  $("#brightness").addEventListener("input", e => {
    $("#brightness-v").textContent = e.target.value + "%";
    const now = Date.now();
    if (now - last > 120) { last = now; api.preview_brightness(Number(e.target.value)); }
  });
  $("#brightness").addEventListener("change", e => setSetting("display.brightness", Number(e.target.value)));
  $$("#home-orient button").forEach(b => b.addEventListener("click", () => {   // keeps the 180° choice
    const o = String(getSetting("display.orientation") || "landscape");
    const want = b.dataset.v + (o.endsWith("_flipped") ? "_flipped" : "");
    if (want !== o) setSetting("display.orientation", want);
  }));
  $("#rotate").addEventListener("click", () => {
    const o = getSetting("display.orientation") || "landscape";
    setSetting("display.orientation", o.endsWith("_flipped") ? o.replace("_flipped", "") : o + "_flipped");
  });
  $("#autostart").addEventListener("click", async () => {
    const el = $("#autostart");
    const want = el.getAttribute("aria-checked") !== "true";
    el.setAttribute("aria-checked", String(want));
    const real = await api.set_autostart(want);
    el.setAttribute("aria-checked", String(!!real));
    toast(t("toast.saved"));
  });
  $$("[data-cmd]").forEach(b => b.addEventListener("click", async () => {
    await api.command(b.dataset.cmd);
    toast(t("toast.sent"));
  }));
  $("#pause").addEventListener("click", async () => {
    await api.command("pause");
    if (S.state) { S.state.status.paused = !S.state.status.paused; renderState(S.state, true); }
  });
  $("#quit").addEventListener("click", () => api.quit());
  $("#release").addEventListener("click", async () => {
    await api.command("release");
    if (S.state) { S.state.status.released = !S.state.status.released; renderState(S.state, true); }
  });
  $("#restart-btn").addEventListener("click", () => openModal({ title: t("adv.restart_title"), desc: t("adv.restart_desc"), buttons: [
    { label: t("modal.cancel") }, { label: t("adv.restart"), primary: true, onClick: () => { api.restart(); } }] }));
  $("#bg-pick").addEventListener("click", async () => {
    const rel = await api.pick_background();
    if (rel) { (S.settings.background = S.settings.background || {}).image = rel; syncControls(); toast(t("toast.saved")); }
  });
  $("#bg-remove").addEventListener("click", () => setSetting("background.image", ""));
  $("#reset-colors").addEventListener("click", async () => {
    S.settings.colors = await api.theme_colors_reset();
    renderColors();
    renderScreenThemes();
    toast(t("toast.saved"));
  });
  $("#rescan").addEventListener("click", async () => { S.init.ports = await api.ports(); renderPorts(); });
  $("#tx-reset").addEventListener("click", async () => { await api.reset_screen_words(); renderWords(); toast(t("toast.saved")); });
  $("#folder-btn").addEventListener("click", () => api.open_folder());
  $("#edit-btn").addEventListener("click", () => api.edit_config());
  $("#diag-btn").addEventListener("click", showDiagnostics);
  $("#sensors-btn").addEventListener("click", showSensors);
  $("#uninstall-btn").addEventListener("click", showUninstall);
  $("#add-logos").addEventListener("click", async () => { S.logos = await api.add_logos(); renderLogos(); });
  $("#logos-folder").addEventListener("click", () => api.open_logos_folder());
  $("#logo-search").addEventListener("input", filterLogos);
  $("#logos-auto").addEventListener("click", async () => {
    const auto = ((S.settings.logos || {}).mode || "auto") === "auto";
    if (auto && !(S.settings.logos.files || "").trim() && S.logos) {
      await setSetting("logos.files", S.logos.auto.join(", "), true);   // start the list from what was showing
      S.logos.files = [...S.logos.auto];
    }
    await setSetting("logos.mode", auto ? "list" : "auto");
    renderLogos();
  });
  $("[data-set='logos.color']").addEventListener("click", () => setTimeout(loadLogos, 300));
}

// ------------------------------------------------------------------ tabs and language
function showTab(name) {
  if (S.tab === "layout" && name !== "layout" && typeof clearSelection === "function") clearSelection();
  S.tab = name;
  $$("nav [role=tab]").forEach(b => b.setAttribute("aria-selected", String(b.dataset.tab === name)));
  $$("[data-panel]").forEach(p => { p.hidden = p.dataset.panel !== name; });
  $("#title").textContent = t("tab." + name);
  $(".lang").hidden = !["home", "settings"].includes(name);
  $("#main").scrollTop = 0;
  try { localStorage.setItem("tela.tab", name); } catch (e) { /* storage may be unavailable */ }
  if (name === "look" && !S.logos) loadLogos();
  if (name === "look") { stLoad(); stMirror(); }
  if (name === "layout") edLoad();
  if (name === "advanced") { pollUsage(); renderLog(true); }
  if (name === "settings") { renderWords(); pollWeather(); }
}
function flagSvg(l) {
  const b = $(`#lang-menu [data-l="${l}"] svg`);
  return b ? b.outerHTML.replace("<svg ", '<svg class="flag" ') : "";
}
function renderLangMenu() {
  const setting = (S.settings.ui || {}).language || "auto";
  $("#lang-flag").innerHTML = flagSvg(S.lang);
  const sys = (S.init && S.init.system_language) || "en";
  $("#lang-auto-desc").textContent = t("lang.auto_desc", { name: LANG_NAMES[STRINGS[sys] ? sys : "en"] });
  $$("#lang-menu [data-l]").forEach(b => b.setAttribute("aria-checked", String(b.dataset.l === setting)));
}
function bindLangMenu() {
  const btn = $("#lang-btn"), menu = $("#lang-menu");
  const close = () => { menu.hidden = true; btn.setAttribute("aria-expanded", "false"); };
  btn.addEventListener("click", e => { e.stopPropagation(); menu.hidden = !menu.hidden; btn.setAttribute("aria-expanded", String(!menu.hidden)); });
  $$("#lang-menu [data-l]").forEach(b => b.addEventListener("click", () => { close(); setSetting("ui.language", b.dataset.l); }));
  document.addEventListener("click", e => { if (!menu.contains(e.target)) close(); });
  document.addEventListener("keydown", e => { if (e.key === "Escape") { close(); closeModal(); } });
}

// ------------------------------------------------------------------ screen texts and weather
async function renderWords() {
  const box = $("#tx-list");
  if (!box || !api) return;
  let w;
  try { w = await api.screen_words(); } catch (e) { return; }
  S.words = w;
  box.innerHTML = "";
  for (const k of w.keys) {
    const lab = document.createElement("label");
    lab.innerHTML = `<span>${esc(w.words[k] || k)}</span><input class="txt" maxlength="24">`;
    const inp = $("input", lab);
    inp.placeholder = w.words[k] || "";
    inp.value = w.custom[k] || "";
    inp.addEventListener("change", async () => {
      await api.set_screen_word(k, inp.value.trim());
      w.custom[k] = inp.value.trim();
      toast(t("toast.saved"));
    });
    box.appendChild(lab);
  }
}
async function pollWeather() {
  const el = $("#wx-status");
  if (!el || S.tab !== "settings") return;
  let st;
  try { st = await api.weather_status(); } catch (e) { return; }
  const city = ((S.settings.weather || {}).city || "").trim();
  el.textContent = !city ? t("wx.no_city") : st.state === "ok" ? t("wx.now", { place: [st.place, st.country].filter(Boolean).join(", "), text: st.text || "" })
    : st.state === "error" ? t(st.error === "city not found" ? "wx.not_found" : "wx.offline") : st.state === "off" ? "" : t("wx.waiting");
}

// ------------------------------------------------------------------ static sections
const COLOR_KEYS = ["accent", "warn", "crit", "background", "panel", "text", "secondary", "track"];
function renderColors() {
  const box = $("#colors");
  if (!box || !S.init) return;
  const cur = { ...(S.init.default_colors || {}), ...(S.settings.colors || {}) };
  box.innerHTML = "";
  for (const k of COLOR_KEYS) {
    const v = String(cur[k] || "#000000").toUpperCase();
    const el = document.createElement("label");
    el.className = "color";
    el.innerHTML = `<i style="background:${v}"></i><div><b style="font-weight:500">${t("color." + k)}</b><small>${t("color." + k + "_d")}</small><code>${v}</code></div><input type="color" value="${v.length === 7 ? v : "#000000"}" aria-label="${t("color." + k)}">`;
    const input = $("input", el);
    input.addEventListener("input", () => { $("i", el).style.background = input.value; $("code", el).textContent = input.value.toUpperCase(); });
    input.addEventListener("change", async () => {
      const custom = await api.set_screen_color(k, input.value.toUpperCase());
      S.settings.custom_colors = custom;
      S.settings.colors = { ...custom };
      renderScreenThemes(); followScreenColors(); toast(t("toast.saved"));
    });
    box.appendChild(el);
  }
  followScreenColors();
}
const SCREEN_THEME_KEYS = ["dark", "light", "red", "ice"];
function renderScreenThemes() {
  const box = $("#screen-themes");
  if (!box || !S.screenThemes) return;
  const cur = S.settings.colors || {};
  const same = c => ["background", "panel", "accent", "text", "secondary", "track"].every(x => String(cur[x] || "").toUpperCase() === String(c[x] || "").toUpperCase());
  const own = typeof stCur === "function" && stCur() ? stCur().colors : null;   // the screen theme's own colors
  const palettes = { theme: own, ...S.screenThemes };
  const keys = [...(own ? ["theme"] : []), ...SCREEN_THEME_KEYS];
  const preset = keys.find(k => same(palettes[k]));
  const mine = S.settings.custom_colors || {};
  const custom = Object.keys(mine).length ? { ...S.screenThemes.dark, ...mine } : null;
  box.innerHTML = "";
  for (const k of [...keys, "custom"]) {
    if (k === "custom" && !custom && preset) continue;   // shown once the user has own colors
    const c = k === "custom" ? (custom || cur) : palettes[k];
    const on = k === "custom" ? !preset : k === preset;
    const b = document.createElement("button");
    b.className = "theme";
    b.setAttribute("aria-pressed", String(on));
    b.innerHTML = `<div class="mini" style="background:${c.background};grid-template-columns:1fr 1fr;gap:4px;padding:5px">
      <div style="background:${c.panel};border-radius:3px;padding:4px;display:grid;gap:3px;align-content:start"><b style="height:3px;background:${c.secondary};border-radius:2px;width:60%"></b><b style="height:8px;background:${c.text};border-radius:2px;width:45%"></b><b style="height:3px;background:${c.accent};border-radius:2px"></b></div>
      <div style="background:${c.panel};border-radius:3px;display:grid;place-items:center"><i style="width:22px;height:22px;border-radius:50%;border:3px solid ${c.accent};border-bottom-color:${c.track}"></i></div></div><span>${t("stheme." + k)}</span>`;
    b.addEventListener("click", async () => {
      const colors = k === "theme" ? await api.theme_colors_reset() : await api.screen_theme(k);
      S.settings.colors = { ...(S.settings.colors || {}), ...colors };
      renderColors(); renderScreenThemes(); toast(t("toast.saved"));
    });
    box.appendChild(b);
  }
}
const INTERVAL_GROUPS = [["cpu", /^cpu/], ["gpu", /^(gpu|vram)/], ["ram", /^ram/], ["disks", /^(disk|ssd)/], ["net", /^net/], ["app", /^app/]];
function intervalGroup(name) { const g = INTERVAL_GROUPS.find(([, re]) => re.test(name)); return g ? g[0] : "other"; }
function renderIntervals() {
  const box = $("#intervals");
  if (!box || !S.init) return;
  const base = Number(S.settings.interval || 1);
  const cur = S.settings.intervals || {};
  const all = !!S.intervalsAll;
  box.innerHTML = "";
  const groups = {};
  for (const name of S.init.sensors) (groups[intervalGroup(name)] = groups[intervalGroup(name)] || []).push(name);
  let changed = 0;
  for (const key of [...INTERVAL_GROUPS.map(g => g[0]), "other"]) {
    const names = groups[key];
    if (!names) continue;
    const diff = names.filter(n => Number(cur[n] || base) > base).length;
    changed += diff;
    const det = document.createElement("details");
    det.className = "int-group";
    det.open = all ? diff > 0 : true;
    det.hidden = !all && !diff;
    det.innerHTML = `<summary><b>${t("int.g_" + key)}</b><small>${diff ? t("int.changed", { n: diff }) : t("int.count", { n: names.length })}</small></summary>`;
    for (const name of names) {
      const v = Math.max(Number(cur[name] || base), base);
      const row = document.createElement("div");
      row.className = "row";
      row.hidden = !all && !(v > base);
      row.innerHTML = `<span>${t("sensor." + name)}</span><span class="inline"><input class="num" type="number" min="0.5" max="120" step="0.5" value="${v}"><span>${t("s")}</span></span>`;
      $("input", row).addEventListener("change", saveIntervals);
      row.dataset.name = name;
      det.appendChild(row);
    }
    box.appendChild(det);
  }
  const more = document.createElement("button");
  more.className = "btn int-more";
  more.textContent = all ? t("int.less") : t("int.all", { n: S.init.sensors.length });
  more.addEventListener("click", () => { S.intervalsAll = !all; renderIntervals(); });
  if (!all && !changed) { const p = document.createElement("p"); p.className = "hint"; p.textContent = t("int.none"); box.appendChild(p); }
  box.appendChild(more);
}
async function saveIntervals() {
  const base = Number(S.settings.interval || 1);
  const items = {};
  $$("#intervals .row").forEach(r => { items[r.dataset.name] = Math.max(base, Number($("input", r).value) || base); });
  S.settings.intervals = Object.fromEntries(Object.entries(items).filter(([, v]) => v > base));
  await api.set_intervals(base, items);
  toast(t("toast.saved"));
}
function renderNight() {
  const d = S.settings.display || {};
  const hs = $("#hist-sub");
  if (hs) hs.classList.toggle("off", (S.settings.history || {}).save === false);
  $("#night-sub").classList.toggle("off", !d.night_enabled);
  $("#off-sub").classList.toggle("off", !d.off_enabled);
  $("#al-sub").classList.toggle("off", !(S.settings.alerts || {}).enabled);
  $("#wx-sub").classList.toggle("off", (S.settings.weather || {}).enabled === false);
  $("#sum-sub").classList.toggle("off", (S.settings.session || {}).summary === false);
  const sg = $("[data-set='session.graph']");
  if (sg) sg.classList.toggle("off", (S.settings.session || {}).show_graph === false);
  $("#night-desc").textContent = t("home.night_desc", { b: d.night_brightness ?? 15, a: d.night_start || "22:00", z: d.night_end || "07:00" });
}
function renderDisks() {
  const d = (S.init && S.init.disks) || [];
  $("#disks").textContent = d.length ? d.map(x => `${x.letter} ${x.name}${x.kind ? " (" + x.kind + ")" : ""}`).join(" · ") : t("set.none_detected");
}
function renderPorts() {
  const sel = $("#port");
  if (!sel || !S.init) return;
  const cur = getSetting("display.port") || "auto";
  const opts = [["auto", t("port.auto")], ...S.init.ports.map(p => [p.device, `${p.device} · ${p.label}`])];
  if (cur !== "auto" && !opts.some(o => o[0] === cur)) opts.push([cur, cur]);
  sel.innerHTML = "";
  for (const [v, label] of opts) { const o = document.createElement("option"); o.value = v; o.textContent = label; sel.appendChild(o); }
  sel.value = cur;
}

// ------------------------------------------------------------------ logos
async function loadLogos() { S.logos = await api.logos(); renderLogos(); }
function renderLogos() {
  const L = S.logos;
  const box = $("#logos");
  const auto = ((S.settings.logos || {}).mode || "auto") === "auto";
  const chosen = new Set(auto ? L.auto : L.files);
  $("#logo-search").placeholder = t("look.search", { n: L.items.length });
  $("#logos-auto-now").textContent = L.auto.length ? t("look.logos_auto_now", { list: L.auto.map(n => n.replace(/\.[a-z]+$/i, "").replace(/ Logo$/i, "")).join(", ") }) : "";
  $("#logos-count").textContent = t("look.selected", { n: chosen.size });
  box.innerHTML = "";
  if (!L.items.length) { box.innerHTML = `<p class="hint">${t("look.none")}</p>`; return; }
  for (const it of L.items) {
    const el = document.createElement("label");
    el.className = "logo" + (auto ? " locked" : "");
    el.title = it.name;
    el.innerHTML = `<input type="checkbox" ${chosen.has(it.name) ? "checked" : ""} ${auto ? "disabled" : ""}>${it.thumb ? `<img src="${it.thumb}" alt="">` : "<b>?</b>"}<span>${it.label}</span>`;
    $("input", el).addEventListener("change", saveLogoList);
    el.dataset.name = it.name;
    box.appendChild(el);
  }
  filterLogos();
}
function filterLogos() {
  const q = $("#logo-search").value.trim().toLowerCase();
  $$("#logos .logo").forEach(l => { l.hidden = q && !l.dataset.name.toLowerCase().includes(q); });
}
async function saveLogoList() {
  const names = $$("#logos .logo").filter(l => $("input", l).checked).map(l => l.dataset.name);
  S.logos.files = names;
  $("#logos-count").textContent = t("look.selected", { n: names.length });
  await setSetting("logos.files", names.join(", "));
}

// ------------------------------------------------------------------ live state
function pill(kind, label, text, title) {
  return `<div class="pill ${kind}" title="${(title || text || "").replace(/"/g, "&quot;")}"><i></i><b>${label}</b><span>${text}</span></div>`;
}
function mmss(sec) {
  sec = Math.max(0, Math.floor(sec));
  const h = Math.floor(sec / 3600), m = Math.floor(sec / 60) % 60, s = sec % 60;
  return (h ? h + ":" + String(m).padStart(2, "0") : String(m).padStart(2, "0")) + ":" + String(s).padStart(2, "0");
}
function screenState(st) {
  if (st.released) return ["warn", t("st.released")];
  if (st.paused) return ["warn", t("st.paused")];
  if (st.sleeping && st.sleeping.length) {
    const r = st.sleeping[0];
    return ["warn", t(r === "lock" ? "st.off_lock" : r === "monitor" ? "st.off_monitor" : r === "schedule" ? "st.off_schedule" : "st.off_suspend")];
  }
  if (st.connected) return ["ok", t("st.connected", { port: st.port || "" })];
  const e = st.screen_error || "";
  if (/PermissionError|denied|negado|Access/i.test(e)) return ["err", t("st.busy")];
  if (/unsupported screen: (.*)/i.test(e)) return ["err", t("st.unsupported", { m: e.match(/unsupported screen: (.*)/i)[1] })];
  if (/not found/i.test(e)) return ["err", t("st.not_found")];
  if (e) return ["err", e.slice(0, 80)];
  return ["warn", t("st.connecting")];
}
function renderState(s, quick) {
  S.state = s;
  renderUpdate(s.update);
  const cf = s.conflict || [];
  $("#conflict").hidden = !cf.length;
  if (cf.length) $("#conflict-msg").textContent = t("conf.msg", { apps: cf.join(", ") });
  const st = s.status;
  // pills
  const pills = [];
  const [sk, stext] = screenState(st);
  pills.push(pill(sk, t("pill.screen"), stext, st.screen_error));
  if (st.demo) pills.push(pill("warn", t("pill.sensors"), t("st.demo")));
  else if (st.source === "embedded") pills.push(st.lhm_error ? pill("err", t("pill.sensors"), t("st.sensor_error"), st.lhm_error)
    : st.admin ? pill("ok", t("pill.sensors"), t("st.embedded")) : pill("warn", t("pill.sensors"), t("st.no_admin")));
  else if (st.source) pills.push(st.lhm_error ? pill("err", t("pill.sensors"), t("st.web_error"), st.lhm_error) : pill("ok", t("pill.sensors"), t("st.web")));
  if (st.hwinfo) pills.push(st.hwinfo.error ? pill("warn", "HWiNFO", t("st.hwinfo_off"), st.hwinfo.error)
    : pill("ok", "HWiNFO", t("st.hwinfo_on", { n: st.hwinfo.count })));
  const f = st.fps || {};
  if (st.demo) pills.push(pill("ok", t("pill.fps"), t("st.fps_game", { fps: "120", app: "Demo" })));
  else if (f.fps) pills.push(pill("ok", t("pill.fps"), t("st.fps_game", { fps: Math.round(f.fps), app: f.app || "" })));
  else if (f.running) pills.push(pill("ok", t("pill.fps"), t("st.fps_wait")));
  else if (f.error && f.error !== "PresentMon not found") pills.push(pill("err", t("pill.fps"), t("st.fps_error"), f.error));
  else pills.push(pill("warn", t("pill.fps"), t("st.fps_none"), f.error));
  const n = s.network || {};
  if (n.state === "down") pills.push(pill("err", t("pill.network"), t("st.net_down", { t: mmss(Date.now() / 1000 - (n.since || Date.now() / 1000)) })));
  else if (n.state === "unstable") pills.push(pill("warn", t("pill.network"), t("st.net_unstable", { ms: n.ms == null ? "--" : Math.round(n.ms), loss: Math.round(n.loss || 0) })));
  else if (n.state === "normal") pills.push(pill("ok", t("pill.network"), t("st.net", { ms: n.ms == null ? "--" : Math.round(n.ms), loss: Math.round(n.loss || 0) })));
  else pills.push(pill("", t("pill.network"), (S.settings.network || {}).ping === false ? t("st.net_off") : t("st.net_wait")));
  if (!s.media_enabled) pills.push(pill("", t("pill.music"), t("st.music_off")));
  else if (s.media) pills.push(pill("ok", t("pill.music"), s.media.title + (s.media.artist ? " · " + s.media.artist : "")));
  else if (s.media_error) pills.push(pill("warn", t("pill.music"), t("st.music_error"), s.media_error));
  else pills.push(pill("", t("pill.music"), t("st.music_idle")));
  if (s.usage) pills.push(pill("", "Tela!", t("st.usage", { cpu: num(s.usage.cpu, 1), ram: num(s.usage.ram_mb) }), t("pill.usage")));
  if (st.eco) pills.push(pill("", t("pill.eco"), t("st.eco")));
  $("#pills").innerHTML = pills.join("");
  // device and preview
  const dev = $("#device");
  dev.className = "device " + sk;
  $("#device-port").textContent = st.port || "—";
  $("#preview-size").textContent = S.frameSize ? `· ${S.frameSize}` : "";
  $("#preview-note").textContent = st.released ? t("home.released") : st.paused ? t("home.paused") : (st.sleeping && st.sleeping.length) ? t("home.off") : st.eco ? t("home.eco") : "";
  $("#pause").textContent = st.paused ? t("home.resume") : t("home.pause");
  $("#pause").disabled = !!st.released;
  $("#release").textContent = st.released ? t("home.retake") : t("home.release");
  $("#release").title = t("home.release_hint");
  $("#port-now").textContent = t("set.port_now", { port: st.connected ? st.port : t("set.port_none") });
  if (s.frame) showFrame(s.frame);
  if (s.theme_imported) stImported(s.theme_imported);
  $("#preview-paused").hidden = s.preview !== false;
  if (s.disks && JSON.stringify(s.disks) !== JSON.stringify(S.init.disks)) { S.init.disks = s.disks; renderDisks(); }
  renderLastGame(s.last_game);
  if (!quick || S.tab === "advanced") renderLog();
}
function renderLastGame(g) {
  const body = $("#last-body");
  if (!g) {
    $("#last-when").textContent = "";
    body.innerHTML = `<p>${t("home.last_empty", { min: (S.settings.session || {}).min_minutes ?? 5 })}</p>`;
    return;
  }
  let when = "";
  if (g.ended_at) {
    const d = new Date(g.ended_at * 1000), now = new Date();
    const days = Math.round((new Date(now.toDateString()) - new Date(d.toDateString())) / 86400000);
    when = days === 0 ? t("when.today") : days === 1 ? t("when.yesterday") : d.toLocaleDateString(S.lang === "pt" ? "pt-BR" : "en-US", { day: "2-digit", month: "2-digit" });
  }
  $("#last-when").textContent = [when, g.duration].filter(Boolean).join(" · ");
  const v = x => (x == null ? "--" : num(Math.round(x)));
  body.innerHTML = `<div class="game-name" title="${g.name}">${g.name}</div>
    <div class="stats" style="margin-top:10px"><div><span>${t("home.fps_avg")}</span><b>${v(g.fps_avg)}</b></div>
    <div><span>${t("home.low")}</span><b>${v(g.fps_1low)}</b></div><div><span>${t("home.cpu_max")}</span><b>${v((g.max || {}).cpu)}${(g.max || {}).cpu == null ? "" : "°"}</b></div></div>
    <div class="btns" style="margin-top:12px"><button class="btn" id="show-last">${t("home.show")}</button><button class="btn" id="last-history">${t("hist.open")}</button></div>`;
  $("#show-last").addEventListener("click", async () => { await api.command("summary_last"); toast(t("toast.sent")); });
  $("#last-history").addEventListener("click", showHistory);
}
function renderLog(force) {
  const s = S.state;
  if (!s || (!force && s.log_count === S.logCount)) return;
  S.logCount = s.log_count;
  const el = $("#log");
  const atEnd = el.scrollHeight - el.scrollTop - el.clientHeight < 30;
  el.innerHTML = s.log.map(l => { const i = l.indexOf("  "); return i > 0 ? `<b>${l.slice(0, i)}</b>${esc(l.slice(i))}` : esc(l); }).join("\n");
  if (atEnd || force) el.scrollTop = el.scrollHeight;
}
const esc = s => s.replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));

// The preview is drawn on canvases. Setting a new image URL on every frame made WebView2 keep each
// decoded picture (about 70 MB more per minute).
async function showFrame(dataUrl) {
  const bin = atob(dataUrl.slice(dataUrl.indexOf(",") + 1));
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  let bmp;
  try { bmp = await createImageBitmap(new Blob([bytes], { type: "image/png" })); } catch (e) { return; }
  S.frameSize = `${bmp.width}×${bmp.height}`;
  const targets = [$("#preview")];
  if (!$("#stage-boxes .drag")) targets.push($("#stage-img"));
  for (const c of targets) {
    if (!c) continue;
    const resized = c.width !== bmp.width || c.height !== bmp.height;
    if (resized) { c.width = bmp.width; c.height = bmp.height; }
    c.getContext("2d").drawImage(bmp, 0, 0);
    if (c.id === "stage-img" && (resized || !c.dataset.ready) && S.tab === "layout") { c.dataset.ready = "1"; edRenderBoxes(); }
  }
  bmp.close();
  document.dispatchEvent(new Event("tela-frame"));
}
function copyFrame(canvas) {
  const src = $("#preview");
  if (canvas.width !== src.width || canvas.height !== src.height) { canvas.width = src.width; canvas.height = src.height; }
  canvas.getContext("2d").drawImage(src, 0, 0);
}

async function poll() {
  let wait = 700;
  if (document.visibilityState === "visible") {
    try {
      const s = await api.state(S.frameNo);
      if (s.hidden) wait = 2000;   // the window is in the tray: nothing to draw
      else { renderState(s); S.frameNo = s.frame_no; }
    } catch (e) { wait = 2000; /* the app may be closing */ }
  } else wait = 2000;
  setTimeout(poll, wait);
}
async function pollUsage() {
  if (S.tab !== "advanced" || document.visibilityState !== "visible") return;
  try {
    const u = await api.usage();
    let cpu = 0, ram = 0;
    $("#usage").innerHTML = Object.entries(u).filter(([, v]) => v.ram_mb).map(([k, v]) => {
      cpu += v.cpu; ram += v.ram_mb;
      return `<div><div class="row"><span>${t("usage." + k)}</span><span class="val">${num(v.cpu, 1)}% · ${num(v.ram_mb)} MB</span></div><div class="bar"><i style="width:${Math.min(100, v.ram_mb / 4)}%"></i></div></div>`;
    }).join("");
    $("#usage-total").textContent = t("adv.usage_total", { cpu: num(cpu, 1), ram: num(ram) });
  } catch (e) { /* ignore */ }
  setTimeout(pollUsage, 2000);
}

// ------------------------------------------------------------------ modals
let lastFocus = null;
function openModal({ title, desc, body, buttons }) {
  lastFocus = document.activeElement;
  $("#modal-title").textContent = title;
  $("#modal-desc").textContent = desc || "";
  $("#modal-desc").hidden = !desc;
  const b = $("#modal-body");
  b.innerHTML = "";
  if (typeof body === "string") b.innerHTML = body; else if (body) b.appendChild(body);
  const foot = $("#modal-foot");
  foot.innerHTML = "";
  for (const btn of buttons || [{ label: t("modal.close"), primary: true }]) {
    const el = document.createElement("button");
    el.className = "btn" + (btn.primary ? " pri" : "") + (btn.danger ? " danger" : "");
    el.textContent = btn.label;
    el.addEventListener("click", async () => { if (btn.onClick && (await btn.onClick(el)) === false) return; closeModal(); });
    foot.appendChild(el);
  }
  $("#overlay").hidden = false;
  (foot.lastChild || b).focus();
}
function closeModal() {
  if ($("#overlay").hidden) return;
  $("#overlay").hidden = true;
  if (lastFocus) lastFocus.focus();
}
async function copyText(text, el) {
  let ok = false;
  try { await navigator.clipboard.writeText(text); ok = true; } catch (e) { ok = await api.copy(text); }
  if (el) el.textContent = ok ? t("modal.copied") : t("modal.copy");
  return ok;
}
async function showDiagnostics() {
  const pre = document.createElement("pre");
  pre.textContent = "…";
  openModal({ title: t("diag.title"), desc: t("diag.desc"), body: pre, buttons: [
    { label: t("modal.copy"), onClick: async el => { await copyText(pre.textContent, el); return false; } },
    { label: t("modal.close"), primary: true }] });
  pre.textContent = await api.diagnostics();
}
async function showSensors(pick) {
  if (typeof pick !== "function") pick = null;
  const wrap = document.createElement("div");
  wrap.innerHTML = `<input class="txt" type="search" placeholder="${t("sensors.search")}" style="margin-bottom:8px"><p class="hint">${t("sensors.loading")}</p><div class="sensor-list"></div>`;
  openModal({ title: t("sensors.title"), desc: pick ? t("sensors.pick") : t("sensors.hint"), body: wrap });
  const res = await api.sensors();
  const list = $(".sensor-list", wrap);
  $(".hint", wrap).textContent = res.notes.includes("demo") ? t("sensors.demo") : res.notes.join(" · ");
  let current = null;
  for (const r of res.rows) {
    if (r.hardware !== current) {
      current = r.hardware;
      const h = document.createElement("h4"); h.textContent = current || "—"; list.appendChild(h);
    }
    const b = document.createElement("button");
    b.innerHTML = `<code>${esc(r.selector)}</code><span>${esc(r.value)}</span>`;
    b.dataset.q = (r.hardware + " " + r.selector).toLowerCase();
    b.addEventListener("click", async () => {
      if (pick) { closeModal(); pick(r.selector); return; }
      await copyText(r.selector); toast(t("modal.copied"));
    });
    list.appendChild(b);
  }
  $("input", wrap).addEventListener("input", e => {
    const q = e.target.value.trim().toLowerCase();
    $$("button", list).forEach(b => { b.hidden = q && !b.dataset.q.includes(q); });
  });
}
// Tela! was reopened by the guard process after it stopped responding
function showRecovered() {
  api.recovered_seen();
  openModal({ title: t("crash.title"), desc: t("crash.desc"), buttons: [
    { label: t("crash.report"), onClick: () => { api.open_url("https://github.com/Fekaziroh/Tela/issues/new/choose"); return false; } },
    { label: t("adv.diag"), onClick: () => { closeModal(); showDiagnostics(); return false; } },
    { label: t("modal.close"), primary: true }] });
}
function showUninstall() {
  const body = `<p style="margin:0 0 12px;color:var(--muted)">${t("uninstall.body")}</p>
    <div class="row"><span class="lbl">${t("uninstall.data")}<small>${esc(S.init.folder || "")}</small></span><button class="sw" role="switch" id="un-data" aria-checked="false"></button></div>`;
  openModal({ title: t("uninstall.title"), body, buttons: [
    { label: t("modal.cancel") },
    { label: t("uninstall.ok"), danger: true, onClick: () => api.uninstall($("#un-data").getAttribute("aria-checked") === "true") }] });
  $("#un-data").addEventListener("click", e => e.target.setAttribute("aria-checked", String(e.target.getAttribute("aria-checked") !== "true")));
}

// ------------------------------------------------------------------ start
async function start() {
  S.init = await api.init();
  S.settings = S.init.settings;
  S.themes = S.init.themes || [];
  S.screenThemes = await api.screen_themes();
  S.lang = effectiveLang();
  $("#version").textContent = S.init.version;
  applyTheme();
  $("#autostart").setAttribute("aria-checked", String(S.init.autostart));
  if (!S.init.windows) $("#autostart").disabled = true;
  bindControls();
  bindLangMenu();
  bindThemes();
  bindScreenThemes();
  bindEditor();
  $$("nav [role=tab]").forEach(b => b.addEventListener("click", () => showTab(b.dataset.tab)));
  $("#overlay").addEventListener("click", e => { if (e.target.id === "overlay") closeModal(); });
  let tab = "home";
  try { tab = localStorage.getItem("tela.tab") || "home"; } catch (e) { /* ignore */ }
  syncControls();
  showTab(["home", "layout", "look", "settings", "advanced"].includes(tab) ? tab : "home");
  applyTexts();
  stLoad(false);
  poll();
  $("#wizard-btn").addEventListener("click", wizStart);
  bindHistory();
  renderHistoryFolder();
  bindUpdate();
  bindPresets();
  $("#conflict-btn").addEventListener("click", async () => { await api.close_conflict(); toast(t("conf.closed")); });
  $("#set-search").addEventListener("input", e => searchSettings(e.target.value));
  $("#about-ver").textContent = S.init.version;
  $$("[data-url]").forEach(b => b.addEventListener("click", () => api.open_url(b.dataset.url)));
  if (S.init.recovered) setTimeout(showRecovered, 700);
  else if (wizNeeded()) setTimeout(wizStart, 800);
  else if (S.init.updated_from) setTimeout(() => { showWhatsNew(S.init.updated_from); api.news_seen(); }, 600);
  document.addEventListener("visibilitychange", () => { if (document.visibilityState === "visible" && S.tab === "advanced") pollUsage(); });
}

function bridgeApi() {
  const token = new URLSearchParams(location.search).get("t");
  return new Proxy({}, { get: (_, name) => (...args) => fetch("/api/" + String(name), {
    method: "POST", headers: { "Content-Type": "application/json", "X-Tela-Token": token }, body: JSON.stringify(args),
  }).then(r => r.json()).then(r => { if (r.error) throw new Error(r.error); return r.result; }) });
}
function boot() {
  if (window.pywebview && window.pywebview.api && window.pywebview.api.init) { api = window.pywebview.api; start(); return true; }
  return false;
}
if (!boot()) {
  window.addEventListener("pywebviewready", () => { if (!api) boot(); });
  if (location.protocol.startsWith("http") && new URLSearchParams(location.search).get("t")) { api = bridgeApi(); start(); }
}

// ------------------------------------------------------------------ search in Settings
function searchSettings(q) {
  const norm = s => String(s || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  const words = norm(q).split(/\s+/).filter(Boolean);
  const hit = el => { const tx = norm(el.textContent); return words.every(w => tx.includes(w)); };
  let any = false;
  $$('[data-panel="settings"] .grid > .card').forEach(card => {
    const parts = $$(":scope > .row, :scope > .sub, :scope > p, :scope > .presets, :scope > .profiles, :scope > .item-list, :scope > .btns, :scope > hr", card);
    if (!words.length) { card.hidden = false; parts.forEach(p => p.classList.remove("s-hide")); card.classList.remove("s-hit"); return; }
    const title = $("h3", card);
    const whole = title && hit(title);
    let n = 0;
    parts.forEach(p => { const ok = whole || hit(p); p.classList.toggle("s-hide", !ok); if (ok) n++; });
    card.hidden = !whole && !n;
    card.classList.toggle("s-hit", !card.hidden);
    if (!card.hidden) any = true;
  });
  $("#set-search-none").hidden = !words.length || any;
}
