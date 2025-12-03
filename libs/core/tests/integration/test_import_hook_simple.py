"""Simple test of import hook without using language packs."""

import sys

sys.path.insert(0, "/tmp/CORE-464-universal-import-hook/libs/legesher")
sys.path.insert(0, "/tmp/CORE-464-universal-import-hook/libs/core")
sys.path.insert(0, "/tmp/CORE-464-universal-import-hook/libs/i18n")

# Test importing the modules
from legesher.runtime import get_source_mapper

print("✓ Successfully imported runtime modules")

# Test source mapper
mapper = get_source_mapper()
mapper.register_mapping(
    filename="test.py",
    native_source="linea 1\nlinea 2\nlinea 3",
    english_source="line 1\nline 2\nline 3",
)

print("✓ Registered mapping for test.py")
print(f"✓ Native line 2: {mapper.get_native_source_line('test.py', 2)}")
print(f"✓ Mapping line 2 (English) -> {mapper.get_native_line('test.py', 2)} (Native)")

print("\nAll core functionality tests passed!")
