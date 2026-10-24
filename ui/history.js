"use strict";
// Game history: list of saved games, details with the FPS graph, delete, export.

const H = { games: [], folder: "" };

function fmtWhen(ts) {
  const d = new Date((ts || 0) * 1000);
  return d.toLocaleString(S.lang === "pt" ? "pt-BR" : S.lang === "zh" ? "zh-CN" : S.lang === "es" ? "es-ES" : "en-US",
    { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
}
const r0 = v => (v == null ? "--" : num(Math.round(v)));

const H_VIEW = { view: "games", compare: false, sel: [] };
const fmtHours = sec => {
  const m = Math.round((sec || 0) / 60);
  return m >= 60 ? `${Math.floor(m / 60)} h ${String(m % 60).padStart(2, "0")} min` : `${m} min`;
};
function gameIcon(name) {
  const src = (H.icons || {})[name || ""];
  return src ? `<img class="hist-ico" src="${src}" alt="">` : `<span class="hist-ico none"></span>`;
}

async function showHistory(keep) {
  const res = await api.history_list();
  H.games = res.games || [];
  H.per = res.per_game || [];
  H.icons = res.icons || {};
  H.folder = res.folder || "";
  if (!keep) { H_VIEW.compare = false; H_VIEW.sel = []; }
  const wrap = document.createElement("div");
  wrap.className = "hist";
  wrap.innerHTML = `<div class="hist-top"><div class="seg" role="group"><button data-v="games">${t("hist.v_games")}</button><button data-v="per">${t("hist.v_per")}</button></div>
    <input class="txt" type="search" placeholder="${t("hist.search")}"><small class="hint"></small></div>
    <div class="hist-cmp-bar" hidden><span></span><button class="btn pri" disabled>${t("hist.cmp_go")}</button></div>
    <div class="hist-list"></div>`;
  const list = $(".hist-list", wrap), hint = $(".hint", wrap), search = $("input", wrap);
  const bar = $(".hist-cmp-bar", wrap);
  const paint = () => {
    $$(".seg button", wrap).forEach(b => b.setAttribute("aria-pressed", String(b.dataset.v === H_VIEW.view)));
    list.innerHTML = "";
    bar.hidden = !(H_VIEW.compare && H_VIEW.view === "games");
    $("span", bar).textContent = t("hist.cmp_pick", { n: H_VIEW.sel.length });
    $("button", bar).disabled = H_VIEW.sel.length !== 2;
    if (H_VIEW.view === "per") {
      hint.textContent = t("hist.count_games", { n: H.per.length });
      if (!H.per.length) list.innerHTML = `<p class="hint">${t("hist.empty")}</p>`;
      for (const a of H.per) {
        const b = document.createElement("button");
        b.className = "hist-row per";
        b.dataset.q = String(a.name || "").toLowerCase();
        b.innerHTML = `${gameIcon(a.name)}<b>${esc(a.name)}</b><span>${t("hist.sessions", { n: a.count })} · ${fmtHours(a.seconds)}</span>
          <span class="val">${r0(a.fps_avg)} <small>${t("home.fps_avg")}</small> · ${r0(a.fps_1low)} <small>1% LOW</small></span>`;
        b.title = t("hist.per_tip", { best: r0(a.best_avg), cpu: r0((a.max || {}).cpu), gpu: r0((a.max || {}).gpu) });
        b.addEventListener("click", () => { H_VIEW.view = "games"; search.value = a.name; paint(); filter(); });
        list.appendChild(b);
      }
    } else {
      hint.textContent = t("hist.count", { n: H.games.length });
      if (!H.games.length) list.innerHTML = `<p class="hint">${t("hist.empty")}</p>`;
      for (const g of H.games) {
        const b = document.createElement("button");
        b.className = "hist-row" + (H_VIEW.compare ? " pick" : "") + (H_VIEW.sel.includes(g.id) ? " on" : "");
        b.dataset.q = String(g.name || "").toLowerCase();
        b.innerHTML = `${gameIcon(g.name)}<b>${esc(g.name || "?")}</b><span>${fmtWhen(g.ended_at)}</span><span>${esc(g.duration || "")}</span>
          <span class="val">${r0(g.fps_avg)} <small>${t("home.fps_avg")}</small> · ${r0(g.fps_1low)} <small>1% LOW</small></span>`;
        b.addEventListener("click", () => {
          if (!H_VIEW.compare) { showGame(g.id); return; }
          const i = H_VIEW.sel.indexOf(g.id);
          if (i >= 0) H_VIEW.sel.splice(i, 1);
          else { H_VIEW.sel.push(g.id); if (H_VIEW.sel.length > 2) H_VIEW.sel.shift(); }
          paint(); filter();
        });
        list.appendChild(b);
      }
    }
  };
  const filter = () => {
    const q = search.value.trim().toLowerCase();
    $$(".hist-row", list).forEach(r => { r.hidden = q && !r.dataset.q.includes(q); });
  };
  $$(".seg button", wrap).forEach(b => b.addEventListener("click", () => { H_VIEW.view = b.dataset.v; paint(); filter(); }));
  search.addEventListener("input", filter);
  $("button", bar).addEventListener("click", () => compareGames(H_VIEW.sel[0], H_VIEW.sel[1]));
  paint();
  const buttons = [
    { label: t("hist.export"), onClick: async () => { const p = await api.history_export(); if (p) toast(t("hist.exported")); return false; } },
    { label: t("hist.open_folder"), onClick: () => { api.history_folder(); return false; } },
  ];
  if (H.games.length > 1) buttons.push({ label: t("hist.compare"), onClick: el => {
    H_VIEW.compare = !H_VIEW.compare; H_VIEW.sel = []; H_VIEW.view = "games"; paint(); filter();
    el.textContent = H_VIEW.compare ? t("modal.cancel") : t("hist.compare");
    return false; } });
  if (H.games.length) buttons.push({ label: t("hist.delete_all"), danger: true, onClick: () => { confirmDeleteAll(); return false; } });
  buttons.push({ label: t("modal.close"), primary: true });
  openModal({ title: t("hist.title"), desc: H.folder, body: wrap, buttons });
}

function confirmDeleteAll() {
  openModal({ title: t("hist.title"), body: `<p>${t("hist.confirm_all", { n: H.games.length })}</p>`, buttons: [
    { label: t("modal.cancel"), onClick: () => { showHistory(); return false; } },
    { label: t("hist.delete_all"), danger: true, onClick: async () => { await api.history_delete(H.games.map(g => g.id)); showHistory(); return false; } }] });
}

async function showGame(id) {
  const g = await api.history_get(id);
  if (!g) { showHistory(); return; }
  const m = g.max || {};
  const body = document.createElement("div");
  body.className = "hist-game";
  body.innerHTML = `<div class="stats six">
      <div><span>${t("home.fps_avg")}</span><b>${r0(g.fps_avg)}</b></div><div><span>1% LOW</span><b>${r0(g.fps_1low)}</b></div>
      <div><span>${t("hist.fps_max")}</span><b>${r0(g.fps_max)}</b></div><div><span>${t("home.cpu_max")}</span><b>${r0(m.cpu)}°</b></div>
      <div><span>${t("hist.gpu_max")}</span><b>${r0(m.gpu)}°</b></div><div><span>${t("hist.hot_max")}</span><b>${r0(m.hotspot)}°</b></div></div>
    <h4>${t("hist.fps_graph")}</h4><canvas class="hist-graph"></canvas>`;
  openModal({ title: g.name || "?", desc: `${fmtWhen(g.ended_at)} · ${g.duration || ""}`, body, buttons: [
    { label: t("hist.back"), onClick: () => { showHistory(true); return false; } },
    { label: t("hist.delete"), danger: true, onClick: async () => { await api.history_delete([id]); showHistory(); return false; } },
    { label: t("home.show"), primary: true, onClick: async () => { await api.history_show(id); toast(t("toast.sent")); return false; } }] });
  requestAnimationFrame(() => drawSeries($(".hist-graph", body), g.fps_series || []));
}

async function compareGames(a, b) {
  const [ga, gb] = await Promise.all([api.history_get(a), api.history_get(b)]);
  if (!ga || !gb) { showHistory(true); return; }
  // older first, so the difference reads as "what changed since"
  const [g1, g2] = (ga.ended_at || 0) <= (gb.ended_at || 0) ? [ga, gb] : [gb, ga];
  const rows = [
    ["home.fps_avg", g => g.fps_avg, 1, ""], ["1% LOW", g => g.fps_1low, 1, ""], ["hist.fps_max", g => g.fps_max, 1, ""],
    ["home.cpu_max", g => (g.max || {}).cpu, -1, "°"], ["hist.gpu_max", g => (g.max || {}).gpu, -1, "°"],
    ["hist.hot_max", g => (g.max || {}).hotspot, -1, "°"]];
  const diff = (v1, v2, better, unit) => {
    if (v1 == null || v2 == null) return "";
    const d = Math.round(v2 - v1);
    if (!d) return `<em>=</em>`;
    const pct = v1 ? ` (${d > 0 ? "+" : ""}${num(Math.round((v2 - v1) / v1 * 100))}%)` : "";
    return `<em class="${d * better > 0 ? "up" : "down"}">${d > 0 ? "+" : ""}${num(d)}${unit}${unit ? "" : pct}</em>`;
  };
  const head = g => `<div class="cmp-h">${gameIcon(g.name)}<span><b>${esc(g.name || "?")}</b><small>${fmtWhen(g.ended_at)} · ${esc(g.duration || "")}</small></span></div>`;
  const body = document.createElement("div");
  body.className = "hist-game hist-cmp";
  body.innerHTML = `<div class="cmp-heads"><i class="dot a"></i>${head(g1)}<i class="dot b"></i>${head(g2)}</div>
    <table class="cmp-t"><tr class="cmp-k"><th></th><td><i class="dot a"></i></td><td><i class="dot b"></i></td><td>Δ</td></tr>${rows.map(([k, f, better, unit]) => `<tr><th>${k.includes(".") ? t(k) : k}</th>
      <td>${r0(f(g1))}${f(g1) == null ? "" : unit}</td><td>${r0(f(g2))}${f(g2) == null ? "" : unit}</td><td>${diff(f(g1), f(g2), better, unit)}</td></tr>`).join("")}</table>
    <h4>${t("hist.fps_graph")}</h4><canvas class="hist-graph"></canvas><small class="hint">${t("hist.cmp_hint")}</small>`;
  openModal({ title: t("hist.cmp_title"), body, buttons: [
    { label: t("hist.back"), onClick: () => { showHistory(true); return false; } },
    { label: t("modal.close"), primary: true }] });
  requestAnimationFrame(() => drawSeries($(".hist-graph", body), g1.fps_series || [], g2.fps_series || []));
}

function drawSeries(cv, series, other) {
  const css = getComputedStyle(document.documentElement);
  const dpr = window.devicePixelRatio || 1;
  const W = cv.clientWidth || 600, Hh = 150;
  cv.width = W * dpr; cv.height = Hh * dpr; cv.style.height = Hh + "px";
  const c = cv.getContext("2d");
  c.scale(dpr, dpr);
  c.clearRect(0, 0, W, Hh);
  const all = [series, other || []];
  const vals = all.flat().filter(v => v != null);
  c.strokeStyle = css.getPropertyValue("--line"); c.lineWidth = 1;
  c.beginPath(); c.moveTo(0, Hh - 0.5); c.lineTo(W, Hh - 0.5); c.stroke();
  if (vals.length < 2) return;
  const max = Math.max(...vals) * 1.12 || 1;
  c.fillStyle = css.getPropertyValue("--muted"); c.font = "11px " + css.getPropertyValue("--f-mono");
  c.fillText(`${Math.round(max / 1.12)} FPS`, 4, 12);
  const colors = [css.getPropertyValue("--accent"), css.getPropertyValue("--warn") || "#e8a33d"];
  all.forEach((ser, k) => {
    if (ser.length < 2) return;
    const pts = ser.map((v, i) => [i * W / (ser.length - 1), Hh - 6 - ((v || 0) / max) * (Hh - 16)]);
    if (!other) {
      c.beginPath(); pts.forEach(([x, y], i) => (i ? c.lineTo(x, y) : c.moveTo(x, y)));
      c.lineTo(W, Hh); c.lineTo(0, Hh); c.closePath();
      c.globalAlpha = 0.15; c.fillStyle = colors[k]; c.fill(); c.globalAlpha = 1;
    }
    c.beginPath(); pts.forEach(([x, y], i) => (i ? c.lineTo(x, y) : c.moveTo(x, y)));
    c.strokeStyle = colors[k]; c.lineWidth = 1.6; c.stroke();
  });
}

function bindHistory() {
  $("#hist-open").addEventListener("click", showHistory);
  $("#hist-keep").addEventListener("change", e => changeKeep(e.target));
  $("#hist-choose").addEventListener("click", async () => {
    const f = await api.history_choose_folder();
    if (f) { (S.settings.history = S.settings.history || {}).folder = f; renderHistoryFolder(); toast(t("toast.saved")); }
  });
}
async function changeKeep(el) {
  const old = (S.settings.history || {}).keep ?? 15;
  let n = Math.round(Number(el.value));
  if (!isFinite(n) || n < 0) { el.value = old; return; }
  const apply = async () => {
    await api.history_set_keep(n);
    (S.settings.history = S.settings.history || {}).keep = n;
    el.value = n; toast(t("toast.saved"));
  };
  const count = await api.history_count();
  if (n > 0 && count > n) {
    openModal({ title: t("hist.title"), body: `<p>${t("hist.keep_confirm", { d: count - n, n })}</p>`, buttons: [
      { label: t("modal.cancel"), onClick: () => { el.value = old; } },
      { label: t("hist.keep_ok"), danger: true, onClick: apply }] });
  } else await apply();
}
function renderHistoryFolder() {
  const k = $("#hist-keep");
  if (k && document.activeElement !== k) k.value = (S.settings.history || {}).keep ?? 15;
  const f = (S.settings.history || {}).folder;
  $("#hist-folder").textContent = f || t("hist.default_folder");
}
