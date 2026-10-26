"""
ArbolAgenda — Agenda de contactos sobre un Árbol AVL.
Backend en Flask que expone el árbol mediante una API REST para el frontend.

Ejecutar:  python app.py   ->   http://127.0.0.1:5000
"""
import json
import random
from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request

from arbol import ArbolAVL

BASE = Path(__file__).parent
RUTA_DATOS = BASE / "data" / "contactos.json"

DEMO = [
    ("Mariana López", "310 555 0101", "mariana@correo.com", "Universidad"),
    ("Santiago Benavides", "311 555 0102", "santi.b@correo.com", "Amigos"),
    ("Valentina Rosero", "312 555 0103", "vale.rosero@correo.com", "Familia"),
    ("Andrés Burbano", "313 555 0104", "aburbano@correo.com", "Trabajo"),
    ("Camila Ortega", "314 555 0105", "camila.o@correo.com", "Universidad"),
    ("Daniel Erazo", "315 555 0106", "derazo@correo.com", "Amigos"),
    ("Laura Insuasty", "316 555 0107", "laura.i@correo.com", "Trabajo"),
    ("Felipe Guerrero", "317 555 0108", "felipe.g@correo.com", "Universidad"),
    ("Sofía Delgado", "318 555 0109", "sofi.d@correo.com", "Familia"),
    ("Juan Pablo Chamorro", "319 555 0110", "jp.chamorro@correo.com", "Amigos"),
    ("Natalia Villota", "320 555 0111", "nvillota@correo.com", "Trabajo"),
    ("Sebastián Muñoz", "321 555 0112", "sebas.m@correo.com", "Universidad"),
    ("Isabella Pantoja", "322 555 0113", "isa.pantoja@correo.com", "Familia"),
    ("Mateo Cabrera", "323 555 0114", "mateo.c@correo.com", "Amigos"),
    ("Gabriela Narváez", "324 555 0115", "gabi.n@correo.com", "Universidad"),
    ("Tomás Zambrano", "325 555 0116", "tomas.z@correo.com", "Trabajo"),
    ("Paula Enríquez", "326 555 0117", "paula.e@correo.com", "Familia"),
    ("Esteban Ruano", "327 555 0118", "e.ruano@correo.com", "Amigos"),
    ("Lucía Bravo", "328 555 0119", "lucia.b@correo.com", "Universidad"),
    ("Óscar Timarán", "329 555 0120", "oscar.t@correo.com", "Trabajo"),
]

app = Flask(__name__)


def cargar_demo(arbol, ordenado=False):
    datos = sorted(DEMO, key=lambda c: c[0]) if ordenado else random.sample(DEMO, len(DEMO))
    arbol.vaciar(registrar=False)
    arbol._silencio = not ordenado  # en el peor caso sí mostramos las rotaciones
    for nombre, tel, correo, cat in datos:
        arbol.insertar(nombre, tel, correo, cat)
    arbol._silencio = False
    arbol._registrar("📦 Demo cargada " + ("en orden alfabético (peor caso)" if ordenado else "en orden aleatorio"))


if RUTA_DATOS.exists():
    arbol = ArbolAVL.cargar(RUTA_DATOS)
else:
    arbol = ArbolAVL()
    cargar_demo(arbol)
    arbol.guardar(RUTA_DATOS)


def estado(**extra):
    """Respuesta estándar: el árbol completo + estadísticas + bitácora."""
    return jsonify({
        "arbol": arbol.a_dict(),
        "stats": arbol.estadisticas(),
        "balanceado": arbol.balanceado,
        "bitacora": list(reversed(arbol.bitacora[-20:])),
        **extra,
    })


def guardar():
    arbol.guardar(RUTA_DATOS)


@app.errorhandler(ValueError)
def error_valor(e):
    return jsonify({"error": str(e)}), 400


# ---------------- vistas ----------------

@app.get("/")
def inicio():
    return render_template("index.html")


@app.get("/api/arbol")
def obtener_arbol():
    return estado()


@app.post("/api/contactos")
def crear_contacto():
    d = request.get_json(force=True) or {}
    antes = len(arbol.bitacora)
    resultado = arbol.insertar(d.get("nombre", ""), d.get("telefono", ""),
                               d.get("correo", ""), d.get("categoria", "General"))
    eventos = arbol.bitacora[antes:]
    rotaciones = [e for e in eventos if "Rotación" in e]
    guardar()
    return estado(resultado=resultado, nombre=d["nombre"].strip(), rotaciones=rotaciones)


@app.delete("/api/contactos/<path:nombre>")
def borrar_contacto(nombre):
    antes = len(arbol.bitacora)
    if not arbol.eliminar(nombre):
        return jsonify({"error": f"No existe el contacto «{nombre}»"}), 404
    rotaciones = [e for e in arbol.bitacora[antes:] if "Rotación" in e]
    guardar()
    return estado(rotaciones=rotaciones)


@app.get("/api/buscar")
def buscar():
    nodo, camino = arbol.buscar(request.args.get("nombre", ""))
    return jsonify({
        "encontrado": nodo is not None,
        "contacto": nodo.contacto() if nodo else None,
        "camino": camino,
        "comparaciones": len(camino),
        "peso": arbol.peso(),
    })


@app.get("/api/autocompletar")
def autocompletar():
    resultados, visitados = arbol.autocompletar(request.args.get("q", ""))
    return jsonify({"resultados": resultados, "visitados": visitados})


@app.get("/api/rango")
def rango():
    desde = request.args.get("desde", "")
    hasta = request.args.get("hasta", "")
    if desde and hasta and desde.lower() > hasta.lower():
        desde, hasta = hasta, desde
    resultados, visitados = arbol.rango(desde, hasta or "￿")
    return jsonify({"resultados": resultados, "visitados": visitados, "peso": arbol.peso()})


@app.get("/api/recorrido/<tipo>")
def recorrido(tipo):
    return jsonify({"tipo": tipo, "orden": arbol.recorrido(tipo)})


@app.get("/api/nodo/<path:nombre>")
def info_nodo(nombre):
    info = arbol.info_nodo(nombre)
    if info is None:
        return jsonify({"error": "Nodo no encontrado"}), 404
    return jsonify(info)


@app.post("/api/modo")
def cambiar_modo():
    d = request.get_json(force=True) or {}
    arbol.cambiar_modo(bool(d.get("balanceado", True)))
    guardar()
    return estado()


@app.post("/api/demo")
def demo():
    d = request.get_json(silent=True) or {}
    cargar_demo(arbol, ordenado=bool(d.get("ordenado")))
    guardar()
    return estado()


@app.post("/api/vaciar")
def vaciar():
    arbol.vaciar()
    guardar()
    return estado()


@app.get("/api/exportar")
def exportar():
    datos = {"balanceado": arbol.balanceado, "contactos": arbol.contactos_en_orden_insercion()}
    return Response(
        json.dumps(datos, ensure_ascii=False, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": "attachment; filename=agenda.json"},
    )


@app.post("/api/importar")
def importar():
    d = request.get_json(force=True) or {}
    contactos = d.get("contactos")
    if not isinstance(contactos, list):
        raise ValueError("El archivo no tiene una lista de 'contactos'")
    arbol.vaciar(registrar=False)
    for c in contactos:
        arbol.insertar(c.get("nombre", ""), c.get("telefono", ""), c.get("correo", ""), c.get("categoria", "General"))
    arbol._registrar(f"📥 Importados {len(contactos)} contactos")
    guardar()
    return estado()


if __name__ == "__main__":
    app.run(debug=True)
