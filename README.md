# 🌳 ArbolAgenda — Agenda de contactos con Árbol AVL

**Taller Árboles · Estructuras de Datos (4.º semestre)**
**Universidad Cooperativa de Colombia**

Aplicación web hecha en **Python (Flask)** con **frontend en HTML, CSS y JavaScript**. Guarda una agenda de contactos dentro de un **Árbol AVL**, es decir, un árbol binario de búsqueda que se balancea solo. La interfaz dibuja el árbol en tiempo real y anima cada operación: búsquedas, recorridos y rotaciones.

---

## 📌 Caso de estudio

En clase vimos una **agenda telefónica** guardada en un árbol binario de búsqueda (ABB). Ese árbol tiene un problema: si los contactos se insertan en orden alfabético (A, B, C, D…), **el árbol degenera en una lista**. Con 20 contactos, una búsqueda puede necesitar 20 comparaciones.

Este proyecto resuelve ese problema con un **Árbol AVL**. Después de cada inserción o eliminación, el árbol revisa el **factor de balance** de cada nodo. Si algún nodo queda desbalanceado, aplica **rotaciones**. Así la altura se mantiene cerca de `log₂(n)`.

| 20 contactos insertados de la A a la Z | Altura | Comparaciones máximas por búsqueda |
|---|---|---|
| ABB sin balanceo | 20 | 20 |
| **Árbol AVL** | **5** | **5** |

La aplicación permite cambiar entre los dos modos con un interruptor, para ver la diferencia en vivo.

---

## ✨ Funcionalidades

**Operaciones sobre el árbol**
- ➕ **Insertar** contactos (nombre, teléfono, correo y categoría). Si el nombre ya existe, se actualizan sus datos.
- 🗑️ **Eliminar** contactos. Se cubren los 3 casos: nodo hoja, nodo con un hijo y nodo con dos hijos (se usa el sucesor inorden).
- 🔍 **Buscar** un contacto. Se anima el camino desde la raíz y se muestra cuántas comparaciones hicieron falta.
- ⚡ **Autocompletar** por prefijo. Poda las ramas que no pueden tener coincidencias y muestra cuántos nodos visitó.
- 🔤 **Búsqueda por rango**, por ejemplo todos los contactos entre la "C" y la "L".
- 🔄 **Rotaciones AVL**: simple a la izquierda, simple a la derecha, doble Izquierda-Derecha y doble Derecha-Izquierda. Cada rotación queda en la bitácora.
- La búsqueda no distingue tildes ni mayúsculas: "oscar" encuentra a "Óscar".

**Recorridos animados**
- Inorden (devuelve los contactos en orden alfabético), Preorden, Postorden y Por niveles (BFS con una cola).

**Conceptos de clase calculados en vivo**
- Peso, altura, altura mínima posible, número de hojas y de ramas, raíz, orden y grado.
- Al hacer clic en un nodo se ve su **tipo** (raíz, rama u hoja), **nivel**, **grado**, **padre**, **hermano**, **hijos**, **ancestros**, **descendientes**, altura del subárbol y **factor de balance**.
- Colores iguales a los de las diapositivas: raíz 🟡, rama 🔵, hoja 🟢.

**Extras**
- Interruptor **AVL ↔ ABB simple**. El árbol se reconstruye con el mismo orden de inserción.
- Botón **"Peor caso (A→Z)"** para demostrar por qué hace falta el balanceo.
- Persistencia automática en `data/contactos.json`.
- Exportar e importar la agenda en formato JSON.
- Gráfica de contactos por categoría, control de zoom y de velocidad de animación.
- 9 pruebas unitarias que verifican las propiedades del ABB y del AVL.

---

## 🗂️ Estructura del proyecto

```
arboles/
├── app.py               # Servidor Flask y API REST
├── arbol/
│   ├── __init__.py
│   └── avl.py           # Nodo + ArbolAVL (toda la lógica del árbol)
├── templates/
│   └── index.html       # Interfaz
├── static/
│   ├── style.css        # Estilos
│   └── app.js           # Dibujo del árbol (SVG) y animaciones
├── tests/
│   └── test_avl.py      # Pruebas unitarias
├── data/                # Aquí se guarda contactos.json
└── requirements.txt
```

---

## 🚀 Cómo ejecutarlo

Requisito: Python 3.9 o superior.

```bash
# 1. Clonar el repositorio
git clone https://github.com/Santix19/arboles.git
cd arboles

# 2. (Opcional) Crear un entorno virtual
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux / Mac

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar
python app.py
```

Abrir en el navegador: **http://127.0.0.1:5000**

La primera vez se cargan automáticamente 20 contactos de ejemplo.

Para correr las pruebas:

```bash
python -m unittest -v
```

---

## 🧠 Cómo funciona el AVL

Cada nodo guarda su **altura**. El **factor de balance** es:

```
FB(nodo) = altura(subárbol izquierdo) − altura(subárbol derecho)
```

Si en algún nodo `|FB| > 1`, se rebalancea según el caso:

| Caso | Condición | Solución |
|---|---|---|
| Izquierda-Izquierda | FB > 1 y FB(hijo izq.) ≥ 0 | Rotación simple a la derecha |
| Derecha-Derecha | FB < −1 y FB(hijo der.) ≤ 0 | Rotación simple a la izquierda |
| Izquierda-Derecha | FB > 1 y FB(hijo izq.) < 0 | Rotación izquierda en el hijo, luego derecha |
| Derecha-Izquierda | FB < −1 y FB(hijo der.) > 0 | Rotación derecha en el hijo, luego izquierda |

Complejidad de insertar, buscar y eliminar: **O(log n)**. En un ABB sin balanceo el peor caso es O(n).

---

## 🔌 API REST

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/arbol` | Árbol completo, estadísticas y bitácora |
| POST | `/api/contactos` | Insertar o actualizar un contacto |
| DELETE | `/api/contactos/<nombre>` | Eliminar un contacto |
| GET | `/api/buscar?nombre=` | Buscar un contacto y devolver el camino recorrido |
| GET | `/api/autocompletar?q=` | Sugerencias por prefijo |
| GET | `/api/rango?desde=&hasta=` | Contactos dentro de un rango alfabético |
| GET | `/api/recorrido/<tipo>` | `inorden`, `preorden`, `postorden` o `niveles` |
| GET | `/api/nodo/<nombre>` | Nivel, grado, padre, hermano, etc. de un nodo |
| POST | `/api/modo` | Cambiar entre AVL y ABB simple |
| POST | `/api/demo` | Cargar datos de ejemplo (`{"ordenado": true}` para el peor caso) |
| POST | `/api/vaciar` | Vaciar la agenda |
| GET / POST | `/api/exportar` · `/api/importar` | Exportar o importar en JSON |
