import unittest

from arbol import ArbolAVL
from arbol.avl import altura, factor_balance


def es_abb(n, lo=None, hi=None):
    if n is None:
        return True
    if (lo is not None and n.clave <= lo) or (hi is not None and n.clave >= hi):
        return False
    return es_abb(n.izq, lo, n.clave) and es_abb(n.der, n.clave, hi)


def todos_balanceados(n):
    if n is None:
        return True
    return abs(factor_balance(n)) <= 1 and todos_balanceados(n.izq) and todos_balanceados(n.der)


NOMBRES = [f"Contacto {chr(65 + i)}" for i in range(20)]  # A..T en orden


class PruebasAVL(unittest.TestCase):
    def setUp(self):
        self.arbol = ArbolAVL()
        for i, n in enumerate(NOMBRES):
            self.arbol.insertar(n, f"300{i:04d}")

    def test_peor_caso_queda_balanceado(self):
        self.assertTrue(es_abb(self.arbol.raiz))
        self.assertTrue(todos_balanceados(self.arbol.raiz))
        self.assertLessEqual(altura(self.arbol.raiz), 6)

    def test_abb_sin_balanceo_degenera(self):
        self.arbol.cambiar_modo(False)
        self.assertEqual(altura(self.arbol.raiz), 20)
        self.arbol.cambiar_modo(True)
        self.assertTrue(todos_balanceados(self.arbol.raiz))

    def test_buscar_con_tildes(self):
        self.arbol.insertar("Óscar Timarán", "329")
        nodo, camino = self.arbol.buscar("oscar timaran")
        self.assertIsNotNone(nodo)
        self.assertEqual(nodo.nombre, "Óscar Timarán")
        self.assertGreater(len(camino), 0)

    def test_actualizar_no_duplica(self):
        self.assertEqual(self.arbol.insertar("Contacto A", "999"), "actualizado")
        self.assertEqual(self.arbol.peso(), 20)
        self.assertEqual(self.arbol.buscar("Contacto A")[0].telefono, "999")

    def test_eliminar_mantiene_propiedades(self):
        for n in NOMBRES[::3]:
            self.assertTrue(self.arbol.eliminar(n))
        self.assertFalse(self.arbol.eliminar("No existe"))
        self.assertTrue(es_abb(self.arbol.raiz))
        self.assertTrue(todos_balanceados(self.arbol.raiz))
        self.assertEqual(self.arbol.peso(), 20 - len(NOMBRES[::3]))

    def test_recorridos(self):
        self.assertEqual(self.arbol.recorrido("inorden"), NOMBRES)
        pre = self.arbol.recorrido("preorden")
        self.assertEqual(pre[0], self.arbol.raiz.nombre)
        self.assertEqual(self.arbol.recorrido("postorden")[-1], self.arbol.raiz.nombre)
        self.assertEqual(self.arbol.recorrido("niveles")[0], self.arbol.raiz.nombre)
        self.assertEqual(sorted(pre), NOMBRES)

    def test_autocompletar_y_rango(self):
        self.arbol.insertar("Mariana", "1")
        self.arbol.insertar("Mateo", "2")
        res, _ = self.arbol.autocompletar("ma")
        self.assertEqual([c["nombre"] for c in res], ["Mariana", "Mateo"])
        res, _ = self.arbol.rango("Contacto B", "Contacto D")
        self.assertEqual([c["nombre"] for c in res], ["Contacto B", "Contacto C", "Contacto D"])

    def test_info_nodo(self):
        raiz = self.arbol.info_nodo(self.arbol.raiz.nombre)
        self.assertEqual(raiz["tipo"], "Raíz")
        self.assertEqual(raiz["nivel"], 1)
        self.assertEqual(raiz["descendientes"], 19)
        hoja = self.arbol.info_nodo(self.arbol.minimo().nombre)
        self.assertIn(hoja["tipo"], ("Hoja", "Rama"))
        self.assertGreater(hoja["nivel"], 1)

    def test_estadisticas(self):
        s = self.arbol.estadisticas()
        self.assertEqual(s["peso"], 20)
        self.assertEqual(s["altura_minima"], 5)
        self.assertEqual(s["hojas"] + s["ramas"] + 1, 20)
        self.assertTrue(s["balanceado"])


if __name__ == "__main__":
    unittest.main()
