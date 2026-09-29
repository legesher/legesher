# Legesher-translated Python in French, used by the integration tests
# (CORE-1976). Spelled from the pack's 3.10 vocabulary, like sample_de.py.

défini greet(name):
    """Say hello to someone."""
    si name:
        imprimer(f"{name}!")
    autre:
        imprimer("!")
    retourner vrai


défini count(n):
    pour i dans plage(1, n + 1):
        imprimer(i)
