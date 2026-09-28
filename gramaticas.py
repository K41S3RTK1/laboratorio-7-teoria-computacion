"""Lectura y transformaciones de CFG con simbolos de un caracter."""

from collections import deque
from dataclasses import dataclass
from itertools import product
from pathlib import Path
import re
import string


EPSILON = "ε"
LINEA = re.compile(r"\s*([A-Z])\s*(?:->|→)\s*(.*?)\s*")
CUERPO = re.compile(r"(?:[A-Za-z0-9]+|ε)(?:\s*\|\s*(?:[A-Za-z0-9]+|ε))*")


@dataclass
class Gramatica:
    inicio: str
    reglas: dict[str, list[str]]

    def copia(self):
        return Gramatica(self.inicio, {a: list(cuerpos) for a, cuerpos in self.reglas.items()})


def _agregar(reglas, cabeza, cuerpo):
    reglas.setdefault(cabeza, [])
    if cuerpo not in reglas[cabeza]:
        reglas[cabeza].append(cuerpo)


def leer_gramatica(ruta):
    ruta = Path(ruta)
    try:
        lineas = ruta.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"No se pudo leer {ruta}: {exc}") from exc
    reglas = {}
    for numero, linea in enumerate(lineas, 1):
        if not linea.strip():
            continue
        coincidencia = LINEA.fullmatch(linea)
        if not coincidencia or not CUERPO.fullmatch(coincidencia.group(2)):
            raise ValueError(f"{ruta}:{numero}: producción inválida: {linea!r}")
        cabeza, texto = coincidencia.groups()
        for cuerpo in re.split(r"\s*\|\s*", texto):
            _agregar(reglas, cabeza, cuerpo)
    if not reglas:
        raise ValueError(f"{ruta}: el archivo no contiene producciones")
    return Gramatica(next(iter(reglas)), reglas)


def no_definidos(g):
    usados = {c for cuerpos in g.reglas.values() for cuerpo in cuerpos for c in cuerpo if c.isupper()}
    return sorted(usados - g.reglas.keys())


def anulables(g):
    encontrados = set()
    rondas = []
    while True:
        nuevos = []
        for cabeza, cuerpos in g.reglas.items():
            if cabeza in encontrados:
                continue
            testigos = [cuerpo for cuerpo in cuerpos if cuerpo == EPSILON or all(c in encontrados for c in cuerpo)]
            if testigos:
                nuevos.append((cabeza, testigos[0]))
        if not nuevos:
            return encontrados, rondas
        rondas.append(nuevos)
        encontrados.update(cabeza for cabeza, _ in nuevos)


def _nuevo_simbolo(ocupados):
    for simbolo in string.ascii_uppercase[::-1]:
        if simbolo not in ocupados:
            ocupados.add(simbolo)
            return simbolo
    raise ValueError("Se agotaron los no terminales individuales A-Z")


def eliminar_epsilon(g, conservar_vacia=False):
    """Devuelve (gramatica, rondas_anulables, expansiones).

    Una expansion guarda (cabeza, cuerpo, variantes), incluyendo el caso
    vacio en la traza. Solo el nuevo inicial puede conservar epsilon.
    """
    nulos, rondas = anulables(g)
    reglas = {}
    expansiones = []
    for cabeza, cuerpos in g.reglas.items():
        reglas.setdefault(cabeza, [])
        for cuerpo in cuerpos:
            if cuerpo == EPSILON:
                continue
            posiciones = [i for i, c in enumerate(cuerpo) if c in nulos]
            variantes = []
            for conservar in product((True, False), repeat=len(posiciones)):
                borrar = {posiciones[i] for i, queda in enumerate(conservar) if not queda}
                variante = "".join(c for i, c in enumerate(cuerpo) if i not in borrar)
                variantes.append(variante or EPSILON)
                if variante:
                    _agregar(reglas, cabeza, variante)
            expansiones.append((cabeza, cuerpo, variantes))
    inicio = g.inicio
    if conservar_vacia and inicio in nulos:
        ocupados = set(g.reglas) | {c for cuerpos in g.reglas.values() for cuerpo in cuerpos for c in cuerpo if c.isupper()}
        inicio = _nuevo_simbolo(ocupados)
        reglas = {inicio: [g.inicio, EPSILON], **reglas}
    return Gramatica(inicio, reglas), rondas, expansiones


def eliminar_unitarias(g):
    reglas = {}
    clausuras = {}
    for cabeza in g.reglas:
        vistos = {cabeza}
        cola = deque([cabeza])
        while cola:
            actual = cola.popleft()
            for cuerpo in g.reglas.get(actual, []):
                if len(cuerpo) == 1 and cuerpo.isupper() and cuerpo not in vistos:
                    vistos.add(cuerpo)
                    cola.append(cuerpo)
        clausuras[cabeza] = vistos
        reglas[cabeza] = []
        for destino in sorted(vistos):
            for cuerpo in g.reglas.get(destino, []):
                if not (len(cuerpo) == 1 and cuerpo.isupper()):
                    _agregar(reglas, cabeza, cuerpo)
    return Gramatica(g.inicio, reglas), clausuras


def eliminar_inutiles(g):
    productivos = set()
    while True:
        nuevos = {a for a, cuerpos in g.reglas.items() if any(
            cuerpo == EPSILON or all(not c.isupper() or c in productivos for c in cuerpo)
            for cuerpo in cuerpos
        )}
        if nuevos <= productivos:
            break
        productivos |= nuevos
    reglas = {
        a: [cuerpo for cuerpo in cuerpos if all(not c.isupper() or c in productivos for c in cuerpo)]
        for a, cuerpos in g.reglas.items() if a in productivos
    }
    if g.inicio not in productivos:
        return Gramatica(g.inicio, {g.inicio: []}), productivos, {g.inicio}
    alcanzables = {g.inicio}
    cola = deque([g.inicio])
    while cola:
        for cuerpo in reglas[cola.popleft()]:
            for c in cuerpo:
                if c.isupper() and c in reglas and c not in alcanzables:
                    alcanzables.add(c)
                    cola.append(c)
    return Gramatica(g.inicio, {a: cuerpos for a, cuerpos in reglas.items() if a in alcanzables}), productivos, alcanzables


def a_fnc(g):
    """Convierte una CFG sin unitarias ni inutiles a forma normal de Chomsky."""
    ocupados = set(g.reglas) | {c for cuerpos in g.reglas.values() for cuerpo in cuerpos for c in cuerpo if c.isupper()}
    reglas = {a: [] for a in g.reglas}
    terminales = {}
    sufijos = {}

    def variable_terminal(c):
        if c not in terminales:
            variable = _nuevo_simbolo(ocupados)
            terminales[c] = variable
            reglas[variable] = [c]
        return terminales[c]

    def variable_sufijo(secuencia):
        clave = tuple(secuencia)
        if clave not in sufijos:
            variable = _nuevo_simbolo(ocupados)
            sufijos[clave] = variable
            reglas[variable] = []
            if len(secuencia) == 2:
                _agregar(reglas, variable, "".join(secuencia))
            else:
                _agregar(reglas, variable, secuencia[0] + variable_sufijo(secuencia[1:]))
        return sufijos[clave]

    for cabeza, cuerpos in g.reglas.items():
        for cuerpo in cuerpos:
            if cuerpo == EPSILON:
                if cabeza != g.inicio:
                    raise ValueError("Solo el símbolo inicial puede producir ε en FNC")
                _agregar(reglas, cabeza, cuerpo)
            elif len(cuerpo) == 1:
                if cuerpo.isupper():
                    raise ValueError("Queda una producción unitaria")
                _agregar(reglas, cabeza, cuerpo)
            else:
                secuencia = [variable_terminal(c) if not c.isupper() else c for c in cuerpo]
                if len(secuencia) == 2:
                    _agregar(reglas, cabeza, "".join(secuencia))
                else:
                    _agregar(reglas, cabeza, secuencia[0] + variable_sufijo(secuencia[1:]))
    return Gramatica(g.inicio, reglas), terminales, sufijos


def formatear(g):
    return "\n".join(f"{a} → {' | '.join(cuerpos) if cuerpos else '∅'}" for a, cuerpos in g.reglas.items())
