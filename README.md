# Laboratorio 7 - Teoría de la Computación

## Problema 1: programa

Implementación en Python 3.10 o posterior, sin dependencias externas.

```bash
python3 main.py
python3 main.py gramaticas/gramatica_1.txt
python3 -m unittest tests.py
```

Sin argumentos, procesa las tres gramáticas del enunciado. También acepta uno o
varios archivos `.txt`. Primero valida **todos** los archivos y, si hay una línea
inválida, se detiene sin procesar ninguno. El mensaje indica archivo y número de
línea. Acepta `->` o `→`, una mayúscula individual a la izquierda, cuerpos con
letras o dígitos individuales y alternativas separadas por `|`. `ε` solo puede
aparecer como alternativa completa. Ignora líneas vacías.

El programa muestra la gramática original, las rondas de símbolos anulables,
las `2^m` variantes por producción y el resultado sin producciones `ε`.
Consolida variantes duplicadas. Cuando el símbolo inicial es anulable, eliminar
todas las reglas `ε` excluye la cadena vacía; para preservarla se requiere un
nuevo símbolo inicial con una única regla `ε`.

Se incluyen las tres gramáticas impresas en el problema 2. La segunda usa `E`
sin una producción que la defina; el programa lo advierte sin inventar una regla.

## Problema 2: procedimiento

[Solución del problema 2](Problema%202/solucion_problema_2.pdf): eliminación de
producciones ε, producciones unitarias y símbolos inútiles, seguida de la
conversión a Forma Normal de Chomsky.

## Video de demostración

Demostración de la ejecución y la validación de errores (video no listado):
[ver video](https://youtu.be/yFrPmYXiImw).
