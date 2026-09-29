# Legesher-translated Python in Arabic, used by the integration tests
# (CORE-1976). Spelled from the pack's 3.10 vocabulary, like sample_de.py.

تعريف greet(name):
    """Say hello to someone."""
    إذا name:
        طَبْع(f"{name}!")
    إلا:
        طَبْع("!")
    إرجاع صحيح


تعريف count(n):
    لكل i في النطاق(1, n + 1):
        طَبْع(i)
