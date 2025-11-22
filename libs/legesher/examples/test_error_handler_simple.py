#!/usr/bin/env python3
"""Simple test of the error handler with source mapping.

This test demonstrates:
1. Installing the error handler
2. Registering source mappings
3. Triggering an error that shows native line numbers and source code
"""

import sys

sys.path.insert(0, "libs/legesher")

from legesher.runtime import install_error_handler, get_source_mapper

# Install error handler for Spanish
print("Installing error handler for Spanish...")
install_error_handler("es")

# Register a source mapping
print("Registering source mapping...")
mapper = get_source_mapper()

# Simulate Spanish source code
native_source = """definir calcular(numero):
    si numero > 10:
        resultado = valor_inexistente
        retornar resultado
    retornar numero"""

# Corresponding English code (what actually runs)
english_source = """def calculate(number):
    if number > 10:
        result = nonexistent_value
        return result
    return number"""

# Register the mapping for a file called "ejemplo.py"
mapper.register_mapping("ejemplo.py", native_source, english_source)

print("Registered mapping for ejemplo.py")
print(f"Native source line 3: '{mapper.get_native_source_line('ejemplo.py', 3)}'")
print()
print("Now triggering an error to demonstrate the error handler...")
print()

# This will trigger a NameError
# The error handler should show line numbers and native source code
nonexistent_value
