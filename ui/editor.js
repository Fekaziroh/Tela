"use strict";
// Layout editor: blocks on the preview can be selected, moved and resized; their items are edited on the side.

const E = { lay: null, groups: [], sel: null, open: null, undo: [], W: 480, H: 320, timer: null, loading: false };
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
    if (!selGroup()) E.sel = null;
    edRender();
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
}

// ------------------------------------------------------------------ stage (preview with draggable blocks)
function stageScale() { return $("#stage-img").clientWidth / E.W || 1; }
function edRenderBoxes() {
  const box = $("#stage-boxes");
  const sc = stageScale();
  box.innerHTML = "";
  for (const g of E.groups) {
    const el = document.createElement("div");
    el.className = "box" + (g.id === E.sel ? " sel" : "") + (g.enabled === false ? " off" : "");
    Object.assign(el.style, { left: g.x * sc + "px", top: g.y * sc + "px", width: g.w * sc + "px", height: g.h * sc + "px" });
    el.dataset.id = g.id;
    el.innerHTML = `<span class="tag-b">${esc(blockName(g))}</span><i class="handle nw"></i><i class="handle ne"></i><i class="handle sw"></i><i class="handle se"></i>`;
    el.addEventListener("pointerdown", e => edPointer(e, g, el));
    box.appendChild(el);
  }
  $("#ed-family").textContent = t(E.lay && E.lay.family === "portrait" ? "ed.portrait" : "ed.landscape") + ` · ${E.W}×${E.H}` + (E.lay && E.lay.custom ? " · " + t("ed.custom") : "");
}
function edPointer(e, g, el) {
  e.preventDefault();
  e.stopPropagation();
  if (E.sel !== g.id) { E.sel = g.id; E.open = null; edRender(); el = $(`#stage-boxes [data-id="${CSS.escape(g.id)}"]`); }
  const handle = e.target.classList.contains("handle") ? [...e.target.classList].find(c => c.length === 2) : null;
  const sc = stageScale();
  const start = { px: e.clientX, py: e.clientY, x: g.x, y: g.y, w: g.w, h: g.h };
  const snapshot = JSON.stringify(E.groups);
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
  };
  paint();
  const move = ev => {
    const dx = (ev.clientX - start.px) / sc, dy = (ev.clientY - start.py) / sc;
    if (Math.abs(dx) + Math.abs(dy) > 1) moved = true;
    if (!handle) {
      g.x = Math.max(0, Math.min(E.W - g.w, snap(start.x + dx)));
      g.y = Math.max(0, Math.min(E.H - g.h, snap(start.y + dy)));
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
  const img = $("#stage-img");
  img.style.aspectRatio = `${E.W} / ${E.H}`;
  edRenderBoxes();
  // block list
  const list = $("#ed-blocks");
  list.innerHTML = "";
  for (const g of E.groups) {
    const row = document.createElement("div");
    row.className = "row" + (g.id === E.sel ? " on" : "");
    row.innerHTML = `<span class="lbl">${esc(blockName(g))} <small>${Math.round(g.w)}×${Math.round(g.h)}</small></span><button class="sw" role="switch" aria-checked="${g.enabled !== false}" aria-label="${esc(blockName(g))}"></button>`;
    row.addEventListener("click", e => { if (e.target.classList.contains("sw")) return; E.sel = g.id; E.open = null; edRender(); });
    $(".sw", row).addEventListener("click", () => edChange(() => { g.enabled = g.enabled === false; }));
    list.appendChild(row);
  }
  // selected block
  const g = selGroup();
  $("#ed-block").hidden = !g;
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
  if (it.type === "clock") box.append(field("ed.format", selectInput(it, "format", CLOCK_FORMATS, CLOCK_FORMATS.map(f => t("clock." + CLOCK_FORMATS.indexOf(f))))));
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
  return box;
}
function edRenderItems(g) {
  const box = $("#ed-items");
  box.innerHTML = "";
  (g.items || []).forEach((it, i) => {
    const el = document.createElement("div");
    el.className = "item-ed" + (it.enabled === false ? " off" : "");
    el.innerHTML = `<div class="row"><span class="lbl">${itemLabel(it)}</span><span class="inline"><button class="sw" role="switch" aria-checked="${it.enabled !== false}"></button><button class="icon-btn" title="${t("ed.remove")}">✕</button></span></div>`;
    $(".lbl", el).addEventListener("click", () => { E.open = E.open === i ? null : i; edRender(); });
    $(".sw", el).addEventListener("click", () => edChange(() => { it.enabled = it.enabled === false; }));
    $(".icon-btn", el).addEventListener("click", () => edChange(() => { g.items.splice(i, 1); E.open = null; }));
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
  $("#ed-del").addEventListener("click", () => edChange(() => { E.groups = E.groups.filter(g => g.id !== E.sel); E.sel = null; }));
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
    if (S.tab !== "layout" || !E.sel || /INPUT|SELECT|TEXTAREA/.test(document.activeElement.tagName)) return;
    const g = selGroup();
    const d = e.shiftKey ? 10 : 2;
    const mv = { ArrowLeft: [-d, 0], ArrowRight: [d, 0], ArrowUp: [0, -d], ArrowDown: [0, d] }[e.key];
    if (mv) {
      e.preventDefault();
      edChange(() => { g.x = Math.max(0, Math.min(E.W - g.w, g.x + mv[0])); g.y = Math.max(0, Math.min(E.H - g.h, g.y + mv[1])); });
    } else if ((e.key === "z" || e.key === "Z") && (e.ctrlKey || e.metaKey)) { e.preventDefault(); $("#ed-undo").click(); }
  });
  $("#stage").addEventListener("pointerdown", e => { if (e.target.id === "stage" || e.target.id === "stage-img" || e.target.id === "stage-boxes") { E.sel = null; edRender(); } });
  window.addEventListener("resize", () => { if (S.tab === "layout") edRenderBoxes(); });
  setInterval(async () => {   // live values in the sensor lists
    if (S.tab !== "layout" || document.visibilityState !== "visible" || !E.lay || E.open == null) return;
    try { E.lay.sensors = await api.sensor_values(); } catch (e) { /* ignore */ }
  }, 3000);
}
