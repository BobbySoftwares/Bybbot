from numpy import round, abs
from numpy.random import Generator, Philox

rng = Generator(Philox())


def roll(loc, scale):
    """Génère un entier aléatoire suivant une loi de Cauchy modifiée
    à valeurs dans l'ensemble des entiers naturels.

    Args:
        loc (float): Centre de la distribution de probabilités.
        scale (float): Largeur de la distribution de probabilités.

    Returns:
        int: Nombre aléatoire généré.
    """
    rv = rng.standard_cauchy() * scale + loc
    return int(abs(round(rv)))
