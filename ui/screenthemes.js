"use strict";
// Screen themes (Appearance): gallery with live pictures, preview on hover, save / import / export / restore.

const ST = { list: [], current: null, thumbs: {}, hover: null, token: 0, notice: false };

async function stLoad(thumbs = true) {
  try {
    const r = await api.theme_list();
    ST.list = r.themes || [];
    ST.current = r.current;
    ST.notice = !!r.notice;
  } catch (e) { return; }
  stRender();
  stNotice();
  if (typeof renderScreenThemes === "function") renderScreenThemes();
  if (thumbs) stThumbs();
}
async function stThumbs() {
  try { ST.thumbs = await api.theme_thumbs(); } catch (e) { return; }
  stRender();
}
const stCur = () => ST.list.find(x => x.id === ST.current) || null;
const stName = id => (ST.list.find(x => x.id === id) || {}).name || id || "";

function stHomeSelect() {   // Início › Tema: the same list, as a quick choice
  const sel = $("#home-theme");
  if (!sel || document.activeElement === sel) return;
  sel.innerHTML = ST.list.map(th => `<option value="${esc(th.id)}">${esc(th.name)}</option>`).join("");
  sel.value = ST.current || "";
  if (!sel.dataset.bound) { sel.dataset.bound = "1"; sel.addEventListener("change", () => stApply(sel.value)); }
}

function stRender() {
  stHomeSelect();
  const grid = $("#st-grid");
  if (!grid) return;
  grid.innerHTML = "";
  for (const th of ST.list) {
    const b = document.createElement("button");
    b.className = "st-item";
    b.setAttribute("aria-pressed", String(th.id === ST.current));
    const pic = ST.thumbs[th.id];
    const tags = [th.edited ? `<span class="tag">${t("st.edited")}</span>` : "", !th.builtin ? `<span class="tag">${t("st.yours")}</span>` : ""].join("");
    b.innerHTML = `<div class="thumb"${pic ? ` style="background-image:url('${pic}')"` : ""}></div><div class="nm"><span>${esc(th.name)}</span>${tags}</div>`;
    b.title = th.id === ST.current ? t("st.in_use") : t("st.click_to_use");
    b.addEventListener("mouseenter", () => stHover(th.id));
    b.addEventListener("focus", () => stHover(th.id));
    b.addEventListener("mouseleave", () => stHover(null));
    b.addEventListener("blur", () => stHover(null));
    b.addEventListener("click", () => stApply(th.id));
    grid.appendChild(b);
  }
  for (const id of ["#st-day", "#st-night"]) {   // theme by the time of day: the same list of themes
    const sel = $(id);
    if (!sel) continue;
    const want = ((S.settings.theme || {})[id === "#st-day" ? "day" : "night"]) || sel.dataset.default;
    sel.innerHTML = ST.list.map(x => `<option value="${esc(x.id)}">${esc(x.name)}</option>`).join("");
    sel.value = want;
  }
  const sch = $("#st-sched");
  if (sch) sch.classList.toggle("off", !(S.settings.theme || {}).schedule);
  const cur = stCur();
  $("#st-now").textContent = cur ? cur.name : "";
  const acts = $("#st-actions");
  acts.innerHTML = "";
  const add = (key, fn, cls = "") => {
    const el = document.createElement("button");
    el.className = "btn " + cls;
    el.textContent = t(key);
    el.addEventListener("click", fn);
    acts.appendChild(el);
  };
  add("st.edit", () => showTab("layout"));
  if (cur && cur.edited) add("st.restore", stRestore);
  if (cur && !cur.builtin) { add("st.rename", stRename); add("st.delete", stDelete, "danger"); }
}

async function stHover(id) {
  ST.hover = id;
  const token = ++ST.token;
  if (!id || id === ST.current) {
    $("#st-hint").textContent = "";
    stMirror();
    return;
  }
  $("#st-hint").textContent = t("st.previewing", { name: stName(id) });
  await new Promise(r => setTimeout(r, 140));   // passing over the grid quickly draws nothing
  if (token !== ST.token) return;
  let url = null;
  try { url = await api.theme_preview(id); } catch (e) { url = null; }
  if (token !== ST.token || !url) return;
  const img = new Image();
  img.onload = () => {
    if (token !== ST.token) return;
    const c = $("#st-canvas");
    if (c.width !== img.width || c.height !== img.height) { c.width = img.width; c.height = img.height; }
    c.getContext("2d").drawImage(img, 0, 0);
  };
  img.src = url;
}
function stMirror() {   // the screen as it is now, while no theme is being previewed
  if (ST.hover && ST.hover !== ST.current) return;
  const c = $("#st-canvas");
  if (c && S.tab === "screen" && typeof copyFrame === "function") copyFrame(c);
}

async function stApply(id) {
  if (id === ST.current) return;
  const r = await api.theme_apply(id);
  if (!r) return;
  ST.current = id;
  S.settings.colors = { ...(S.settings.colors || {}), ...r.colors };
  (S.settings.theme = S.settings.theme || {}).name = id;
  ST.notice = false;
  ST.hover = null;
  ST.token++;
  if (typeof E !== "undefined") E.lay = null;   // the layout editor loads the new theme's blocks
  stRender();
  stNotice();
  renderColors();
  renderScreenThemes();
  $("#st-hint").textContent = "";
  toast(t("st.applied", { name: stName(id) }));
  setTimeout(stThumbs, 2500);
}

function stAsk(title, desc, value, ok) {
  const box = document.createElement("div");
  box.innerHTML = `<input class="txt" maxlength="40" style="width:100%">`;
  const input = $("input", box);
  input.value = value || "";
  openModal({ title, desc, body: box, buttons: [
    { label: t("modal.cancel") },
    { label: t("st.ok"), primary: true, onClick: async () => { const v = input.value.trim(); if (!v) return false; await ok(v); } }] });
  setTimeout(() => { input.focus(); input.select(); }, 30);
  input.addEventListener("keydown", e => { if (e.key === "Enter") $("#modal-foot .pri").click(); });
}
function stSaveAs() {
  const cur = stCur();
  stAsk(t("st.save_title"), t("st.save_desc"), cur ? t("st.copy_of", { name: cur.name }) : "", async name => {
    const r = await api.theme_save_as(name);
    ST.list = r.themes; ST.current = r.current;
    const now = await api.theme_list();
    S.settings.colors = { ...(S.settings.colors || {}), ...((now.themes.find(x => x.id === now.current) || {}).colors || {}) };
    if (typeof E !== "undefined") E.lay = null;
    stRender(); stThumbs();
    toast(t("st.saved", { name }));
  });
}
function stNew() {
  stAsk(t("st.new_title"), t("st.new_desc"), "", async name => {
    const r = await api.theme_new(name);
    ST.list = r.themes; ST.current = r.current;
    if (typeof E !== "undefined") E.lay = null;
    stRender(); stThumbs();
    toast(t("st.saved", { name }));
    showTab("layout");
  });
}
function stRename() {
  const cur = stCur();
  if (!cur) return;
  stAsk(t("st.rename_title"), "", cur.name, async name => {
    const r = await api.theme_rename(cur.id, name);
    ST.list = r.themes;
    stRender();
    toast(t("toast.saved"));
  });
}
function stDelete() {
  const cur = stCur();
  if (!cur) return;
  openModal({ title: t("st.delete_title", { name: cur.name }), desc: t("st.delete_desc"), buttons: [
    { label: t("modal.cancel") },
    { label: t("st.delete"), danger: true, onClick: async () => {
      const r = await api.theme_delete(cur.id);
      ST.list = r.themes; ST.current = r.current;
      const th = stCur();
      if (th) S.settings.colors = { ...(S.settings.colors || {}), ...th.colors };
      if (typeof E !== "undefined") E.lay = null;
      stRender(); renderColors(); renderScreenThemes(); stThumbs();
    } }] });
}
function stRestore() {
  const cur = stCur();
  if (!cur) return;
  openModal({ title: t("st.restore_title", { name: cur.name }), desc: t("st.restore_desc"), buttons: [
    { label: t("modal.cancel") },
    { label: t("st.restore"), primary: true, onClick: async () => {
      const r = await api.theme_reset(cur.id);
      ST.list = r.themes;
      const th = stCur();
      if (th) S.settings.colors = { ...(S.settings.colors || {}), ...th.colors };
      if (typeof E !== "undefined") E.lay = null;
      stRender(); renderColors(); renderScreenThemes(); setTimeout(stThumbs, 1500);
      toast(t("st.restored"));
    } }] });
}
async function stImport() {
  let r;
  try { r = await api.theme_import(); } catch (e) { toast(t("st.import_error")); return; }
  if (!r) return;
  if (r.error) { toast(t("st.import_error")); return; }
  ST.list = r.themes;
  stRender(); stThumbs();
  toast(t("st.imported", { name: stName(r.imported) }));
}
async function stExport() {
  let path;
  try { path = await api.theme_export(null); } catch (e) { toast(t("st.export_error")); return; }
  if (path) toast(t("st.exported"));
}

// community gallery: themes shared by people (repository's "gallery" branch), imported with one click
async function stGallery(force) {
  const body = document.createElement("div");
  body.className = "gal";
  body.innerHTML = `<p class="hint">${t("gal.loading")}</p>`;
  let share = "";
  openModal({ title: t("gal.title"), desc: t("gal.desc"), body, buttons: [
    { label: t("gal.share"), onClick: () => { if (share) api.open_url(share); return false; } },
    { label: t("modal.close"), primary: true }] });
  const r = await api.gallery_list(!!force);
  share = r.share || "";
  if (r.error) {
    body.innerHTML = `<p class="hint">${t("gal.offline")}</p>`;
    const again = document.createElement("button");
    again.className = "btn"; again.textContent = t("gal.retry");
    again.addEventListener("click", () => stGallery(true));
    body.appendChild(again);
    return;
  }
  if (!r.items.length) { body.innerHTML = `<p class="hint">${t("gal.empty")}</p>`; return; }
  body.innerHTML = `<div class="gal-grid"></div>`;
  const grid = $(".gal-grid", body);
  for (const it of r.items) {
    const card = document.createElement("div");
    card.className = "gal-item";
    card.innerHTML = `${it.picture ? `<img src="${it.picture}" alt="">` : `<div class="gal-none"></div>`}
      <div class="gal-meta"><b>${esc(it.name)}</b><small>${it.author ? esc(t("gal.by", { name: it.author })) : ""}</small></div>
      <div class="btns">${it.link ? `<button class="btn" data-a="post">${t("gal.post")}</button>` : ""}<button class="btn pri" data-a="get">${t("gal.import")}</button></div>`;
    const get = $("[data-a=get]", card);
    get.addEventListener("click", async () => {
      get.disabled = true; get.textContent = t("gal.importing");
      const res = await api.gallery_import(it.id).catch(() => ({ error: true }));
      if (!res || res.error) { get.disabled = false; get.textContent = t("gal.import"); toast(t("st.import_error")); return; }
      ST.list = res.themes;
      stRender(); stThumbs();
      get.textContent = t("gal.imported");
      toast(t("st.imported", { name: stName(res.imported) }));
    });
    const post = $("[data-a=post]", card);
    if (post) post.addEventListener("click", () => api.open_url(it.link));
    grid.appendChild(card);
  }
}

function stNotice() {
  const el = $("#st-notice");
  if (el) el.hidden = !ST.notice;
}

function bindScreenThemes() {
  $("#st-save").addEventListener("click", stSaveAs);
  $("#st-new").addEventListener("click", stNew);
  $("#st-import").addEventListener("click", stImport);
  $("#st-export").addEventListener("click", stExport);
  $("#st-gallery").addEventListener("click", () => stGallery(false));
  $("#st-notice-go").addEventListener("click", () => { ST.notice = false; stNotice(); api.theme_notice_seen(); showTab("screen"); });
  $("#st-notice-no").addEventListener("click", () => { ST.notice = false; stNotice(); api.theme_notice_seen(); });
  document.addEventListener("tela-frame", stMirror);
}

// a .tela-theme opened with a double click in Explorer (Tela.exe --import-theme)
async function stImported(id) {
  await stLoad();
  showTab("screen");
  toast(t("st.imported", { name: stName(id) }));
}
