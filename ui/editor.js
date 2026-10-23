"use strict";
// Layout editor: blocks on the preview can be selected, moved and resized; their items are edited on the side.

const E = { lay: null, groups: [], sel: null, multi: new Set(), open: null, item: null, boxes: {}, undo: [], W: 480, H: 320, timer: null, loading: false, boxTimer: null };
const FONTS = ["", "segoe", "arial", "verdana", "trebuchet", "georgia", "consolas", "impact"];
const ROTATIONS = [0, 90, 180, 270];
const SENSOR_TYPES = ["value", "bar", "gauge", "graph"];
const CLOCK_FORMATS = ["%H:%M", "%H:%M:%S", "{weekday} %d/%m", "%d/%m/%Y"];
const PROGRESS_MODES = ["bottom", "below_title", "beside_artist", "none"];

function blockName(g) {
  const n = String(g.name || g.id);
  return n.startsWith("#") ? t("block." + n.slice(1)) : n;
}
function sensorLabel(name) {
  const k = "sensor." + name;
  const s = t(k);
  return s === k ? name : s;
}
function fmtVal(v) { return v == null ? "--" : num(v, Math.abs(v) < 10 ? 1 : 0); }
function selGroup() { return E.groups.find(g => g.id === E.sel) || null; }
function snap(v) { return Math.round(v / 2) * 2; }

async function edLoad() {
  if (E.loading) return;
  E.loading = true;
  try {
    E.lay = await api.layout_get();
    E.groups = E.lay.groups;
    [E.W, E.H] = E.lay.size;
    if (!selGroup()) { E.sel = null; E.item = null; }
    edRender();
    edBoxes();
  } finally { E.loading = false; }
}
function edSave(pushUndo = true) {
  if (pushUndo) { /* undo snapshot is taken before the change by edChange */ }
  clearTimeout(E.timer);
  E.timer = setTimeout(async () => { await api.layout_save(E.groups); E.lay.custom = true; }, 250);
}
function edChange(fn) {
  E.undo.push(JSON.stringify(E.groups));
  if (E.undo.length > 40) E.undo.shift();
  fn();
  edSave();
  edRender();
  edBoxes();
}
// element rectangles on the screen, measured by the app (texts and values get their real size)
function edBoxes() {
  clearTimeout(E.boxTimer);
  E.boxTimer = setTimeout(async () => {
    try { E.boxes = await api.layout_boxes(E.groups); } catch (e) { E.boxes = {}; }
    edRenderBoxes();
  }, 150);
}

// ------------------------------------------------------------------ stage (preview with draggable blocks)
function stageScale() { return $("#stage-img").clientWidth / E.W || 1; }
function edRenderBoxes() {
  const box = $("#stage-boxes");
  const sc = stageScale();
  box.innerHTML = "";
  for (const g of E.groups) {
    const el = document.createElement("div");
    el.className = "box" + (g.id === E.sel ? " sel" : "") + (E.multi.has(g.id) && g.id !== E.sel ? " sel2" : "") + (g.enabled === false ? " off" : "");
    Object.assign(el.style, { left: g.x * sc + "px", top: g.y * sc + "px", width: g.w * sc + "px", height: g.h * sc + "px" });
    el.dataset.id = g.id;
    el.innerHTML = `<span class="tag-b">${esc(blockName(g))}</span><i class="handle nw"></i><i class="handle ne"></i><i class="handle sw"></i><i class="handle se"></i>`;
    el.addEventListener("pointerdown", e => edPointer(e, g, el));
    box.appendChild(el);
  }
  const g = selGroup();
  const rects = g && E.boxes[g.id];
  if (g && rects && g.enabled !== false) {
    (g.items || []).forEach((it, i) => {
      const r = rects[i];
      if (!r || it.enabled === false || it.type === "panel") return;
      const el = document.createElement("div");
      el.className = "ibox" + (E.item === i ? " sel" : "");
      Object.assign(el.style, { left: r[0] * sc + "px", top: r[1] * sc + "px", width: Math.max(6, r[2] * sc) + "px", height: Math.max(6, r[3] * sc) + "px" });
      el.dataset.i = i;
      el.title = itemLabel(it).replace(/<[^>]+>/g, " ");
      el.innerHTML = `<i class="handle se"></i>`;
      el.addEventListener("pointerdown", e => itemPointer(e, g, i, el, r));
      box.appendChild(el);
    });
  }
  $("#ed-family").textContent = t(E.lay && E.lay.family === "portrait" ? "ed.portrait" : "ed.landscape") + ` · ${E.W}×${E.H}` + (E.lay && E.lay.custom ? " · " + t("ed.custom") : "");
}
function edPointer(e, g, el) {
  e.preventDefault();
  e.stopPropagation();
  if (e.shiftKey && !e.target.classList.contains("handle")) {   // Shift: add to / remove from the selection
    toggleMulti(g.id);
    return;
  }
  if (!E.multi.has(g.id)) E.multi.clear();
  if (E.sel !== g.id || E.item != null) { E.sel = g.id; E.open = null; E.item = null; edRender(); el = $(`#stage-boxes [data-id="${CSS.escape(g.id)}"]`); }
  const handle = e.target.classList.contains("handle") ? [...e.target.classList].find(c => c.length === 2) : null;
  const sc = stageScale();
  const start = { px: e.clientX, py: e.clientY, x: g.x, y: g.y, w: g.w, h: g.h };
  const snapshot = JSON.stringify(E.groups);
  const nbs = handle ? edgeNeighbours(g) : [];
  const others = handle ? [] : E.groups.filter(o => o !== g && E.multi.has(o.id)).map(o => ({ o, x: o.x, y: o.y }));
  const img = $("#stage-img");
  // the block's current picture travels with the mouse
  el.style.backgroundImage = `url("${img.toDataURL()}")`;   // one picture per drag, not per frame
  let moved = false;
  el.classList.add("drag");
  el.setPointerCapture(e.pointerId);
  const paint = () => {
    const fx = g.w / start.w, fy = g.h / start.h;
    el.style.backgroundSize = `${E.W * sc * fx}px ${E.H * sc * fy}px`;
    el.style.backgroundPosition = `${-start.x * sc * fx}px ${-start.y * sc * fy}px`;
    Object.assign(el.style, { left: g.x * sc + "px", top: g.y * sc + "px", width: g.w * sc + "px", height: g.h * sc + "px" });
    $("#ed-pos").textContent = `x ${Math.round(g.x)} · y ${Math.round(g.y)} · ${Math.round(g.w)}×${Math.round(g.h)}`;
  const sit = E.item != null ? (g.items || [])[E.item] : null;
  if (sit) $("#ed-pos").textContent = itemLegend(sit);   // the clicked element's name and position
  };
  paint();
  const move = ev => {
    const dx = (ev.clientX - start.px) / sc, dy = (ev.clientY - start.py) / sc;
    if (Math.abs(dx) + Math.abs(dy) > 1) moved = true;
    if (!handle) {
      g.x = Math.max(0, Math.min(E.W - g.w, snap(start.x + dx)));
      g.y = Math.max(0, Math.min(E.H - g.h, snap(start.y + dy)));
      for (const s of others) {   // the other selected blocks move together
        s.o.x = Math.max(0, Math.min(E.W - s.o.w, s.x + (g.x - start.x)));
        s.o.y = Math.max(0, Math.min(E.H - s.o.h, s.y + (g.y - start.y)));
        const oel = $(`#stage-boxes [data-id="${CSS.escape(s.o.id)}"]`);
        if (oel) Object.assign(oel.style, { left: s.o.x * sc + "px", top: s.o.y * sc + "px" });
      }
    } else {
      if (!g.base) g.base = [start.w, start.h];
      const keep = ev.shiftKey ? start.w / start.h : null;
      let x0 = start.x, y0 = start.y, x1 = start.x + start.w, y1 = start.y + start.h;
      if (handle.includes("w")) x0 = Math.max(0, Math.min(x1 - 16, snap(start.x + dx)));
      if (handle.includes("e")) x1 = Math.min(E.W, Math.max(x0 + 16, snap(x1 + dx)));
      if (handle.includes("n")) y0 = Math.max(0, Math.min(y1 - 16, snap(start.y + dy)));
      if (handle.includes("s")) y1 = Math.min(E.H, Math.max(y0 + 16, snap(y1 + dy)));
      if (keep) {   // Shift keeps the proportions
        const w = x1 - x0, h = Math.max(16, Math.round(w / keep));
        if (handle.includes("n")) y0 = y1 - h; else y1 = y0 + h;
      }
      Object.assign(g, { x: x0, y: y0, w: x1 - x0, h: y1 - y0 });
      reflowResize(g, handle, nbs);
      for (const s of nbs) {
        const nel = $(`#stage-boxes [data-id="${CSS.escape(s.n.id)}"]`);
        if (nel) Object.assign(nel.style, { left: s.n.x * sc + "px", top: s.n.y * sc + "px", width: s.n.w * sc + "px", height: s.n.h * sc + "px" });
      }
    }
    paint();
  };
  const up = () => {
    el.removeEventListener("pointermove", move);
    el.removeEventListener("pointerup", up);
    el.removeEventListener("pointercancel", up);
    el.classList.remove("drag");
    if (moved) {
      E.undo.push(snapshot);
      edSave();
      edRender();
      edBoxes();
    } else {
      el.style.backgroundImage = "";
    }
  };
  el.addEventListener("pointermove", move);
  el.addEventListener("pointerup", up);
  el.addEventListener("pointercancel", up);
}

// ------------------------------------------------------------------ side panels
function edRender() {
  if (!E.lay) return;
  if (E.paletteLang !== S.lang) { E.paletteLang = S.lang; renderPalette(); }   // follows the window language
  const img = $("#stage-img");
  img.style.aspectRatio = `${E.W} / ${E.H}`;
  edRenderBoxes();
  // block list
  const list = $("#ed-blocks");
  list.innerHTML = "";
  for (const g of E.groups) {
    const row = document.createElement("div");
    row.className = "row" + (g.id === E.sel || E.multi.has(g.id) ? " on" : "");
    row.innerHTML = `<span class="lbl">${esc(blockName(g))} <small>${Math.round(g.w)}×${Math.round(g.h)}</small></span><button class="sw" role="switch" aria-checked="${g.enabled !== false}" aria-label="${esc(blockName(g))}"></button>`;
    row.addEventListener("click", e => {
      if (e.target.classList.contains("sw")) return;
      if (e.shiftKey) { toggleMulti(g.id); return; }
      E.multi.clear(); selectBlock(g.id);
    });
    $(".sw", row).addEventListener("click", () => edChange(() => { g.enabled = g.enabled === false; }));
    list.appendChild(row);
  }
  // selected block
  const g = selGroup();
  $("#ed-block").hidden = !g;
  $("#ed-multi").hidden = E.multi.size < 2;
  $("#ed-multi").textContent = t("ed.multi", { n: E.multi.size });
  if (!g) { $("#ed-pos").textContent = ""; return; }
  $("#ed-name").value = blockName(g);
  $("#ed-x").value = Math.round(g.x); $("#ed-y").value = Math.round(g.y);
  $("#ed-w").value = Math.round(g.w); $("#ed-h").value = Math.round(g.h);
  $("#ed-natural").hidden = !g.base || (g.base[0] === g.w && g.base[1] === g.h);
  $("#ed-pos").textContent = `x ${Math.round(g.x)} · y ${Math.round(g.y)} · ${Math.round(g.w)}×${Math.round(g.h)}`;
  edRenderItems(g);
}
function itemLabel(it) {
  const typeName = t("item." + it.type);
  if (SENSOR_TYPES.includes(it.type)) return `${typeName} <small>${esc(sensorLabel(it.sensor || ""))}</small>`;
  if (it.type === "text") return `${typeName} <small>${esc(String(it.text || "").replace(/^#/, ""))}</small>`;
  if (it.type === "panel") return `${typeName} <small>${esc(String(it.title || "").replace(/^#/, ""))}</small>`;
  const when = [].concat(it.when || []);
  if (it.type === "media") return `${typeName} <small>${t(when.includes("media_in_game") ? "idesc.media_game" : "idesc.media_idle")}</small>`;
  if (it.type === "clock") {
    const i = CLOCK_FORMATS.indexOf(it.format || "%H:%M");
    return `${typeName} <small>${i >= 0 ? t("clock." + i) : esc(it.format || "")}</small>`;
  }
  if (it.type === "image") return `${typeName} <small>${t("idesc.logos")}</small>`;
  if (it.type === "frametime") return `${typeName} <small>${t("idesc.frametime")}</small>`;
  return typeName;
}
function sensorSelect(it) {
  const sel = document.createElement("select");
  const known = (E.lay.sensors || []);
  for (const s of known) {
    const o = document.createElement("option");
    o.value = s.name;
    o.textContent = `${sensorLabel(s.name)} (${fmtVal(s.value)})`;
    sel.appendChild(o);
  }
  if (it.sensor && !known.some(s => s.name === it.sensor)) {
    const o = document.createElement("option"); o.value = it.sensor; o.textContent = it.sensor; sel.appendChild(o);
  }
  const other = document.createElement("option");
  other.value = "__other__"; other.textContent = t("ed.other_sensor");
  sel.appendChild(other);
  sel.value = it.sensor || "";
  sel.addEventListener("change", () => {
    if (sel.value === "__other__") {
      sel.value = it.sensor || "";
      showSensors(async selector => {
        const name = await api.add_sensor(selector, E.groups);
        E.lay.sensors = await api.sensor_values();
        edChange(() => { it.sensor = name; });
      });
      return;
    }
    edChange(() => { it.sensor = sel.value; });
  });
  return sel;
}
function field(labelKey, input) {
  const f = document.createElement("div");
  f.className = "field";
  f.innerHTML = `<label>${t(labelKey)}</label>`;
  f.appendChild(input);
  return f;
}
function textInput(it, key) {
  const inp = document.createElement("input");
  inp.className = "txt";
  inp.value = it[key] == null ? "" : String(it[key]);
  inp.addEventListener("change", () => edChange(() => { it[key] = inp.value; }));
  return inp;
}
function numInput(it, key, step = 1) {
  const inp = document.createElement("input");
  inp.className = "num"; inp.type = "number"; inp.step = step;
  inp.value = it[key] == null ? "" : it[key];
  inp.addEventListener("change", () => {
    const v = Number(String(inp.value).replace(",", "."));
    edChange(() => { if (inp.value === "") delete it[key]; else if (isFinite(v)) it[key] = v; });
  });
  return inp;
}
function selectInput(it, key, options, labels) {
  const sel = document.createElement("select");
  options.forEach((v, i) => { const o = document.createElement("option"); o.value = v; o.textContent = labels[i]; sel.appendChild(o); });
  sel.value = it[key] ?? options[0];
  sel.addEventListener("change", () => edChange(() => { it[key] = sel.value; }));
  return sel;
}
function pair(a, b) { const d = document.createElement("div"); d.className = "two"; d.append(a, b); return d; }
function edItemFields(it) {
  const box = document.createElement("div");
  box.className = "fields";
  if (it.type === "panel") box.append(pair(field("ed.title", textInput(it, "title")), field("ed.subtitle", textInput(it, "subtitle"))));
  if (it.type === "text") box.append(field("ed.text", textInput(it, "text")));
  if (SENSOR_TYPES.includes(it.type)) box.append(field("ed.sensor", sensorSelect(it)));
  if (it.type === "value") box.append(pair(field("ed.unit", textInput(it, "unit")), field("ed.size", numInput(it, "size"))));
  if (it.type === "bar" || it.type === "gauge") box.append(pair(field("ed.min", numInput(it, "min")), field("ed.max", numInput(it, "max"))));
  if (it.type === "frametime") {
    box.append(pair(field("ed.ft_seconds", numInput(it, "seconds", 0.5)), field("ed.ft_labels", selectInput(it, "labels", ["top", "right"], [t("ed.ft_top"), t("ed.ft_right")]))));
    const sw = (key, label) => {
      const s = document.createElement("button");
      s.className = "sw"; s.setAttribute("role", "switch"); s.setAttribute("aria-checked", String(it[key] !== false));
      s.addEventListener("click", () => edChange(() => { it[key] = it[key] === false; }));
      const row = document.createElement("div"); row.className = "row";
      row.innerHTML = `<span class="lbl">${t(label)}</span>`; row.appendChild(s);
      return row;
    };
    box.append(sw("show_ms", "ed.ft_ms"), sw("show_1low", "ed.ft_low"), field("ed.ft_size", numInput(it, "label_size")));
  }
  if (it.type === "clock") box.append(field("ed.format", selectInput(it, "format", CLOCK_FORMATS, CLOCK_FORMATS.map(f => t("clock." + CLOCK_FORMATS.indexOf(f))))));
  if (["text", "clock", "value", "gauge"].includes(it.type)) {
    const font = selectInput(it, "font", FONTS, FONTS.map(f => f ? f[0].toUpperCase() + f.slice(1) : t("ed.font_default")));
    font.addEventListener("change", () => { if (!font.value) edChange(() => { delete it.font; }); });
    const fbox = document.createElement("div"); fbox.className = "two";
    fbox.append(field("ed.font", font));
    if (it.type !== "value") fbox.append(field("ed.size", numInput(it, "size")));
    else fbox.append(field("ed.bold", (() => { const s = document.createElement("button"); s.className = "sw"; s.setAttribute("role", "switch"); s.setAttribute("aria-checked", String(!!it.bold)); s.addEventListener("click", () => edChange(() => { it.bold = !it.bold; })); return s; })()));
    box.append(fbox);
  }
  if (it.type === "media") {
    box.append(field("ed.progress", selectInput(it, "progress", PROGRESS_MODES, PROGRESS_MODES.map(m => t("progress." + m)))));
    const sw = document.createElement("button");
    sw.className = "sw"; sw.setAttribute("role", "switch"); sw.setAttribute("aria-checked", String(!!it.show_time));
    sw.addEventListener("click", () => edChange(() => { it.show_time = !it.show_time; }));
    const row = document.createElement("div"); row.className = "row";
    row.innerHTML = `<span class="lbl">${t("ed.show_time")}</span>`; row.appendChild(sw);
    box.append(row);
  }
  const posX = "x" in it ? "x" : "cx", posY = "y" in it ? "y" : "cy";
  box.append(pair(field("ed.pos_x", numInput(it, posX)), field("ed.pos_y", numInput(it, posY))));
  if ("w" in it) box.append(pair(field("ed.w", numInput(it, "w")), field("ed.h", numInput(it, "h"))));
  if ("radius" in it && it.type === "gauge") box.append(field("ed.radius", numInput(it, "radius")));
  const rot = document.createElement("div");
  rot.className = "rot";
  ROTATIONS.forEach(a => {
    const b = document.createElement("button");
    b.className = "btn" + ((Number(it.rotate) || 0) === a ? " pri" : "");
    b.textContent = a + "°";
    b.addEventListener("click", () => edChange(() => { if (a) it.rotate = a; else delete it.rotate; }));
    rot.appendChild(b);
  });
  const free = numInput(it, "rotate", 5);
  free.title = t("ed.rotate_free");
  rot.appendChild(free);
  box.append(field("ed.rotate", rot));
  return box;
}
function edRenderItems(g) {
  const box = $("#ed-items");
  box.innerHTML = "";
  (g.items || []).forEach((it, i) => {
    const el = document.createElement("div");
    el.className = "item-ed" + (it.enabled === false ? " off" : "") + (E.item === i ? " on" : "");
    el.innerHTML = `<div class="row"><span class="lbl">${itemLabel(it)}</span><span class="inline"><button class="sw" role="switch" aria-checked="${it.enabled !== false}"></button><button class="icon-btn" title="${t("ed.remove")}">✕</button></span></div>`;
    $(".lbl", el).addEventListener("click", () => { if (E.open === i) { E.open = null; E.item = null; edRender(); edRenderBoxes(); } else selectItem(i); });
    $(".sw", el).addEventListener("click", () => edChange(() => { it.enabled = it.enabled === false; }));
    $(".icon-btn", el).addEventListener("click", () => edChange(() => { g.items.splice(i, 1); E.open = null; E.item = null; }));
    if (E.open === i) el.appendChild(edItemFields(it));
    box.appendChild(el);
  });
}

// ------------------------------------------------------------------ actions
function bindEditor() {
  $("#ed-undo").addEventListener("click", () => {
    const last = E.undo.pop();
    if (!last) return;
    E.groups = JSON.parse(last);
    edSave();
    edRender();
  });
  $("#ed-reset").addEventListener("click", () => openModal({
    title: t("ed.reset_title"), body: `<p style="margin:0;color:var(--muted)">${t("ed.reset_body")}</p>`,
    buttons: [{ label: t("modal.cancel") }, { label: t("ed.reset"), danger: true, onClick: async () => {
      E.undo.push(JSON.stringify(E.groups));
      E.lay = await api.layout_reset(); E.groups = E.lay.groups; E.sel = null; edRender();
    } }],
  }));
  const menu = $("#ed-add-menu");
  $("#ed-add").addEventListener("click", e => {
    e.stopPropagation();
    menu.innerHTML = "";
    for (const k of (E.lay ? E.lay.kinds : [])) {
      const b = document.createElement("button");
      b.innerHTML = `${t("kind." + k)}<small>${t("kind." + k + "_d")}</small>`;
      b.addEventListener("click", async () => {
        menu.hidden = true;
        const g = await api.layout_new_block(k, 10, 10);
        g.x = snap(Math.max(0, (E.W - g.w) / 2)); g.y = snap(Math.max(0, (E.H - g.h) / 2));
        if (k === "text") g.items[0].text = t("kind.text");
        g.name = t("kind." + k);
        const panel = g.items.find(it => it.type === "panel");
        if (panel && k !== "usage") panel.title = sensorLabel(g.items[1] && g.items[1].sensor || "").split(" · ").pop().toUpperCase().slice(0, 14);
        edChange(() => { E.groups.push(g); E.sel = g.id; });
      });
      menu.appendChild(b);
    }
    menu.hidden = !menu.hidden;
  });
  document.addEventListener("click", e => { if (!menu.contains(e.target)) menu.hidden = true; });
  $("#ed-del").addEventListener("click", deleteSelectedBlocks);
  renderPalette();
  bindStageDrop();
  $("#ed-name").addEventListener("change", () => { const g = selGroup(); if (g) edChange(() => { g.name = $("#ed-name").value.trim() || g.name; }); });
  for (const k of ["x", "y", "w", "h"]) {
    $("#ed-" + k).addEventListener("change", () => {
      const g = selGroup(); if (!g) return;
      let v = Number($("#ed-" + k).value);
      if (!isFinite(v)) return;
      edChange(() => {
        if ((k === "w" || k === "h") && !g.base) g.base = [g.w, g.h];
        v = Math.max(k === "w" || k === "h" ? 16 : 0, v);
        if (k === "x") v = Math.min(v, E.W - g.w); if (k === "y") v = Math.min(v, E.H - g.h);
        if (k === "w") v = Math.min(v, E.W - g.x); if (k === "h") v = Math.min(v, E.H - g.y);
        g[k] = v;
      });
    });
  }
  $("#ed-natural").addEventListener("click", () => { const g = selGroup(); if (g && g.base) edChange(() => { [g.w, g.h] = g.base; g.x = Math.min(g.x, E.W - g.w); g.y = Math.min(g.y, E.H - g.h); }); });
  $("#ed-add-item").addEventListener("click", () => {
    const g = selGroup(); if (!g) return;
    const [bw, bh] = g.base || [g.w, g.h];
    const s = (E.lay.sensors[0] || {}).name || "cpu_temp";
    edChange(() => { g.items.push({ type: "value", sensor: s, x: Math.round(bw / 2), y: Math.round(bh / 2), size: 14 }); E.open = g.items.length - 1; });
  });
  document.addEventListener("keydown", e => {
    if (S.tab !== "layout" || (!E.sel && !E.multi.size) || /INPUT|SELECT|TEXTAREA/.test(document.activeElement.tagName)) return;
    if (!$("#overlay").hidden) return;
    const g = selGroup() || E.groups.find(o => E.multi.has(o.id));
    if (!g) return;
    const d = e.shiftKey ? 10 : 2;
    const mv = { ArrowLeft: [-d, 0], ArrowRight: [d, 0], ArrowUp: [0, -d], ArrowDown: [0, d] }[e.key];
    const it = E.item != null ? (g.items || [])[E.item] : null;
    if (it) {   // the selected element
      if (mv) {
        e.preventDefault();
        const px = "x" in it ? "x" : "cx", py = "y" in it ? "y" : "cy";
        const one = e.shiftKey ? 5 : 1;
        edChange(() => { it[px] = (it[px] || 0) + Math.sign(mv[0]) * one; it[py] = (it[py] || 0) + Math.sign(mv[1]) * one; });
      } else if (e.key === "Delete" || e.key === "Backspace") {
        e.preventDefault();
        edChange(() => { g.items.splice(E.item, 1); E.item = null; E.open = null; });
      } else if (e.key === "r" || e.key === "R") {
        edChange(() => { const a = ((Number(it.rotate) || 0) + 90) % 360; if (a) it.rotate = a; else delete it.rotate; });
      } else if (e.key === "Escape") { E.item = null; E.open = null; edRender(); edRenderBoxes(); }
      return;
    }
    if (e.key === "Delete" || e.key === "Backspace") { e.preventDefault(); deleteSelectedBlocks(); return; }
    if (e.key === "Escape") { clearSelection(); return; }
    if (mv) {
      e.preventDefault();
      const all = E.groups.filter(o => o === g || E.multi.has(o.id));
      edChange(() => all.forEach(o => { o.x = Math.max(0, Math.min(E.W - o.w, o.x + mv[0])); o.y = Math.max(0, Math.min(E.H - o.h, o.y + mv[1])); }));
    } else if ((e.key === "z" || e.key === "Z") && (e.ctrlKey || e.metaKey)) { e.preventDefault(); $("#ed-undo").click(); }
  });
  $("#stage").addEventListener("pointerdown", e => { if (e.target.id === "stage" || e.target.id === "stage-img" || e.target.id === "stage-boxes") clearSelection(); });
  window.addEventListener("resize", () => { if (S.tab === "layout") edRenderBoxes(); });
  setInterval(async () => {   // live values in the sensor lists
    if (S.tab !== "layout" || document.visibilityState !== "visible" || !E.lay || E.open == null) return;
    try { E.lay.sensors = await api.sensor_values(); } catch (e) { /* ignore */ }
  }, 3000);
}

// ------------------------------------------------------------------ elements (items) on the stage
function groupScale(g) {
  const [bw, bh] = g.base || [g.w, g.h];
  return { sx: g.w / bw, sy: g.h / bh, k: Math.min(g.w / bw, g.h / bh) };
}
function itemLegend(it) {
  const px = "x" in it ? "x" : "cx", py = "y" in it ? "y" : "cy";
  const name = itemLabel(it).replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
  return `${name} · x ${Math.round(it[px] || 0)} · y ${Math.round(it[py] || 0)}`;
}
function selectItem(i) {
  E.item = i; E.open = i;
  edRender(); edRenderBoxes();
  const el = $(`#ed-items .item-ed:nth-child(${i + 1})`);
  if (el) el.scrollIntoView({ block: "nearest" });
}
function itemPointer(e, g, i, el, r) {
  e.preventDefault(); e.stopPropagation();
  if (E.item !== i) { selectItem(i); el = $(`#stage-boxes .ibox[data-i="${i}"]`) || el; }
  const it = g.items[i];
  const resize = e.target.classList.contains("handle");
  const sc = stageScale();
  const { sx, sy, k } = groupScale(g);
  const px = "x" in it ? "x" : "cx", py = "y" in it ? "y" : "cy";
  const start = { cx: e.clientX, cy: e.clientY, x: it[px] || 0, y: it[py] || 0, w: it.w, h: it.h, radius: it.radius,
                  size: it.size, unit: it.unit_size, rect: r.slice() };
  const snapshot = JSON.stringify(E.groups);
  let moved = false;
  el.setPointerCapture(e.pointerId);
  const move = ev => {
    const dx = (ev.clientX - start.cx) / sc, dy = (ev.clientY - start.cy) / sc;   // screen pixels
    if (Math.abs(dx) + Math.abs(dy) > 1) moved = true;
    if (!resize) {
      it[px] = Math.round(start.x + dx / sx); it[py] = Math.round(start.y + dy / sy);
      Object.assign(el.style, { left: (start.rect[0] + dx) * sc + "px", top: (start.rect[1] + dy) * sc + "px" });
    } else {
      const nw = Math.max(6, start.rect[2] + dx), nh = Math.max(6, start.rect[3] + dy);
      if (start.w != null && start.h != null) { it.w = Math.max(4, Math.round(start.w + dx / sx)); it.h = Math.max(2, Math.round(start.h + dy / sy)); }
      else if (it.type === "gauge") it.radius = Math.max(8, Math.round((start.radius || 30) + Math.max(dx, dy) / k / 2));
      else {
        const f = nh / start.rect[3];
        it.size = Math.max(6, Math.round((start.size || 14) * f));
        if (start.unit) it.unit_size = Math.max(5, Math.round(start.unit * f));
      }
      Object.assign(el.style, { width: nw * sc + "px", height: nh * sc + "px" });
    }
    $("#ed-pos").textContent = itemLegend(it);
  };
  const up = () => {
    el.removeEventListener("pointermove", move); el.removeEventListener("pointerup", up); el.removeEventListener("pointercancel", up);
    if (moved) { E.undo.push(snapshot); edSave(); edRender(); edBoxes(); }
  };
  el.addEventListener("pointermove", move); el.addEventListener("pointerup", up); el.addEventListener("pointercancel", up);
}

// palette: elements dragged onto the screen
const PALETTE = ["value", "bar", "gauge", "graph", "text", "clock", "media", "image", "frametime", "panel"];
function newItem(type, sensor) {
  const s = sensor || ((E.lay.sensors || [])[0] || {}).name || "cpu_temp";
  return {
    value: { type: "value", sensor: s, size: 16, bold: true },
    bar: { type: "bar", sensor: s, w: 80, h: 4, min: 0, max: 100 },
    gauge: { type: "gauge", sensor: s, radius: 28, thickness: 6, min: 0, max: 100, size: 18 },
    graph: { type: "graph", sensor: s, w: 120, h: 36, points: 60 },
    text: { type: "text", text: t("item.text"), size: 12 },
    clock: { type: "clock", format: "%H:%M", size: 20, bold: true },
    media: { type: "media", w: 170, h: 30, when: "media", progress: "bottom" },
    image: { type: "image", files: "logos", w: 90, h: 16 },
    frametime: { type: "frametime", w: 56, h: 14, seconds: 2 },
    panel: { type: "panel", w: 100, h: 60, title: "" },
  }[type];
}
function itemSize(it) {   // screen size of a new element, to center it where it was dropped
  if (it.type === "gauge") return [it.radius * 2, it.radius * 2];
  if (it.w) return [it.w, it.h];
  return [0, 0];
}
function placeItem(type, sx0, sy0) {
  const it = newItem(type);
  const [iw, ih] = itemSize(it);
  const hit = [...E.groups].reverse().find(g => g.enabled !== false && sx0 >= g.x && sx0 <= g.x + g.w && sy0 >= g.y && sy0 <= g.y + g.h);
  edChange(() => {
    let g = hit, i;
    if (!g) {   // dropped outside every block: a new block around it
      const bw = Math.max(40, iw + 16 || 120), bh = Math.max(24, ih + 16 || 30);
      g = { id: `${type}_${Date.now() % 100000}`, name: t("item." + type), x: snap(Math.max(0, Math.min(E.W - bw, sx0 - bw / 2))),
            y: snap(Math.max(0, Math.min(E.H - bh, sy0 - bh / 2))), w: bw, h: bh, items: [] };
      E.groups.push(g);
    }
    const { sx, sy } = groupScale(g);
    const rx = (sx0 - g.x) / sx, ry = (sy0 - g.y) / sy;
    if (it.type === "gauge") { it.cx = Math.round(rx); it.cy = Math.round(ry); }
    else if (it.w) { it.x = Math.round(rx - iw / 2); it.y = Math.round(ry - ih / 2); }
    else { it.x = Math.round(rx); it.y = Math.round(ry); }
    g.items.push(it);
    i = g.items.length - 1;
    E.sel = g.id; E.item = i; E.open = i;
  });
}
function renderPalette() {
  const box = $("#ed-palette");
  box.innerHTML = "";
  for (const type of PALETTE) {
    const b = document.createElement("button");
    b.className = "chip-el"; b.textContent = t("item." + type);
    b.title = t("ed.drag_hint");
    b.addEventListener("pointerdown", e => paletteDrag(e, b, type));
    box.appendChild(b);
  }
}
// pointer drag (works the same with mouse, pen and touch, and inside WebView2): a chip follows the cursor
function paletteDrag(e, chip, type) {
  e.preventDefault();
  const start = { x: e.clientX, y: e.clientY };
  const stage = $("#stage");
  let ghost = null;
  chip.setPointerCapture(e.pointerId);
  const over = ev => { const r = $("#stage-img").getBoundingClientRect(); return ev.clientX >= r.left && ev.clientX <= r.right && ev.clientY >= r.top && ev.clientY <= r.bottom ? r : null; };
  const move = ev => {
    if (!ghost && Math.abs(ev.clientX - start.x) + Math.abs(ev.clientY - start.y) > 4) {
      ghost = document.createElement("div"); ghost.className = "chip-el ghost"; ghost.textContent = chip.textContent;
      document.body.appendChild(ghost);
    }
    if (ghost) { ghost.style.left = ev.clientX + 8 + "px"; ghost.style.top = ev.clientY + 8 + "px"; stage.classList.toggle("drop", !!over(ev)); }
  };
  const up = ev => {
    chip.removeEventListener("pointermove", move); chip.removeEventListener("pointerup", up); chip.removeEventListener("pointercancel", up);
    stage.classList.remove("drop");
    if (ghost) {
      ghost.remove();
      const r = over(ev);
      if (r && ev.type === "pointerup") { const sc = stageScale(); placeItem(type, (ev.clientX - r.left) / sc, (ev.clientY - r.top) / sc); }
    } else {   // a click: add in the middle of the selected block (or of the screen)
      const g = selGroup();
      placeItem(type, g ? g.x + g.w / 2 : E.W / 2, g ? g.y + g.h / 2 : E.H / 2);
    }
  };
  chip.addEventListener("pointermove", move); chip.addEventListener("pointerup", up); chip.addEventListener("pointercancel", up);
}
function bindStageDrop() { /* the palette uses pointer drags (paletteDrag) */ }

// automatic re-flow: neighbours follow when a block is deleted or resized
const NEAR = 8;
function reflowOn() { return (S.settings.ui || {}).reflow !== false; }
function vOverlap(a, b) { return Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y); }
function hOverlap(a, b) { return Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x); }
function reflowDelete(gone) {
  if (!reflowOn()) return;
  const rest = E.groups.filter(g => g !== gone && g.enabled !== false);
  const inside = (n, horizontal) => horizontal ? n.y >= gone.y - NEAR && n.y + n.h <= gone.y + gone.h + NEAR && vOverlap(n, gone) > 0
                                               : n.x >= gone.x - NEAR && n.x + n.w <= gone.x + gone.w + NEAR && hOverlap(n, gone) > 0;
  const left = rest.filter(n => Math.abs(n.x + n.w - gone.x) <= NEAR && inside(n, true));
  const right = rest.filter(n => Math.abs(gone.x + gone.w - n.x) <= NEAR && inside(n, true));
  const up = rest.filter(n => Math.abs(n.y + n.h - gone.y) <= NEAR && inside(n, false));
  const down = rest.filter(n => Math.abs(gone.y + gone.h - n.y) <= NEAR && inside(n, false));
  const grow = (list, fn) => list.forEach(n => { if (!n.base) n.base = [n.w, n.h]; fn(n); });
  if (left.length) grow(left, n => { n.w = gone.x + gone.w - n.x; });
  else if (right.length) grow(right, n => { n.w = n.x + n.w - gone.x; n.x = gone.x; });
  else if (up.length) grow(up, n => { n.h = gone.y + gone.h - n.y; });
  else if (down.length) grow(down, n => { n.h = n.y + n.h - gone.y; n.y = gone.y; });
}
// neighbours touching the edges of a block when a resize starts, with their size then
function edgeNeighbours(g) {
  if (!reflowOn()) return [];
  const out = [];
  for (const n of E.groups) {
    if (n === g || n.enabled === false) continue;
    const s = { n, x: n.x, y: n.y, w: n.w, h: n.h };
    if (vOverlap(n, g) > 0 && Math.abs(n.x - (g.x + g.w)) <= NEAR) out.push({ ...s, edge: "e", gap: n.x - (g.x + g.w) });
    if (vOverlap(n, g) > 0 && Math.abs(n.x + n.w - g.x) <= NEAR) out.push({ ...s, edge: "w", gap: g.x - (n.x + n.w) });
    if (hOverlap(n, g) > 0 && Math.abs(n.y - (g.y + g.h)) <= NEAR) out.push({ ...s, edge: "s", gap: n.y - (g.y + g.h) });
    if (hOverlap(n, g) > 0 && Math.abs(n.y + n.h - g.y) <= NEAR) out.push({ ...s, edge: "n", gap: g.y - (n.y + n.h) });
  }
  return out;
}
function reflowResize(g, handle, nbs) {
  for (const s of nbs) {
    const n = s.n;
    if (!handle.includes(s.edge)) continue;
    if (!n.base) n.base = [s.w, s.h];
    if (s.edge === "e") { const x = g.x + g.w + s.gap; n.w = Math.max(16, s.x + s.w - x); n.x = s.x + s.w - n.w; }
    if (s.edge === "w") { n.w = Math.max(16, g.x - s.gap - s.x); }
    if (s.edge === "s") { const y = g.y + g.h + s.gap; n.h = Math.max(16, s.y + s.h - y); n.y = s.y + s.h - n.h; }
    if (s.edge === "n") { n.h = Math.max(16, g.y - s.gap - s.y); }
  }
}

// ------------------------------------------------------------------ selection
function selectBlock(id) {
  E.sel = id; E.open = null; E.item = null;
  edRender(); edRenderBoxes();
  const card = $("#ed-block");   // the selected block's options sit at the top of the side column
  if (card && !card.hidden) card.scrollIntoView({ block: "nearest", behavior: "smooth" });
}
function toggleMulti(id) {
  if (E.sel && !E.multi.size) E.multi.add(E.sel);
  if (E.multi.has(id)) E.multi.delete(id); else E.multi.add(id);
  E.sel = E.multi.has(E.sel) ? E.sel : [...E.multi][0] || null;
  E.item = null; E.open = null;
  edRender(); edRenderBoxes();
}
function clearSelection() {
  if (!E.sel && !E.multi.size && E.item == null) return;
  E.sel = null; E.item = null; E.open = null; E.multi.clear();
  edRender(); edRenderBoxes();
}
function deleteSelectedBlocks() {
  const ids = new Set(E.multi.size ? E.multi : (E.sel ? [E.sel] : []));
  if (!ids.size) return;
  edChange(() => {
    for (const g of E.groups.filter(x => ids.has(x.id))) reflowDelete(g);
    E.groups = E.groups.filter(x => !ids.has(x.id));
    E.sel = null; E.item = null; E.open = null; E.multi.clear();
  });
}
