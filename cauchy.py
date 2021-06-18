from scipy.stats import cauchy
from numpy import round, abs

def roll(base, luck, n=None):
    """Génère un entier aléatoire en suivant une loi de Cauchy

    Args:
        base (int): Équivalent à la moyenne, là où les valeurs du tirage vont être centrée
        luck (int): Équivalent à un étallement, plus la valeur sera grande, plus la probabilité autour de la moyenne s'étalle
        n ([type], optional): Defaults to None.

    Returns:
        int: le nombre aléatoire généré par une loi de Cauchy
    """
    x = round(cauchy.rvs(base, luck, n if n else 1))
    return abs(x.astype(int, copy=False)[0])