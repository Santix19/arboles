// ===================== ArbolAgenda · frontend =====================
const $ = (s) => document.querySelector(s);
const SVG_NS = "http://www.w3.org/2000/svg";
const SX = 92, SY = 90, R = 22, PAD = 50;

let estado = null;
let zoom = 1;
let animacionId = 0; // permite cancelar una animación si empieza otra

// ---------- utilidades ----------
async function api(url, opciones = {}) {
  const r = await fetch(url, { headers: { "Content-Type": "application/json" }, ...opciones });
  const datos = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(datos.error || "Error del servidor");
  return datos;
}
const post = (url, cuerpo = {}) => api(url, { method: "POST", body: JSON.stringify(cuerpo) });

function toast(msg, tipo = "") {
  const t = document.createElement("div");
  t.className = "toast " + tipo;
  t.textContent = msg;
  $("#toasts").append(t);
  setTimeout(() => t.remove(), 3600);
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function el(tag, attrs = {}) {
  const e = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  return e;
}

const iniciales = (n) => n.split(/\s+/).filter(Boolean).slice(0, 2).map((p) => p[0].toUpperCase()).join("");
function corto(n) {
  const p = n.split(/\s+/);
  return p.length > 1 ? `${p[0]} ${p[1][0]}.` : n;
}
const pausa = (ms) => new Promise((r) => setTimeout(r, ms));
const velocidad = () => 1000 - Number($("#vel").value);

function gNodo(nombre) {
  return [...document.querySelectorAll(".nodo")].find((g) => g.dataset.nombre === nombre);
}
function limpiarMarcas() {
  document.querySelectorAll(".nodo").forEach((g) =>
    g.classList.remove("actual", "visita", "encontrado", "fallo", "rango", "sel"));
  document.querySelectorAll(".arista").forEach((a) => a.classList.remove("activa"));
}
function enfocar(g) {
  if (!g) return;
  const wrap = $("#wrap"), box = g.getBoundingClientRect(), w = wrap.getBoundingClientRect();
  if (box.left < w.left || box.right > w.right || box.top < w.top || box.bottom > w.bottom) {
    wrap.scrollBy({ left: box.left - w.left - w.width / 2, top: box.top - w.top - w.height / 2, behavior: "smooth" });
  }
}

// ---------- estado global ----------
const DETALLE_VACIO = $("#detalle").innerHTML;
let seleccionado = null;

function aplicarEstado(d) {
  estado = d;
  animacionId++; // cancela cualquier animación en curso
  $("#secuencia").innerHTML = "";
  document.querySelectorAll(".chip-btn").forEach((b) => b.classList.remove("activo"));
  $("#modo").checked = d.balanceado;
  renderArbol();
  renderStats();
  renderCategorias();
  renderBitacora();
  if (seleccionado) verNodo(seleccionado, true); // refresca nivel, padre, etc.
}

// ---------- dibujo del árbol ----------
function renderArbol() {
  const svg = $("#lienzo");
  svg.innerHTML = "";
  const raiz = estado.arbol;
  $("#vacio").hidden = !!raiz;
  if (!raiz) { svg.setAttribute("width", 0); svg.setAttribute("height", 0); return; }

  // Posición: x = índice inorden (nunca se cruzan), y = profundidad.
  const nodos = [];
  let i = 0;
  (function asignar(n, prof) {
    if (!n) return;
    asignar(n.izq, prof + 1);
    n.x = PAD + i++ * SX;
    n.y = PAD + prof * SY;
    n.prof = prof;
    nodos.push(n);
    asignar(n.der, prof + 1);
  })(raiz, 0);

  const ancho = PAD * 2 + (nodos.length - 1) * SX;
  const alto = PAD * 2 + Math.max(...nodos.map((n) => n.prof)) * SY + 18;
  svg.setAttribute("viewBox", `0 0 ${ancho} ${alto}`);
  svg.setAttribute("width", ancho * zoom);
  svg.setAttribute("height", alto * zoom);

  const capaAristas = el("g"), capaNodos = el("g");
  svg.append(capaAristas, capaNodos);

  for (const n of nodos) {
    for (const h of [n.izq, n.der]) {
      if (!h) continue;
      const linea = el("line", { x1: n.x, y1: n.y, x2: h.x, y2: h.y, class: "arista" });
      linea.dataset.hijo = h.nombre;
      capaAristas.append(linea);
    }
  }

  for (const n of nodos) {
    const tipo = n === raiz ? "raiz" : (!n.izq && !n.der ? "hoja" : "rama");
    const g = el("g", { class: `nodo ${tipo}`, transform: `translate(${n.x},${n.y})` });
    g.dataset.nombre = n.nombre;

    const c = el("circle", { r: R, class: "c" });
    c.style.transformBox = "fill-box";
    c.style.transformOrigin = "center";
    const ini = el("text", { class: "ini", dy: "0.35em" });
    ini.textContent = iniciales(n.nombre);
    const nom = el("text", { class: "nom", y: R + 16 });
    nom.textContent = corto(n.nombre);
    const titulo = el("title");
    titulo.textContent = `${n.nombre}\n📞 ${n.telefono}\n🏷️ ${n.categoria}\nAltura: ${n.altura} · FB: ${n.fb}`;

    const fb = el("g", { class: "fb" + (Math.abs(n.fb) > 1 ? " malo" : ""), transform: `translate(${R - 2},${-R + 2})` });
    const fbc = el("circle", { r: 9 });
    const fbt = el("text", { dy: "0.35em" });
    fbt.textContent = n.fb > 0 ? `+${n.fb}` : n.fb;
    fb.append(fbc, fbt);

    g.append(c, ini, nom, fb, titulo);
    g.addEventListener("click", () => verNodo(n.nombre));
    capaNodos.append(g);
  }
}

// ---------- estadísticas ----------
function renderStats() {
  const s = estado.stats;
  const tarjetas = [
    ["Peso (nodos)", s.peso],
    ["Altura", s.altura],
    ["Altura mínima", s.altura_minima],
    ["Hojas", s.hojas],
    ["Ramas", s.ramas],
    ["Raíz", s.raiz || "—", "txt"],
    ["Balanceado", s.balanceado ? "Sí ✓" : "No ✗", s.balanceado ? "bien" : "mal"],
    ["Búsqueda peor caso", `${s.altura} / ${s.peso}`, "", "comparaciones en el árbol vs. en una lista lineal"],
  ];
  $("#stats").innerHTML = tarjetas.map(([k, v, clase = "", tip = ""]) => `
    <div class="stat ${clase === "txt" ? "" : clase}" title="${esc(tip)}">
      <div class="v ${clase === "txt" ? "txt" : ""}">${esc(v)}</div>
      <div class="k">${esc(k)}</div>
    </div>`).join("");
}

function renderCategorias() {
  const cats = Object.entries(estado.stats.categorias).sort((a, b) => b[1] - a[1]);
  const max = Math.max(1, ...cats.map((c) => c[1]));
  $("#categorias").innerHTML = cats.length
    ? cats.map(([c, n]) => `
      <div class="barra-cat"><span>${esc(c)}</span>
        <div class="pista"><div class="relleno" style="width:${(n / max) * 100}%"></div></div><b>${n}</b></div>`).join("")
    : `<p class="mini">Sin contactos todavía.</p>`;
}

function renderBitacora() {
  $("#bitacora").innerHTML = estado.bitacora.length
    ? estado.bitacora.map((b) => `<li class="${b.includes("Rotación") ? "rot" : ""}">${esc(b)}</li>`).join("")
    : `<li class="mini">Aún no hay operaciones.</li>`;
}

// ---------- detalle de un nodo ----------
async function verNodo(nombre, silencioso = false) {
  try {
    const d = await api(`/api/nodo/${encodeURIComponent(nombre)}`);
    seleccionado = d.nombre;
    document.querySelectorAll(".nodo.sel").forEach((g) => g.classList.remove("sel"));
    gNodo(nombre)?.classList.add("sel");
    const tipo = d.tipo === "Raíz" ? "raiz" : d.tipo.toLowerCase();
    const link = (n) => n ? `<span class="link-nodo" data-ir="${esc(n)}">${esc(n)}</span>` : "—";
    $("#detalle").innerHTML = `
      <h2>🧩 Detalle del nodo</h2>
      <div class="det-cab">
        <div class="avatar ${tipo}">${esc(iniciales(d.nombre))}</div>
        <div><h3>${esc(d.nombre)}</h3><span class="etiqueta">${esc(d.tipo)}</span> <span class="etiqueta">${esc(d.categoria)}</span></div>
      </div>
      <dl class="dl">
        <dt>📞 Teléfono</dt><dd>${esc(d.telefono)}</dd>
        <dt>✉️ Correo</dt><dd>${esc(d.correo || "—")}</dd>
        <dt>Nivel</dt><dd>${d.nivel}</dd>
        <dt>Grado</dt><dd>${d.grado} hijo(s)</dd>
        <dt>Altura subárbol</dt><dd>${d.altura_subarbol}</dd>
        <dt>Factor balance</dt><dd>${d.factor_balance}</dd>
        <dt>Padre</dt><dd>${link(d.padre)}</dd>
        <dt>Hermano</dt><dd>${link(d.hermano)}</dd>
        <dt>Hijos</dt><dd>${d.hijos.length ? d.hijos.map(link).join(", ") : "— (es hoja)"}</dd>
        <dt>Descendientes</dt><dd>${d.descendientes}</dd>
        <dt>Ancestros</dt><dd>${d.ancestros.length ? d.ancestros.map(link).join(" → ") : "— (es la raíz)"}</dd>
      </dl>`;
    $("#detalle").querySelectorAll("[data-ir]").forEach((s) =>
      s.addEventListener("click", () => { verNodo(s.dataset.ir); enfocar(gNodo(s.dataset.ir)); }));
  } catch (e) {
    seleccionado = null;
    $("#detalle").innerHTML = DETALLE_VACIO;
    if (!silencioso) toast(e.message, "error");
  }
}

// ---------- animaciones ----------
async function animarCamino(camino, encontrado) {
  const id = ++animacionId;
  limpiarMarcas();
  for (let i = 0; i < camino.length; i++) {
    if (id !== animacionId) return;
    const g = gNodo(camino[i]);
    document.querySelector(`.arista[data-hijo="${CSS.escape(camino[i])}"]`)?.classList.add("activa");
    g?.classList.add("actual");
    enfocar(g);
    await pausa(velocidad());
    g?.classList.remove("actual");
    g?.classList.add("visita");
  }
  const ultimo = gNodo(camino[camino.length - 1]);
  if (ultimo) ultimo.classList.add(encontrado ? "encontrado" : "fallo");
}

async function animarRecorrido(tipo) {
  const id = ++animacionId;
  limpiarMarcas();
  document.querySelectorAll(".chip-btn").forEach((b) => b.classList.toggle("activo", b.dataset.rec === tipo));
  const { orden } = await api(`/api/recorrido/${tipo}`);
  const sec = $("#secuencia");
  sec.innerHTML = "";
  for (let i = 0; i < orden.length; i++) {
    if (id !== animacionId) return;
    const g = gNodo(orden[i]);
    g?.classList.add("actual");
    enfocar(g);
    const paso = document.createElement("span");
    paso.className = "paso";
    paso.innerHTML = `<i>${i + 1}</i>${esc(orden[i])}`;
    sec.append(paso);
    await pausa(velocidad() * 0.75);
    g?.classList.replace("actual", "visita");
  }
  document.querySelectorAll(".chip-btn").forEach((b) => b.classList.remove("activo"));
}

// ---------- acciones ----------
$("#form-nuevo").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const datos = Object.fromEntries(new FormData(ev.target));
  try {
    const d = await post("/api/contactos", datos);
    aplicarEstado(d);
    toast(d.resultado === "insertado" ? `✅ «${d.nombre}» insertado` : `✏️ «${d.nombre}» actualizado`);
    d.rotaciones.forEach((r, i) => setTimeout(() => toast(r, "rot"), 350 * (i + 1)));
    const g = gNodo(d.nombre);
    g?.classList.add("nuevo");
    enfocar(g);
    ev.target.reset();
  } catch (e) { toast(e.message, "error"); }
});

async function buscar() {
  const nombre = $("#q").value.trim();
  if (!nombre) return toast("Escribe un nombre para buscar", "error");
  $("#sugerencias").hidden = true;
  try {
    const d = await api(`/api/buscar?nombre=${encodeURIComponent(nombre)}`);
    const caja = $("#resultado-busqueda");
    caja.innerHTML = "";
    await animarCamino(d.camino, d.encontrado);
    caja.innerHTML = d.encontrado
      ? `<div class="resultado ok"><b>${esc(d.contacto.nombre)}</b><br>📞 ${esc(d.contacto.telefono)}<br>
         ✉️ ${esc(d.contacto.correo || "—")}<br>🔎 ${d.comparaciones} comparación(es) de ${d.peso} contactos</div>`
      : `<div class="resultado mal">«${esc(nombre)}» no está en la agenda.<br>🔎 Se descartó en ${d.comparaciones} comparación(es).</div>`;
    if (d.encontrado) verNodo(d.contacto.nombre);
  } catch (e) { toast(e.message, "error"); }
}
$("#btn-buscar").addEventListener("click", buscar);
$("#q").addEventListener("keydown", (e) => { if (e.key === "Enter") buscar(); });

$("#btn-eliminar").addEventListener("click", async () => {
  const nombre = $("#q").value.trim();
  if (!nombre) return toast("Escribe el nombre a eliminar", "error");
  if (!confirm(`¿Eliminar a «${nombre}» de la agenda?`)) return;
  try {
    const d = await api(`/api/contactos/${encodeURIComponent(nombre)}`, { method: "DELETE" });
    aplicarEstado(d);
    toast(`🗑️ «${nombre}» eliminado`);
    d.rotaciones.forEach((r, i) => setTimeout(() => toast(r, "rot"), 350 * (i + 1)));
    $("#q").value = "";
    $("#resultado-busqueda").innerHTML = "";
  } catch (e) { toast(e.message, "error"); }
});

// autocompletar con debounce
let temporizador;
$("#q").addEventListener("input", () => {
  clearTimeout(temporizador);
  temporizador = setTimeout(async () => {
    const q = $("#q").value.trim();
    const lista = $("#sugerencias");
    if (!q) { lista.hidden = true; $("#info-auto").textContent = ""; return; }
    const d = await api(`/api/autocompletar?q=${encodeURIComponent(q)}`);
    $("#info-auto").textContent = `Autocompletado: visitó ${d.visitados} de ${estado.stats.peso} nodos (poda de ramas)`;
    lista.innerHTML = d.resultados.map((c) =>
      `<li data-n="${esc(c.nombre)}">${esc(c.nombre)}<small>${esc(c.telefono)}</small></li>`).join("");
    lista.hidden = !d.resultados.length;
    lista.querySelectorAll("li").forEach((li) => li.addEventListener("click", () => {
      $("#q").value = li.dataset.n;
      buscar();
    }));
  }, 140);
});
document.addEventListener("click", (e) => { if (!e.target.closest(".auto")) $("#sugerencias").hidden = true; });

$("#btn-rango").addEventListener("click", async () => {
  const desde = $("#desde").value.trim(), hasta = $("#hasta").value.trim();
  try {
    const d = await api(`/api/rango?desde=${encodeURIComponent(desde)}&hasta=${encodeURIComponent(hasta)}`);
    animacionId++;
    limpiarMarcas();
    d.resultados.forEach((c) => gNodo(c.nombre)?.classList.add("rango"));
    $("#resultado-rango").innerHTML = `
      <p class="mini">${d.resultados.length} contacto(s) · visitó ${d.visitados} de ${d.peso} nodos</p>
      <ul class="lista-mini">${d.resultados.map((c) =>
        `<li>${esc(c.nombre)}<small>${esc(c.telefono)}</small></li>`).join("") || "<li>Sin resultados</li>"}</ul>`;
  } catch (e) { toast(e.message, "error"); }
});

document.querySelectorAll("[data-rec]").forEach((b) =>
  b.addEventListener("click", () => estado.arbol ? animarRecorrido(b.dataset.rec) : toast("El árbol está vacío", "error")));

$("#modo").addEventListener("change", async (e) => {
  const d = await post("/api/modo", { balanceado: e.target.checked });
  aplicarEstado(d);
  toast(e.target.checked
    ? `⚖️ Árbol AVL: altura ${d.stats.altura}`
    : `🌱 ABB sin balanceo: altura ${d.stats.altura}`);
});

$("#btn-demo").addEventListener("click", async () => {
  aplicarEstado(await post("/api/demo", { ordenado: false }));
  toast("📦 Demo cargada en orden aleatorio");
});
$("#btn-peor").addEventListener("click", async () => {
  const d = await post("/api/demo", { ordenado: true });
  aplicarEstado(d);
  toast(d.balanceado
    ? `Insertados A→Z: el AVL rotó y quedó con altura ${d.stats.altura} 💪`
    : `Insertados A→Z sin balanceo: ¡el árbol degeneró en una lista de altura ${d.stats.altura}! 😱`,
    d.balanceado ? "rot" : "error");
});
$("#btn-vaciar").addEventListener("click", async () => {
  if (!confirm("¿Vaciar toda la agenda?")) return;
  aplicarEstado(await post("/api/vaciar"));
  $("#secuencia").innerHTML = "";
});
$("#archivo").addEventListener("change", async (e) => {
  const archivo = e.target.files[0];
  if (!archivo) return;
  try {
    const datos = JSON.parse(await archivo.text());
    aplicarEstado(await post("/api/importar", datos));
    toast(`📥 Importados ${estado.stats.peso} contactos`);
  } catch (err) { toast("Archivo inválido: " + err.message, "error"); }
  e.target.value = "";
});

$("#zoom").addEventListener("input", (e) => { zoom = e.target.value / 100; renderArbol(); });

// ---------- inicio ----------
api("/api/arbol").then(aplicarEstado).catch((e) => toast(e.message, "error"));
