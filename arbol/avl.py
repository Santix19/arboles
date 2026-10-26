"""
Árbol AVL para una agenda de contactos.

Un árbol AVL es un Árbol Binario de Búsqueda (ABB) que se auto-balancea:
en cada nodo la diferencia entre la altura del sub-árbol izquierdo y la del
derecho (factor de balance) nunca es mayor que 1. Cuando una inserción o
eliminación rompe esa regla se aplican rotaciones.

La clase también puede funcionar como un ABB "normal" (sin balanceo) para
poder comparar ambos comportamientos desde el frontend.
"""
import json
import math
import unicodedata
from collections import deque
from pathlib import Path


def normalizar(texto):
    """Clave de comparación: minúsculas y sin tildes ("Óscar" == "oscar")."""
    t = unicodedata.normalize("NFD", (texto or "").strip().lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


class Nodo:
    """Nodo del árbol: guarda un contacto y los enlaces a sus dos hijos."""

    def __init__(self, nombre, telefono, correo="", categoria="General"):
        self.nombre = nombre.strip()
        self.clave = normalizar(nombre)
        self.telefono = telefono.strip()
        self.correo = (correo or "").strip()
        self.categoria = (categoria or "").strip() or "General"
        self.izq = None
        self.der = None
        self.altura = 1  # una hoja tiene altura 1

    def contacto(self):
        return {
            "nombre": self.nombre,
            "telefono": self.telefono,
            "correo": self.correo,
            "categoria": self.categoria,
        }

    def grado(self):
        """Número de hijos del nodo (0, 1 o 2)."""
        return (self.izq is not None) + (self.der is not None)


# ---------- utilidades de altura y balance ----------

def altura(n):
    return n.altura if n else 0


def actualizar_altura(n):
    n.altura = 1 + max(altura(n.izq), altura(n.der))


def factor_balance(n):
    return altura(n.izq) - altura(n.der) if n else 0


class ArbolAVL:
    def __init__(self, balanceado=True):
        self.raiz = None
        self.balanceado = balanceado  # False = se comporta como ABB simple
        self.bitacora = []            # historial de operaciones y rotaciones
        self._orden_insercion = []    # claves en el orden en que se insertaron
        self._silencio = False

    # ---------- bitácora ----------

    def _registrar(self, mensaje):
        if not self._silencio:
            self.bitacora.append(mensaje)
            self.bitacora = self.bitacora[-60:]

    # ---------- rotaciones ----------

    def _rotar_derecha(self, y):
        x = y.izq
        y.izq = x.der
        x.der = y
        actualizar_altura(y)
        actualizar_altura(x)
        return x

    def _rotar_izquierda(self, x):
        y = x.der
        x.der = y.izq
        y.izq = x
        actualizar_altura(x)
        actualizar_altura(y)
        return y

    def _rebalancear(self, n):
        actualizar_altura(n)
        if not self.balanceado:
            return n

        fb = factor_balance(n)
        if fb > 1:  # cargado a la izquierda
            if factor_balance(n.izq) < 0:
                self._registrar(f"🔄 Rotación doble Izquierda-Derecha en «{n.nombre}»")
                n.izq = self._rotar_izquierda(n.izq)
            else:
                self._registrar(f"↻ Rotación simple a la derecha en «{n.nombre}»")
            return self._rotar_derecha(n)

        if fb < -1:  # cargado a la derecha
            if factor_balance(n.der) > 0:
                self._registrar(f"🔄 Rotación doble Derecha-Izquierda en «{n.nombre}»")
                n.der = self._rotar_derecha(n.der)
            else:
                self._registrar(f"↺ Rotación simple a la izquierda en «{n.nombre}»")
            return self._rotar_izquierda(n)

        return n

    # ---------- insertar ----------

    def insertar(self, nombre, telefono, correo="", categoria="General"):
        """Inserta un contacto. Si el nombre ya existe, actualiza sus datos.
        Devuelve "insertado" o "actualizado"."""
        if not (nombre or "").strip():
            raise ValueError("El nombre es obligatorio")
        if not (telefono or "").strip():
            raise ValueError("El teléfono es obligatorio")

        nuevo = Nodo(nombre, telefono, correo, categoria)
        self._resultado = "insertado"
        self.raiz = self._insertar(self.raiz, nuevo)

        if self._resultado == "insertado":
            self._orden_insercion.append(nuevo.clave)
            self._registrar(f"➕ Insertado «{nuevo.nombre}»")
        else:
            self._registrar(f"✏️ Actualizado «{nuevo.nombre}»")
        return self._resultado

    def _insertar(self, n, nuevo):
        if n is None:
            return nuevo
        if nuevo.clave < n.clave:
            n.izq = self._insertar(n.izq, nuevo)
        elif nuevo.clave > n.clave:
            n.der = self._insertar(n.der, nuevo)
        else:  # ya existe -> actualizar datos
            n.nombre, n.telefono = nuevo.nombre, nuevo.telefono
            n.correo, n.categoria = nuevo.correo, nuevo.categoria
            self._resultado = "actualizado"
            return n
        return self._rebalancear(n)

    # ---------- eliminar ----------

    def eliminar(self, nombre):
        clave = normalizar(nombre)
        self._eliminado = None
        self.raiz = self._eliminar(self.raiz, clave)
        if self._eliminado:
            self._orden_insercion.remove(clave)
            self._registrar(f"🗑️ Eliminado «{self._eliminado}»")
            return True
        return False

    def _eliminar(self, n, clave):
        if n is None:
            return None
        if clave < n.clave:
            n.izq = self._eliminar(n.izq, clave)
        elif clave > n.clave:
            n.der = self._eliminar(n.der, clave)
        else:
            if self._eliminado is None:
                self._eliminado = n.nombre
            # caso 1 y 2: cero o un hijo
            if n.izq is None:
                return n.der
            if n.der is None:
                return n.izq
            # caso 3: dos hijos -> se reemplaza por el sucesor inorden
            sucesor = n.der
            while sucesor.izq:
                sucesor = sucesor.izq
            n.nombre, n.clave = sucesor.nombre, sucesor.clave
            n.telefono, n.correo, n.categoria = sucesor.telefono, sucesor.correo, sucesor.categoria
            n.der = self._eliminar(n.der, sucesor.clave)
        return self._rebalancear(n)

    # ---------- búsquedas ----------

    def buscar(self, nombre):
        """Devuelve (nodo | None, camino recorrido desde la raíz)."""
        clave = normalizar(nombre)
        camino = []
        n = self.raiz
        while n:
            camino.append(n.nombre)
            if clave == n.clave:
                return n, camino
            n = n.izq if clave < n.clave else n.der
        return None, camino

    def autocompletar(self, prefijo, limite=8):
        """Contactos cuyo nombre empieza por `prefijo`, en orden alfabético.
        Poda las ramas que no pueden contener coincidencias."""
        p = normalizar(prefijo)
        resultados, visitados = [], [0]

        def rec(n):
            if n is None or len(resultados) >= limite:
                return
            visitados[0] += 1
            if n.clave > p:
                rec(n.izq)
            if n.clave.startswith(p) and len(resultados) < limite:
                resultados.append(n.contacto())
            if n.clave[:len(p)] <= p:
                rec(n.der)

        rec(self.raiz)
        return resultados, visitados[0]

    def rango(self, desde, hasta):
        """Contactos entre dos nombres (inclusive), p. ej. de "A" a "D"."""
        lo = normalizar(desde)
        hi = normalizar(hasta) + "\uffff"  # incluye todo lo que empieza por `hasta`
        resultados, visitados = [], [0]

        def rec(n):
            if n is None:
                return
            visitados[0] += 1
            if n.clave > lo:
                rec(n.izq)
            if lo <= n.clave <= hi:
                resultados.append(n.contacto())
            if n.clave < hi:
                rec(n.der)

        rec(self.raiz)
        return resultados, visitados[0]

    def minimo(self):
        n = self.raiz
        while n and n.izq:
            n = n.izq
        return n

    def maximo(self):
        n = self.raiz
        while n and n.der:
            n = n.der
        return n

    # ---------- recorridos ----------

    def recorrido(self, tipo):
        res = []
        if tipo == "inorden":
            self._inorden(self.raiz, res)
        elif tipo == "preorden":
            self._preorden(self.raiz, res)
        elif tipo == "postorden":
            self._postorden(self.raiz, res)
        elif tipo == "niveles":
            res = self._por_niveles()
        else:
            raise ValueError(f"Recorrido desconocido: {tipo}")
        return res

    def _inorden(self, n, res):        # izquierda - raíz - derecha
        if n:
            self._inorden(n.izq, res)
            res.append(n.nombre)
            self._inorden(n.der, res)

    def _preorden(self, n, res):       # raíz - izquierda - derecha
        if n:
            res.append(n.nombre)
            self._preorden(n.izq, res)
            self._preorden(n.der, res)

    def _postorden(self, n, res):      # izquierda - derecha - raíz
        if n:
            self._postorden(n.izq, res)
            self._postorden(n.der, res)
            res.append(n.nombre)

    def _por_niveles(self):            # anchura (BFS) usando una cola
        res = []
        cola = deque([self.raiz] if self.raiz else [])
        while cola:
            n = cola.popleft()
            res.append(n.nombre)
            if n.izq:
                cola.append(n.izq)
            if n.der:
                cola.append(n.der)
        return res

    # ---------- propiedades del árbol (conceptos de clase) ----------

    def _nodos(self):
        pila = [self.raiz] if self.raiz else []
        while pila:
            n = pila.pop()
            yield n
            if n.der:
                pila.append(n.der)
            if n.izq:
                pila.append(n.izq)

    def peso(self):
        return sum(1 for _ in self._nodos())

    def estadisticas(self):
        nodos = list(self._nodos())
        peso = len(nodos)
        categorias = {}
        for n in nodos:
            categorias[n.categoria] = categorias.get(n.categoria, 0) + 1
        minimo, maximo = self.minimo(), self.maximo()
        return {
            "peso": peso,
            "altura": altura(self.raiz),
            "altura_minima": math.ceil(math.log2(peso + 1)) if peso else 0,
            "hojas": sum(1 for n in nodos if n.grado() == 0),
            "ramas": sum(1 for n in nodos if n is not self.raiz and n.grado() > 0),
            "raiz": self.raiz.nombre if self.raiz else None,
            "orden": 2,
            "grado": max((n.grado() for n in nodos), default=0),
            "balanceado": all(abs(factor_balance(n)) <= 1 for n in nodos),
            "minimo": minimo.nombre if minimo else None,
            "maximo": maximo.nombre if maximo else None,
            "categorias": categorias,
        }

    def info_nodo(self, nombre):
        """Todo lo que se puede decir de un nodo: nivel, grado, padre, hermano..."""
        clave = normalizar(nombre)
        n, padre, nivel, ancestros = self.raiz, None, 1, []
        while n and n.clave != clave:
            ancestros.append(n.nombre)
            padre = n
            n = n.izq if clave < n.clave else n.der
            nivel += 1
        if n is None:
            return None

        hermano = None
        if padre:
            h = padre.der if padre.izq is n else padre.izq
            hermano = h.nombre if h else None

        if n is self.raiz:
            tipo = "Raíz"
        elif n.grado() == 0:
            tipo = "Hoja"
        else:
            tipo = "Rama"

        descendientes = sum(1 for _ in ArbolAVL._contar(n)) - 1
        return {
            **n.contacto(),
            "tipo": tipo,
            "nivel": nivel,
            "grado": n.grado(),
            "padre": padre.nombre if padre else None,
            "hermano": hermano,
            "hijos": [h.nombre for h in (n.izq, n.der) if h],
            "ancestros": ancestros,
            "descendientes": descendientes,
            "altura_subarbol": n.altura,
            "factor_balance": factor_balance(n),
        }

    @staticmethod
    def _contar(n):
        pila = [n]
        while pila:
            x = pila.pop()
            yield x
            pila.extend(h for h in (x.izq, x.der) if h)

    # ---------- serialización ----------

    def a_dict(self, n="__raiz__"):
        """Árbol anidado para que el frontend lo dibuje."""
        if n == "__raiz__":
            n = self.raiz
        if n is None:
            return None
        return {
            **n.contacto(),
            "altura": n.altura,
            "fb": factor_balance(n),
            "izq": self.a_dict(n.izq),
            "der": self.a_dict(n.der),
        }

    def contactos_en_orden_insercion(self):
        por_clave = {n.clave: n.contacto() for n in self._nodos()}
        return [por_clave[k] for k in self._orden_insercion if k in por_clave]

    def cambiar_modo(self, balanceado):
        """Reconstruye el árbol como AVL o como ABB simple, respetando el
        orden original de inserción (así se ve la diferencia)."""
        contactos = self.contactos_en_orden_insercion()
        self.balanceado = balanceado
        self.vaciar(registrar=False)
        self._silencio = True
        for c in contactos:
            self.insertar(**c)
        self._silencio = False
        self._registrar("⚖️ Reconstruido como árbol AVL (balanceado)" if balanceado
                        else "🌱 Reconstruido como ABB sin balanceo")

    def vaciar(self, registrar=True):
        self.raiz = None
        self._orden_insercion = []
        if registrar:
            self._registrar("🧹 Agenda vaciada")

    def guardar(self, ruta):
        ruta = Path(ruta)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        datos = {"balanceado": self.balanceado, "contactos": self.contactos_en_orden_insercion()}
        ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def cargar(cls, ruta):
        datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
        arbol = cls(balanceado=datos.get("balanceado", True))
        arbol._silencio = True
        for c in datos.get("contactos", []):
            arbol.insertar(**c)
        arbol._silencio = False
        modo = "AVL" if arbol.balanceado else "ABB simple"
        arbol._registrar(f"📂 Agenda cargada: {arbol.peso()} contactos ({modo})")
        return arbol
