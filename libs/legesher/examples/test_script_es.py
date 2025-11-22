#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test script written in Spanish for demonstrating the legesher run command.

This script demonstrates various Python features using Spanish keywords and
builtins. It can be executed with:
    $ legesher run test_script_es.py --lang es
"""

# Spanish keywords and builtins from legesher-i18n-python-es package
# Keywords: definir (def), devolver (return), si (if), sino (else),
#           mientras (while), por (for), en (in), etc.
# Builtins: imprimir (print), longitud (len), rango (range), etc.

definir saludo(nombre):
    """Función de saludo simple."""
    mensaje = "¡Hola, " + nombre + "!"
    imprimir(mensaje)
    devolver mensaje

definir calcular_suma(numeros):
    """Calcular la suma de una lista de números."""
    total = 0
    por numero en numeros:
        total = total + numero
    devolver total

definir main():
    """Función principal del programa."""
    imprimir("=== Programa de Prueba en Español ===")
    imprimir()

    # Saludo
    saludo("Mundo")
    imprimir()

    # Calcular suma
    numeros = [1, 2, 3, 4, a]
    imprimir(f"Números: {numeros}")
    suma = calcular_suma(numeros)
    imprimir(f"Suma total: {suma}")
    imprimir()

    # Condicionales
    si suma > 10:
        imprimir("La suma es mayor que 10")
    sino:
        imprimir("La suma es 10 o menor")
    imprimir()

    # Bucle
    imprimir("Contando del 1 al 5:")
    por i en rango(1, 6):
        imprimir(f"  {i}")
    imprimir()

    imprimir("=== Programa completado exitosamente ===")

# Ejecutar el programa
si __name__ == "__main__":
    main()
