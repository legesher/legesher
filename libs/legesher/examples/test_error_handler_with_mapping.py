#!/usr/bin/env python3
"""Test the error handler with source mapping to show native line numbers.

This test creates a scenario where:
1. We have a native language source file (ejemplo.py)
2. We register a mapping for it
3. We manually create an exception from that file
4. The error handler shows the native line number and source code
"""

import sys

sys.path.insert(0, "libs/legesher")

from legesher.runtime import install_error_handler, get_source_mapper
import traceback as tb_module

# Install error handler for Spanish
print("=" * 60)
print("Legesher Error Handler Test - Phase 3")
print("=" * 60)
print()

install_error_handler("es")
print("✓ Error handler installed for Spanish (es)")

# Register a source mapping for a simulated Spanish file
mapper = get_source_mapper()

# Simulate Spanish source code
native_source = """# Ejemplo en Español
definir calcular(numero):
    si numero > 10:
        resultado = valor_inexistente  # ¡Error aquí!
        retornar resultado
    retornar numero

# Llamar la función
calcular(15)"""

# Corresponding English code (what Python actually executes)
english_source = """# Example in English
def calculate(number):
    if number > 10:
        result = nonexistent_value  # Error here!
        return result
    return number

# Call the function
calculate(15)"""

# Register the mapping
mapper.register_mapping("ejemplo.py", native_source, english_source)
print("✓ Source mapping registered for 'ejemplo.py'")
print()

# Show what the native line 4 looks like
print("Native source code (ejemplo.py), line 4:")
print(f"  → {mapper.get_native_source_line('ejemplo.py', 4)}")
print()

print("Now demonstrating error with source mapping...")
print()
print("=" * 60)
print()

# Create a mock traceback by manually creating an exception
# We'll simulate that it came from ejemplo.py line 4
try:
    # Create the actual error
    raise NameError("name 'valor_inexistente' is not defined")
except NameError:
    # Get the exception info
    exc_type, exc_value, exc_tb = sys.exc_info()

    # Create a mock frame that appears to be from ejemplo.py
    # In a real scenario, this would come from the import hook
    # For this test, we'll just show how the error handler formats it

    # Extract current traceback
    tb_list = tb_module.extract_tb(exc_tb)

    # Modify the filename to be ejemplo.py for demonstration
    # This simulates what would happen with the import hook
    mock_frame = tb_module.FrameSummary(
        filename="ejemplo.py",
        lineno=4,  # English line number (will be mapped to native)
        name="calcular",
        line="        result = nonexistent_value  # Error here!",
    )

    # Print explanation
    print("BEFORE Translation (what Python sees):")
    print(f"  File: {mock_frame.filename}")
    print(f"  Line: {mock_frame.lineno} (English source)")
    print(f"  Code: {mock_frame.line}")
    print()

    # Show what the error handler will do
    native_line = mapper.get_native_line("ejemplo.py", 4)
    native_code = mapper.get_native_source_line("ejemplo.py", native_line)

    print("AFTER Translation (what developer sees):")
    print(f"  File: {mock_frame.filename}")
    print(f"  Line: {native_line} (Native Spanish source)")
    print(f"  Code: {native_code}")
    print()

    print("=" * 60)
    print()
    print("Full formatted exception:")
    print()

    # Now trigger the error handler's format_exception
    # This will use our custom formatting
    raise

print()
print("✓ Error handler test complete!")
