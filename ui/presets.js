"use strict";
// Performance presets and profiles (Settings › Preset and profiles).

async function refreshPreset() {
  let p = "custom";
  try { p = await api.preset(); } catch (e) { /* keep the last one */ }
  $$("#presets button").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.p === p)));
}

async function applyPreset(name) {
  const settings = await api.preset_apply(name);
  if (settings) { S.settings = settings; syncControls(); renderNight(); }
  await refreshPreset();
  toast(t("pre.applied"));
}

async function renderProfiles() {
  const list = await api.profiles();
  const box = $("#profiles");
  box.innerHTML = "";
  for (const p of list) {
    const row = document.createElement("div");
    row.className = "prof";
    const when = p.created ? fmtWhen(p.created) : "";
    row.innerHTML = `<b>${esc(p.name)}</b><small>${when}${p.layouts && p.layouts.length ? " · " + t("prof.layouts") : ""}</small>
      <button class="btn" data-a="load">${t("prof.load")}</button><button class="btn" data-a="export">${t("prof.export")}</button><button class="btn danger" data-a="delete">${t("prof.delete")}</button>`;
    row.querySelector("[data-a=load]").addEventListener("click", () => openModal({
      title: t("prof.title"), body: `<p>${esc(t("prof.confirm_load", { n: p.name }))}</p>`, buttons: [
        { label: t("modal.cancel") },
        { label: t("prof.load"), primary: true, onClick: async () => {
          const r = await api.profile_load(p.name);
          if (r && r.settings) { S.settings = r.settings; applyTheme(); syncControls(); renderNight(); renderHistoryFolder(); E.lay = null; }
          await refreshPreset(); toast(t("prof.loaded"));
        } }] }));
    row.querySelector("[data-a=export]").addEventListener("click", async () => { if (await api.profile_export(p.name)) toast(t("prof.exported")); });
    row.querySelector("[data-a=delete]").addEventListener("click", () => openModal({
      title: t("prof.title"), body: `<p>${esc(t("prof.confirm_del", { n: p.name }))}</p>`, buttons: [
        { label: t("modal.cancel") },
        { label: t("prof.delete"), danger: true, onClick: async () => { await api.profile_delete(p.name); renderProfiles(); } }] }));
    box.appendChild(row);
  }
}

function saveProfile() {
  const body = document.createElement("div");
  body.innerHTML = `<input class="txt" type="text" maxlength="60" placeholder="${t("prof.name")}" style="width:100%">`;
  const input = $("input", body);
  const save = async () => {
    const name = input.value.trim();
    if (!name) { input.focus(); return false; }
    await api.profile_save(name);
    await renderProfiles();
    toast(t("prof.saved"));
  };
  input.addEventListener("keydown", e => { if (e.key === "Enter") { save().then(ok => { if (ok !== false) closeModal(); }); } });
  openModal({ title: t("prof.save"), body, buttons: [{ label: t("modal.cancel") }, { label: t("prof.save"), primary: true, onClick: save }] });
  setTimeout(() => input.focus(), 50);
}

function bindPresets() {
  $$("#presets button").forEach(b => b.addEventListener("click", () => { if (b.dataset.p !== "custom") applyPreset(b.dataset.p); }));
  $("#prof-new").addEventListener("click", saveProfile);
  $("#prof-import").addEventListener("click", async () => {
    const r = await api.profile_import();
    if (!r) return;
    if (r.error) { toast(t("prof.bad")); return; }
    await renderProfiles(); toast(t("prof.imported"));
  });
  $("#peek-btn").addEventListener("click", async () => { await api.preview_peek(60); S.frameNo = -1; });
  refreshPreset();
  renderProfiles();
}
