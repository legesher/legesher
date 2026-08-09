# Legesher-translated Python, used by the integration tests.
# Keeping a translated fixture in-tree means the language client is exercised
# the way a user actually hits it, not against English source.

definit gruessen(name):
    """Say hello to someone."""
    wenn name:
        drucken(f"Hallo, {name}!")
    sonst:
        drucken("Hallo, Welt!")
    zurückgeben wahr


definit zaehlen(n):
    für i enthält Bereich(1, n + 1):
        drucken(i)
