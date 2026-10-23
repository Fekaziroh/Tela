"use strict";
// Game history: list of saved games, details with the FPS graph, delete, export.

const H = { games: [], folder: "" };

function fmtWhen(ts) {
  const d = new Date((ts || 0) * 1000);
  return d.toLocaleString(S.lang === "pt" ? "pt-BR" : S.lang === "zh" ? "zh-CN" : S.lang === "es" ? "es-ES" : "en-US",
    { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
}
const r0 = v => (v == null ? "--" : num(Math.round(v)));

async function showHistory() {
  const res = await api.history_list();
  H.games = res.games || [];
  H.folder = res.folder || "";
  const wrap = document.createElement("div");
  wrap.className = "hist";
  wrap.innerHTML = `<div class="search"><input class="txt" type="search" placeholder="${t("hist.search")}"><small class="hint">${t("hist.count", { n: H.games.length })}</small></div><div class="hist-list"></div>`;
  const list = $(".hist-list", wrap);
  if (!H.games.length) list.innerHTML = `<p class="hint">${t("hist.empty")}</p>`;
  for (const g of H.games) {
    const b = document.createElement("button");
    b.className = "hist-row";
    b.dataset.q = String(g.name || "").toLowerCase();
    b.innerHTML = `<b>${esc(g.name || "?")}</b><span>${fmtWhen(g.ended_at)}</span><span>${esc(g.duration || "")}</span>
      <span class="val">${r0(g.fps_avg)} <small>${t("home.fps_avg")}</small> · ${r0(g.fps_1low)} <small>1% LOW</small></span>`;
    b.addEventListener("click", () => showGame(g.id));
    list.appendChild(b);
  }
  $("input", wrap).addEventListener("input", e => {
    const q = e.target.value.trim().toLowerCase();
    $$(".hist-row", list).forEach(r => { r.hidden = q && !r.dataset.q.includes(q); });
  });
  const buttons = [
    { label: t("hist.export"), onClick: async el => { const p = await api.history_export(); if (p) toast(t("hist.exported")); return false; } },
    { label: t("hist.open_folder"), onClick: () => { api.history_folder(); return false; } },
  ];
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
    { label: t("hist.back"), onClick: () => { showHistory(); return false; } },
    { label: t("hist.delete"), danger: true, onClick: async () => { await api.history_delete([id]); showHistory(); return false; } },
    { label: t("home.show"), primary: true, onClick: async () => { await api.history_show(id); toast(t("toast.sent")); return false; } }] });
  requestAnimationFrame(() => drawSeries($(".hist-graph", body), g.fps_series || []));
}

function drawSeries(cv, series) {
  const css = getComputedStyle(document.documentElement);
  const dpr = window.devicePixelRatio || 1;
  const W = cv.clientWidth || 600, Hh = 150;
  cv.width = W * dpr; cv.height = Hh * dpr; cv.style.height = Hh + "px";
  const c = cv.getContext("2d");
  c.scale(dpr, dpr);
  c.clearRect(0, 0, W, Hh);
  const vals = series.filter(v => v != null);
  c.strokeStyle = css.getPropertyValue("--line"); c.lineWidth = 1;
  c.beginPath(); c.moveTo(0, Hh - 0.5); c.lineTo(W, Hh - 0.5); c.stroke();
  if (vals.length < 2) return;
  const max = Math.max(...vals) * 1.12 || 1;
  const pts = series.map((v, i) => [i * W / (series.length - 1), Hh - 6 - ((v || 0) / max) * (Hh - 16)]);
  c.fillStyle = css.getPropertyValue("--muted"); c.font = "11px " + css.getPropertyValue("--f-mono");
  c.fillText(`${Math.round(max / 1.12)} FPS`, 4, 12);
  c.beginPath(); pts.forEach(([x, y], i) => (i ? c.lineTo(x, y) : c.moveTo(x, y)));
  c.lineTo(W, Hh); c.lineTo(0, Hh); c.closePath();
  c.globalAlpha = 0.15; c.fillStyle = css.getPropertyValue("--accent"); c.fill(); c.globalAlpha = 1;
  c.beginPath(); pts.forEach(([x, y], i) => (i ? c.lineTo(x, y) : c.moveTo(x, y)));
  c.strokeStyle = css.getPropertyValue("--accent"); c.lineWidth = 1.6; c.stroke();
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
