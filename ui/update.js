"use strict";
// Update button (next to the version), the Updates card in Advanced and the update window.

const U = { last: null, asking: false };

function renderUpdate(u) {
  if (!u) return;
  U.last = u;
  const b = $("#upd");
  const on = u.state === "available";
  const busy = u.state === "downloading" || u.state === "installing";
  b.classList.toggle("on", on);
  b.classList.toggle("busy", busy);
  b.title = on ? t("upd.tip_on", { v: u.version }) : busy ? updText(u) : t("upd.tip_off");
  $("#version").textContent = busy && u.state === "downloading" ? `${Math.round(u.progress * 100)}%` : S.init.version;
  $("#upd-status").textContent = updText(u);
  const skip = (S.settings.updates || {}).skip;
  const sk = $("#upd-skip");
  sk.hidden = !skip;
  if (skip) { sk.innerHTML = `${esc(t("upd.skipping", { v: skip }))} <a href="#" id="upd-unskip">${t("upd.unskip")}</a>`; $("#upd-unskip").onclick = async e => { e.preventDefault(); await api.update_unskip(); S.settings.updates.skip = ""; renderUpdate(U.last); checkUpdate(true); }; }
  const bar = $("#upd-dl i");
  if (bar) bar.style.width = `${Math.round((u.progress || 0) * 100)}%`;
  const msg = $("#upd-dl-msg");
  if (msg) msg.textContent = updText(u);
}

function updText(u) {
  switch (u.state) {
    case "checking": return t("upd.checking");
    case "available": return u.error && U.tried ? t("upd.failed", { e: u.error }) : t("upd.available", { v: u.version });
    case "downloading": return t("upd.downloading", { p: Math.round((u.progress || 0) * 100) });
    case "installing": return t("upd.installing");
    default:
      if (u.error) return t("upd.offline");
      if (!u.checked_at) return t("upd.never");
      return t("upd.latest", { v: S.init.version }) + " " + t("upd.checked", { t: fmtWhen(u.checked_at) });
  }
}

async function checkUpdate(quiet) {
  $("#upd-status").textContent = t("upd.checking");
  const u = await api.update_check();
  renderUpdate(u);
  if (u && u.state === "available") askUpdate();
  else if (!quiet && u) toast(u.error ? t("upd.offline") : t("upd.latest", { v: S.init.version }));
}

function askUpdate() {
  const u = U.last;
  if (!u || u.state !== "available") return;
  openModal({ title: t("upd.ask_title", { v: u.version }), body: `<p class="hint">${esc(t("upd.ask"))}</p>`, buttons: [
    { label: t("upd.page"), onClick: () => { api.open_release_page(); return false; } },
    { label: t("upd.later") },
    { label: t("upd.go"), primary: true, onClick: () => { startUpdate(); return false; } }] });
}

async function startUpdate() {
  U.tried = true;
  const ok = await api.update_install();
  if (!ok) { closeModal(); toast(t("upd.offline")); return; }
  startWatch(U.last.version);
}

function startWatch(version) {
  const body = document.createElement("div");
  body.innerHTML = `<p id="upd-dl-msg" class="hint">${t("upd.downloading", { p: 0 })}</p><div class="upd-bar" id="upd-dl"><i></i></div>`;
  openModal({ title: t("upd.ask_title", { v: version }), body, buttons: [] });
  const watch = async () => {
    let u;
    try { u = (await api.state(S.frameNo)).update; } catch (e) { return; }   // Tela! is closing for the setup
    if (!u) { setTimeout(watch, 400); return; }
    renderUpdate(u);
    if (u.error && u.state !== "downloading" && u.state !== "installing") {
      openModal({ title: t("upd.title"), body: `<p>${esc(t("upd.failed", { e: u.error }))}</p>`, buttons: [
        { label: t("upd.page"), onClick: () => { api.open_release_page(); return false; } },
        { label: t("modal.close"), primary: true }] });
      return;
    }
    setTimeout(watch, 400);
  };
  watch();
}

function bindUpdate() {
  $("#upd").addEventListener("click", () => {
    const u = U.last || {};
    if (u.state === "available") askUpdate();
    else if (u.state !== "downloading" && u.state !== "installing") checkUpdate(false);
  });
  $("#upd-check").addEventListener("click", () => checkUpdate(false));
  $("#upd-back").addEventListener("click", showReleases);
  $("#cl-btn").addEventListener("click", showChangelog);
}

async function showReleases() {
  const body = document.createElement("div");
  body.innerHTML = `<p class="hint">${t("upd.loading")}</p>`;
  openModal({ title: t("upd.back_title"), desc: t("upd.back_desc"), body, buttons: [{ label: t("modal.close"), primary: true }] });
  const r = await api.update_releases();
  if (!r || r.error) { body.innerHTML = `<p class="hint">${t("upd.offline")}</p>`; return; }
  body.innerHTML = `<div class="rel-list"></div><label class="chk"><input type="checkbox" id="rel-skip" checked> ${esc(t("upd.skip_this", { v: r.current }))}</label>`;
  const list = $(".rel-list", body);
  for (const rel of r.releases) {
    const row = document.createElement("div");
    row.className = "prof";
    const cur = rel.version === r.current;
    const mb = rel.size ? ` · ${num(rel.size / 1048576, 1)} MB` : "";   // download size of that version's setup
    row.innerHTML = `<b>Tela! ${esc(rel.version)}</b><small>${esc(rel.date || "")}${mb}${rel.test ? " · " + t("upd.test_tag") : ""}${cur ? " · " + t("upd.installed") : ""}</small>`;
    if (!cur) {
      const b = document.createElement("button");
      b.className = "btn"; b.textContent = t("upd.install_this");
      b.addEventListener("click", async () => {
        const ok = await api.update_install_version(rel.version, $("#rel-skip").checked);
        if (!ok) { toast(t("upd.offline")); return; }
        U.tried = true; U.last = { ...(U.last || {}), version: rel.version, state: "downloading", progress: 0 };
        startWatch(rel.version);
      });
      row.appendChild(b);
    }
    list.appendChild(row);
  }
}
