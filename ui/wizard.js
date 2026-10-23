"use strict";
// First run: language and theme, screen connection, orientation, start with Windows.

const W = { step: 0, old: null };
const WIZ_STEPS = 4;

function wizNeeded() { return !(S.settings.ui || {}).wizard_done && !S.init.demo; }

async function wizStart() {
  W.step = 0;
  try { W.old = await api.old_install(); } catch (e) { W.old = null; }
  wizRender();
}
function wizFinish() {
  setSetting("ui.wizard_done", true, true);
  closeModal();
}
function wizRender() {
  const body = document.createElement("div");
  body.className = "wiz";
  const st = (S.state || {}).status || {};
  if (W.step === 0) {
    body.innerHTML = `<p class="hint">${t("wiz.lang")}</p><div class="wiz-langs"></div><p class="hint" style="margin-top:14px">${t("wiz.theme")}</p><div class="themes wiz-themes"></div>`;
    const langs = $(".wiz-langs", body);
    for (const l of ["auto", "pt", "en", "es", "zh"]) {
      const b = document.createElement("button");
      b.className = "btn";
      b.setAttribute("aria-pressed", String(((S.settings.ui || {}).language || "auto") === l));
      b.innerHTML = l === "auto" ? `<span class="auto-ic">A</span> ${t("lang.auto")}` : `${flagSvg(l).replace('class="flag"', 'class="flag sm"')} ${LANG_NAMES[l]}`;
      b.addEventListener("click", async () => { await setSetting("ui.language", l, true); wizRender(); });
      langs.appendChild(b);
    }
    const th = $(".wiz-themes", body);
    for (const [id, key, c] of [["auto", "theme.auto", null], ["light", "theme.light", THEME_PRESETS.light], ["dark", "theme.dark", THEME_PRESETS.black]]) {
      const b = document.createElement("button");
      b.className = "theme";
      b.setAttribute("aria-pressed", String(((S.settings.ui || {}).theme || "auto") === id));
      b.innerHTML = (c ? miniPreview(c) : `<div style="position:relative;height:54px"><div class="auto-split" style="inset:0">${miniPreview(THEME_PRESETS.light)}${miniPreview(THEME_PRESETS.black)}</div></div>`) + `<span>${t(key)}</span>`;
      b.addEventListener("click", async () => { await setSetting("ui.theme", id, true); renderThemes(); wizRender(); });
      th.appendChild(b);
    }
  } else if (W.step === 1) {
    const [kind, text] = screenState(st);
    body.innerHTML = `<p class="hint">${t("wiz.screen")}</p><div class="pills">${pill(kind, t("pill.screen"), text)}</div>
      <div class="field" style="margin-top:12px"><label>${t("set.port")}</label><select class="wiz-port"></select></div>
      <div class="btns" style="margin-top:12px"><button class="btn wiz-test">${t("home.test")}</button><button class="btn wiz-rescan">${t("set.rescan")}</button></div>
      <p class="hint" style="margin-top:12px">${t("wiz.screen_hint")}</p>
      <div class="wiz-conflict note warn" hidden><span></span><button class="btn">${t("conf.take")}</button></div>`;
    api.screen_apps().then(apps => {   // another screen program would keep the port busy
      const box = $(".wiz-conflict", body);
      if (!apps || !apps.length) return;
      $("span", box).textContent = t("conf.msg", { apps: apps.join(", ") });
      box.hidden = false;
      $("button", box).addEventListener("click", async () => { await api.close_conflict(); toast(t("conf.closed")); box.hidden = true; });
    }).catch(() => {});
    const sel = $(".wiz-port", body);
    const cur = getSetting("display.port") || "auto";
    for (const [v, label] of [["auto", t("port.auto")], ...S.init.ports.map(p => [p.device, `${p.device} · ${p.label}`])]) {
      const o = document.createElement("option"); o.value = v; o.textContent = label; sel.appendChild(o);
    }
    sel.value = cur;
    sel.addEventListener("change", () => setSetting("display.port", sel.value, true));
    $(".wiz-test", body).addEventListener("click", () => { api.command("test"); toast(t("toast.sent")); });
    $(".wiz-rescan", body).addEventListener("click", async () => { S.init.ports = await api.ports(); wizRender(); });
  } else if (W.step === 2) {
    body.innerHTML = `<p class="hint">${t("wiz.orientation")}</p><div class="wiz-shot"><canvas></canvas></div>
      <div class="seg wiz-orient" style="margin-top:12px"></div>`;
    copyFrame($("canvas", body));
    const seg = $(".wiz-orient", body);
    for (const o of ["landscape", "landscape_flipped", "portrait", "portrait_flipped"]) {
      const b = document.createElement("button");
      b.textContent = t("orient." + o);
      b.setAttribute("aria-pressed", String(getSetting("display.orientation") === o));
      b.addEventListener("click", async () => { await setSetting("display.orientation", o, true); wizRender(); });
      seg.appendChild(b);
    }
  } else {
    body.innerHTML = `<div class="row"><span class="lbl">${t("set.autostart")}<small>${t("wiz.autostart")}</small></span><button class="sw" role="switch" aria-checked="false"></button></div>
      ${W.old ? `<div class="card" style="margin-top:14px"><p>${t("wiz.old")}</p><pre>${esc(W.old)}</pre><div class="btns"><button class="btn danger wiz-old">${t("wiz.old_remove")}</button></div></div>` : ""}
      <p class="hint" style="margin-top:14px">${t("wiz.done")}</p>`;
    const sw = $(".sw", body);
    sw.setAttribute("aria-checked", $("#autostart").getAttribute("aria-checked"));
    sw.addEventListener("click", async () => {
      const want = sw.getAttribute("aria-checked") !== "true";
      sw.setAttribute("aria-checked", String(want));
      const real = await api.set_autostart(want);
      sw.setAttribute("aria-checked", String(!!real));
      $("#autostart").setAttribute("aria-checked", String(!!real));
    });
    const old = $(".wiz-old", body);
    if (old) old.addEventListener("click", async () => {
      old.disabled = true;
      const ok = await api.remove_old(W.old);
      old.textContent = ok ? t("wiz.old_removed") : t("wiz.old_failed");
    });
  }
  const buttons = [];
  if (W.step === 0) buttons.push({ label: t("wiz.skip"), onClick: () => { wizFinish(); return false; } });
  else buttons.push({ label: t("wiz.back"), onClick: () => { W.step--; wizRender(); return false; } });
  if (W.step < WIZ_STEPS - 1) buttons.push({ label: t("wiz.next"), primary: true, onClick: () => { W.step++; wizRender(); return false; } });
  else buttons.push({ label: t("wiz.finish"), primary: true, onClick: () => { wizFinish(); return false; } });
  openModal({ title: t("wiz.title" + W.step), desc: t("wiz.step", { n: W.step + 1, total: WIZ_STEPS }), body, buttons });
}
// keeps the connection step and the orientation picture live
setInterval(() => {
  if ($("#overlay").hidden || !$(".wiz") || W.step === 3) return;
  if (W.step === 1 || W.step === 2) {
    const shot = $(".wiz-shot canvas");
    if (shot) copyFrame(shot);
    if (W.step === 1) {
      const st = (S.state || {}).status || {};
      const [kind, text] = screenState(st);
      const p = $(".wiz .pills");
      if (p) p.innerHTML = pill(kind, t("pill.screen"), text);
    }
  }
}, 1000);
