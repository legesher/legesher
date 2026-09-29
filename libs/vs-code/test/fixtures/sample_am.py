# Legesher-translated Python in Amharic, used by the integration tests
# (CORE-1976). Spelled from the pack's 3.10 vocabulary, like sample_de.py.

ግለጽ greet(name):
    """Say hello to someone."""
    ከሆነ name:
        አትም(f"{name}!")
    ያለበለዚያ:
        አትም("!")
    መልስ እውነት


ግለጽ count(n):
    ለእያንዳንዱ i ውስጥ ክልል(1, n + 1):
        አትም(i)
