"""Pruebas de sintaxis y equivalencia de las transformaciones."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from gramaticas import (EPSILON, a_fnc, eliminar_epsilon, eliminar_inutiles,
                       eliminar_unitarias, leer_gramatica, anulables)


BASE = Path(__file__).resolve().parent


def lenguaje_acotado(g, max_largo=4):
    """Punto fijo independiente de las transformaciones, hasta max_largo."""
    lenguajes = {a: set() for a in g.reglas}
    while True:
        cambio = False
        for cabeza, cuerpos in g.reglas.items():
            for cuerpo in cuerpos:
                parciales = {""}
                for simbolo in cuerpo:
                    opciones = {""} if cuerpo == EPSILON else (
                        lenguajes.get(simbolo, set()) if simbolo.isupper() else {simbolo}
                    )
                    parciales = {x + y for x in parciales for y in opciones
                                 if len(x) + len(y) <= max_largo}
                nuevas = parciales - lenguajes[cabeza]
                if nuevas:
                    lenguajes[cabeza].update(nuevas)
                    cambio = True
        if not cambio:
            return lenguajes.get(g.inicio, set())


class Laboratorio7Tests(unittest.TestCase):
    def test_gramaticas_y_equivalencia(self):
        for ruta in sorted((BASE / "gramaticas").glob("*.txt")):
            with self.subTest(ruta=ruta.name):
                original = leer_gramatica(ruta)
                esperado = lenguaje_acotado(original)
                sin_epsilon, _, _ = eliminar_epsilon(original)
                self.assertEqual(lenguaje_acotado(sin_epsilon), esperado - {""})
                actual, _, _ = eliminar_epsilon(original, conservar_vacia=True)
                self.assertEqual(lenguaje_acotado(actual), esperado)
                actual, _ = eliminar_unitarias(actual)
                self.assertEqual(lenguaje_acotado(actual), esperado)
                actual, _, _ = eliminar_inutiles(actual)
                self.assertEqual(lenguaje_acotado(actual), esperado)
                actual, _, _ = a_fnc(actual)
                self.assertEqual(lenguaje_acotado(actual), esperado)
                for cabeza, cuerpos in actual.reglas.items():
                    for cuerpo in cuerpos:
                        self.assertTrue(
                            (cuerpo == EPSILON and cabeza == actual.inicio)
                            or (len(cuerpo) == 1 and not cuerpo.isupper())
                            or (len(cuerpo) == 2 and cuerpo.isupper()),
                            (ruta.name, cabeza, cuerpo),
                        )

    def test_anulables(self):
        esperados = ({"S", "A", "B", "C"}, {"S", "A", "B", "C", "D"}, {"A", "B"})
        for ruta, esperado in zip(sorted((BASE / "gramaticas").glob("*.txt")), esperados):
            with self.subTest(ruta=ruta.name):
                self.assertEqual(anulables(leer_gramatica(ruta))[0], esperado)

    def test_errores_sintacticos_y_parada(self):
        invalidas = ("s -> a", "S a", "S ->", "S -> a |", "S -> | a",
                    "S -> a ε", "S -> a-b", "S -> a||b", "S -> α")
        with tempfile.TemporaryDirectory() as temporal:
            ruta = Path(temporal) / "mal.txt"
            for linea in invalidas:
                with self.subTest(linea=linea):
                    ruta.write_text(linea + "\n", encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "producción inválida"):
                        leer_gramatica(ruta)
            ruta.write_text("S -> a\nA -> | b\n", encoding="utf-8")
            resultado = subprocess.run(
                [sys.executable, str(BASE / "main.py"),
                 str(BASE / "gramaticas" / "gramatica_1.txt"), str(ruta)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(resultado.returncode, 1)
            self.assertEqual(resultado.stdout, "")
            self.assertIn("mal.txt:2", resultado.stderr)


if __name__ == "__main__":
    unittest.main()
