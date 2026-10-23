"use strict";
// Window themes: Automatic/Light/Dark, ready-made presets and the user's own themes (saved by the app).

const THEME_VARS = ["bg", "win", "panel", "panel2", "line", "fg", "muted", "accent"];
const THEME_PRESETS = {
  graphite: { bg: "#0c0e11", win: "#111419", panel: "#171b21", panel2: "#1d222a", line: "#262c35", fg: "#e8edf3", muted: "#8b95a3", accent: "#eef1f5" },
  light: { bg: "#eef1f4", win: "#f7f8fa", panel: "#ffffff", panel2: "#f0f2f5", line: "#dce1e7", fg: "#141920", muted: "#566170", accent: "#20262e" },
  black: { bg: "#000000", win: "#050506", panel: "#0e0e10", panel2: "#17171a", line: "#232327", fg: "#f2f2f3", muted: "#8c8c93", accent: "#ffffff" },
  red: { bg: "#0e0a0b", win: "#140d0f", panel: "#1c1214", panel2: "#26171a", line: "#3a2124", fg: "#f6eded", muted: "#a8908f", accent: "#ff453a" },
  green: { bg: "#0b0e0c", win: "#101411", panel: "#151b17", panel2: "#1b231e", line: "#24302a", fg: "#e9f2ec", muted: "#8a9b90", accent: "#3ccf7a" },
  purple: { bg: "#0d0b10", win: "#120f17", panel: "#19151f", panel2: "#211b29", line: "#2e2639", fg: "#efeaf6", muted: "#9b91a8", accent: "#b48cff" },
  ice: { bg: "#0b0e12", win: "#10141a", panel: "#151b23", panel2: "#1b232d", line: "#25303c", fg: "#e7eef6", muted: "#8a97a6", accent: "#8fd3ff" },
  sand: { bg: "#efebe4", win: "#f7f4ef", panel: "#fffdf9", panel2: "#f1ece4", line: "#ddd5c8", fg: "#231d16", muted: "#6f6455", accent: "#b4581e" },
};
let themeDraft = null;   // colors being edited (live preview)

function hexLum(hex) {
  const n = parseInt(String(hex || "#000").slice(1, 7), 16);
  const c = [(n >> 16) & 255, (n >> 8) & 255, n & 255].map(v => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; });
  return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
}
function mixHex(a, b, f) {
  const p = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
  const x = p(a), y = p(b);
  return "#" + x.map((v, i) => Math.round(v + (y[i] - v) * f).toString(16).padStart(2, "0")).join("");
}
function systemDark() { return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches; }

function themeColors(id) {
  id = id || "auto";
  if (id === "auto") return null;
  if (id === "light") return THEME_PRESETS.light;
  if (id === "dark") return THEME_PRESETS.black;
  if (id.startsWith("preset:")) return THEME_PRESETS[id.slice(7)] || null;
  if (id.startsWith("custom:")) { const th = (S.themes || []).find(x => x.name === id.slice(7)); return th ? th.colors : null; }
  return null;
}
function paintTheme(colors) {
  const root = document.documentElement;
  THEME_VARS.concat(["dim", "log"]).forEach(v => root.style.removeProperty("--" + v));
  if (!colors) { root.removeAttribute("data-theme"); return; }
  const dark = hexLum(colors.bg) < 0.4;
  root.setAttribute("data-theme", dark ? "dark" : "light");
  THEME_VARS.forEach(v => { if (colors[v]) root.style.setProperty("--" + v, colors[v]); });
  root.style.setProperty("--dim", mixHex(colors.muted, colors.bg, 0.3));
  root.style.setProperty("--log", mixHex(colors.bg, dark ? "#000000" : "#ffffff", 0.35));
}
function currentThemeColors() {
  return themeColors((S.settings.ui || {}).theme) || (systemDark() ? THEME_PRESETS.black : THEME_PRESETS.light);
}
function applyTheme() {
  paintTheme(themeDraft || themeColors((S.settings.ui || {}).theme));
  const c = themeDraft || currentThemeColors();
  if (api && api.set_tray_accent) api.set_tray_accent(hexLum(c.accent) > 0.25 ? c.accent : "#ffffff").catch(() => {});
  if (api && api.set_title_bar) api.set_title_bar(c.win, c.fg, hexLum(c.bg) < 0.4).catch(() => {});
}

function miniPreview(c) {
  return `<div class="mini" style="background:${c.bg}"><div class="side" style="background:${c.win}"><i style="background:${c.muted}"></i><i style="background:${c.accent};opacity:1"></i><i style="background:${c.muted}"></i></div>
    <div class="area"><div class="card-s" style="background:${c.panel}"><b style="background:${c.muted}"></b><u style="background:${c.accent}"></u></div>
    <div class="card-s" style="background:${c.panel}"><b style="background:${c.fg}"></b></div></div></div>`;
}
function renderThemes() {
  const box = $("#themes");
  if (!box) return;
  const cur = (S.settings.ui || {}).theme || "auto";
  const tiles = [["auto", t("theme.auto"), null], ["light", t("theme.light"), THEME_PRESETS.light], ["dark", t("theme.dark"), THEME_PRESETS.black]];
  for (const k of ["graphite", "red", "green", "purple", "ice", "sand"]) tiles.push(["preset:" + k, t("theme." + k), THEME_PRESETS[k]]);
  for (const th of S.themes || []) tiles.push(["custom:" + th.name, th.name, th.colors]);
  box.innerHTML = "";
  for (const [id, label, c] of tiles) {
    const b = document.createElement("button");
    b.className = "theme";
    b.setAttribute("aria-pressed", String(id === cur));
    b.innerHTML = c ? miniPreview(c) + `<span>${esc(label)}</span>`
      : `<div style="position:relative;height:54px"><div class="auto-split" style="inset:0">${miniPreview(THEME_PRESETS.light)}${miniPreview(THEME_PRESETS.black)}</div></div><span>${esc(label)}</span>`;
    b.addEventListener("click", () => { closeThemeEditor(); setSetting("ui.theme", id).then(renderThemes); });
    box.appendChild(b);
  }
  const custom = cur.startsWith("custom:");
  $("#theme-new").textContent = custom ? t("theme.edit") : t("theme.customize");
}
function openThemeEditor() {
  const cur = (S.settings.ui || {}).theme || "auto";
  const editing = cur.startsWith("custom:") ? cur.slice(7) : "";
  themeDraft = { ...currentThemeColors() };
  $("#theme-name").value = editing;
  $("#theme-delete").hidden = !editing;
  const grid = $("#theme-colors");
  grid.innerHTML = "";
  for (const v of THEME_VARS) {
    const el = document.createElement("label");
    el.className = "color";
    el.innerHTML = `<i style="background:${themeDraft[v]}"></i><div><b style="font-weight:500">${t("tvar." + v)}</b><code>${themeDraft[v].toUpperCase()}</code></div><input type="color" value="${themeDraft[v]}" aria-label="${t("tvar." + v)}">`;
    const input = $("input", el);
    input.addEventListener("input", () => {
      themeDraft[v] = input.value;
      $("i", el).style.background = input.value;
      $("code", el).textContent = input.value.toUpperCase();
      paintTheme(themeDraft);
    });
    grid.appendChild(el);
  }
  $("#theme-editor").hidden = false;
  paintTheme(themeDraft);
}
function closeThemeEditor() {
  if ($("#theme-editor").hidden) return;
  $("#theme-editor").hidden = true;
  themeDraft = null;
  applyTheme();
}
function bindThemes() {
  $("#theme-new").addEventListener("click", () => ($("#theme-editor").hidden ? openThemeEditor() : closeThemeEditor()));
  $("#theme-cancel").addEventListener("click", closeThemeEditor);
  $("#theme-save").addEventListener("click", async () => {
    const name = $("#theme-name").value.trim() || t("theme.mine");
    S.themes = await api.save_theme(name, themeDraft);
    themeDraft = null;
    $("#theme-editor").hidden = true;
    await setSetting("ui.theme", "custom:" + name);
    renderThemes();
  });
  $("#theme-delete").addEventListener("click", async () => {
    const name = $("#theme-name").value.trim();
    S.themes = await api.delete_theme(name);
    themeDraft = null;
    $("#theme-editor").hidden = true;
    await setSetting("ui.theme", "auto");
    renderThemes();
  });
  if (window.matchMedia) window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => { if (((S.settings.ui || {}).theme || "auto") === "auto") applyTheme(); });
}
