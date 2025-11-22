"""Demonstration of the Source Mapper functionality.

This script shows how the source mapper maintains bidirectional mappings
between native language source code and translated English code for accurate
error reporting.
"""

from legesher.runtime.source_mapper import get_source_mapper


def main():
    """Demonstrate source mapper functionality."""
    print("=" * 70)
    print("Legesher Source Mapper Demo")
    print("=" * 70)
    print()

    # Get the global source mapper instance
    mapper = get_source_mapper()

    # Example 1: Spanish Python code
    print("Example 1: Spanish Python Code")
    print("-" * 70)

    spanish_source = """# Programa de ejemplo
si verdad:
    imprimir('Hola mundo')
    x = 10 / 0  # Error aquí
    imprimir(x)"""

    english_translated = """# Example program
if True:
    print('Hello world')
    x = 10 / 0  # Error here
    print(x)"""

    # Register the mapping
    mapper.register_mapping("ejemplo_es.py", spanish_source, english_translated)

    print("Native Spanish source:")
    print(spanish_source)
    print()

    print("Translated English source:")
    print(english_translated)
    print()

    # Simulate error reporting
    error_line_english = 4
    native_line = mapper.get_native_line("ejemplo_es.py", error_line_english)
    native_code = mapper.get_native_source_line("ejemplo_es.py", native_line)

    print(f"Error occurred at English line {error_line_english}")
    print(f"Mapped to native line {native_line}")
    print(f"Native code: {native_code}")
    print()

    # Example 2: French Python code
    print("Example 2: French Python Code")
    print("-" * 70)

    french_source = """# Fonction exemple
définir saluer(nom):
    retourner f'Bonjour, {nom}!'

imprimer(saluer('Marie'))"""

    english_translated_fr = """# Example function
def greet(name):
    return f'Hello, {name}!'

print(greet('Marie'))"""

    mapper.register_mapping("exemple_fr.py", french_source, english_translated_fr)

    print("Native French source:")
    print(french_source)
    print()

    # Show line mappings
    print("Line-by-line mapping:")
    for line_num in range(1, mapper.get_line_count("exemple_fr.py") + 1):
        native_code = mapper.get_native_source_line("exemple_fr.py", line_num)
        print(f"  Line {line_num}: {native_code}")
    print()

    # Example 3: Arabic Python code
    print("Example 3: Arabic Python Code")
    print("-" * 70)

    arabic_source = """# برنامج بسيط
طباعة('مرحبا بالعالم')
س = ٥
طباعة(س)"""

    english_translated_ar = """# Simple program
print('Hello world')
x = 5
print(x)"""

    mapper.register_mapping("مثال.py", arabic_source, english_translated_ar)

    print("Native Arabic source:")
    print(arabic_source)
    print()

    print("All mapped files:")
    for filename in mapper.get_mapped_files():
        line_count = mapper.get_line_count(filename)
        print(f"  {filename} ({line_count} lines)")
    print()

    # Demonstrate error context retrieval
    print("Example 4: Error Context Retrieval")
    print("-" * 70)

    def show_error_context(filename, error_line, context_lines=2):
        """Show error context with surrounding lines."""
        print(f"Error in {filename} at line {error_line}:")

        start_line = max(1, error_line - context_lines)
        end_line = min(mapper.get_line_count(filename), error_line + context_lines)

        for line_num in range(start_line, end_line + 1):
            code = mapper.get_native_source_line(filename, line_num)
            prefix = ">>> " if line_num == error_line else "    "
            print(f"{prefix}{line_num:3d}: {code}")

    # Show context for the Spanish example
    show_error_context("ejemplo_es.py", 4, context_lines=2)
    print()

    print("=" * 70)
    print("Demo complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
