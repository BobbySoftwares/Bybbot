from scipy.stats import cauchy
from numpy import round, abs


def roll(loc, scale):
    """Génère un entier aléatoire suivant une loi de Cauchy modifiée
    à valeurs dans l'ensemble des entiers naturels

    Args:
        loc (float): Centre de la distribution de probabilités
        scale (float): Largeur de la distribution de probabilités

    Returns:
        int: Nombre aléatoire généré
    """
    return int(abs(round(cauchy.rvs(loc, scale))))
