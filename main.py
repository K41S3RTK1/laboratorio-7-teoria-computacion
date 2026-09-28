#!/usr/bin/env python3
"""Laboratorio 7: validacion y eliminacion de producciones epsilon."""

import argparse
from pathlib import Path
import sys

from gramaticas import EPSILON, eliminar_epsilon, formatear, leer_gramatica, no_definidos


def procesar(ruta, g):
    print(f"\n{'=' * 64}\nArchivo: {ruta}\nSímbolo inicial: {g.inicio}")
    print("Gramática original:\n" + formatear(g))
    indefinidos = no_definidos(g)
    if indefinidos:
        print("Aviso: no terminales sin definición: " + ", ".join(indefinidos))
    resultado, rondas, expansiones = eliminar_epsilon(g)
    print("\n1. Símbolos anulables")
    if not rondas:
        print("   Ninguno")
    for i, ronda in enumerate(rondas, 1):
        print(f"   Ronda {i}: " + ", ".join(f"{a} por {a} → {c}" for a, c in ronda))
    print("\n2. Variantes por producción")
    for cabeza, cuerpo, variantes in expansiones:
        print(f"   {cabeza} → {cuerpo}: {len(variantes)} casos: " + ", ".join(variantes))
    print("\n3. Gramática sin producciones ε:\n" + formatear(resultado))
    if g.inicio in {a for ronda in rondas for a, _ in ronda}:
        print(f"   Nota: se excluye {EPSILON}; para conservar la cadena vacía, "
              "se requiere un nuevo símbolo inicial con una única regla ε.")


def main(argv=None):
    base = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archivos", nargs="*", type=Path, help="archivos de gramática")
    args = parser.parse_args(argv)
    rutas = args.archivos or sorted((base / "gramaticas").glob("*.txt"))
    if not rutas:
        parser.error("no se encontraron archivos de gramática")
    try:
        cargadas = [(ruta, leer_gramatica(ruta)) for ruta in rutas]
    except ValueError as exc:
        print(f"Error de validación: {exc}", file=sys.stderr)
        return 1
    for ruta, gramatica in cargadas:
        procesar(ruta, gramatica)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
