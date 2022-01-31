from swag.powers.actives.user_actives import Targetting


class Metamorphosis:
    title = "Métamorphose"
    tier = "SS"
    effect = "Copie à volonté de manière permanente le pouvoir d'une waifu"


class IdentityTheft:
    title = "Usurpation d'identité"
    effect = "Permet de rediriger les effets négatifs sur autrui"


class Leverage:
    title = "Moyen de pression"
    effect = "Réduit le coût de la waifu ciblé de X"


class Relocation:
    title = "Délocalisation"
    effect = "Réduit le coût d'utilisation de toutes les waifu du propriétaire de X"


class Cheat:
    title = "Triche"
    effect = "Permet d'augmenter ses chances à la loterie"
    target = Targetting.USER
    has_value = True


class StateGrants:
    title = "Subventions de l’État"
    effect = "Multiplie les résultats d’un minage par X"
    target = Targetting.USER
    has_value = True


class HoleyVein:
    title = "Filon troué"
    effect = "Divise le prochain minage de la cible par X"
    target = Targetting.USER
    has_value = True


class WageCuts:
    title = "Réduction des salaires"
    effect = "Divise le prochain minage des autres mineurs par X"
    target = Targetting.NONE
    has_value = True


class ConvincingThreat:
    title = "Menace convaincante"
    effect = "Réduit le coût d'utilisation de la prochaine waifu par X"
    target = Targetting.NONE
    has_value = True
