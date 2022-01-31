from swag.artefacts.bonuses import Bonuses
from swag.currencies import Style
from ..stylog import stylog


class Immunity:
    title = "Immunité"
    tier = "SS"
    effect = (
        "Immunise contre les pouvoirs négatifs d'autres waifus (cappé au coût "
        "de construction ?)"
    )

    def protection_cost(self, power):
        return Style(0)


class UltimateImmunity:
    title = "Immunité suprême"
    tier = "SSSS"
    effect = (
        "Immunise contre les pouvoirs négatifs d'autres waifus (cappé au coût "
        "de construction ?)"
    )

    def protection_cost(self, power):
        return Style(0)


class PartialImmunity:
    title = "Immunité contre X"
    effect = "Immunise contre un type X de pouvoir négatif"

    def protection_cost(self, power):
        if self.power_kind is power:
            return Style(0)
        else:
            return Style("inf")


class Protection:
    title = "Protection"
    effect = "Protège contre un coût en style contre tous les effets négatifs"

    @property
    def _x_value(self):
        return int(stylog(self._raw_x))

    def protection_cost(self, power):
        return self._x_value


class PartialProtection:
    title = "Protection contre X"
    effect = "Protège contre un coût en style des effets négatifs de type x"

    @property
    def _x_value(self):
        return int(stylog(self._raw_x))

    def protection_cost(self, power):
        if self.power_kind is power:
            return self._x_value
        else:
            return Style("inf")


class InsolentLuck:
    title = "Chance insolente"
    effect = "Augmente les chances à la loterie"

    @property
    def _x_value(self):
        return int(stylog(self._raw_x))

    def add_bonus(self, bonuses: Bonuses):
        bonuses.lottery_luck += self._x_value


class Begging:
    title = "Mendicité"
    effect = (
        "Quand vous êtes le plus pauvre (en richesse totale), recevez X "
        "swag de tout le monde"
    )


class TaxOptimization:
    title = "Optimisation fiscale"
    effect = "Donne l’avantage X au minage"

    @property
    def _x_value(self):
        return int(stylog(self._raw_x))

    def add_bonus(self, bonuses: Bonuses):
        bonuses.avantage += self._x_value


class MauritiusCommercialBank:
    title = "Mauritius Commercial Bank"
    effect = "Permet de miner X fois de plus par jour"

    @property
    def _x_value(self):
        return int(stylog(self._raw_x))

    def add_bonus(self, bonuses: Bonuses):
        bonuses.minings += self._x_value


class StockPortfolio:
    title = "Portefeuille d’actions"
    effect = "Augmente la swag luck de X"

    @property
    def _x_value(self):
        return self._raw_x

    def add_bonus(self, bonuses: Bonuses):
        bonuses.luck += self._x_value


class StockMarketMastery:
    title = "Maîtrise de la bourse"
    effect = "Augmente la swag base de X"

    @property
    def _x_value(self):
        return self._raw_x

    def add_bonus(self, bonuses: Bonuses):
        bonuses.base += self._x_value


class StateGuardianship:
    title = "Tutelle de l’État"
    effect = "Multiplie le résultat du minage par X"

    @property
    def _x_value(self):
        return stylog(self._raw_x)

    def add_bonus(self, bonuses: Bonuses):
        bonuses.multiplier *= self._x_value


class SuccessfulInvestment:
    title = "Placement fructueux"
    effect = "Augmente le bonus de blocage de X"

    def _x_value(self):
        return stylog(self._raw_x)

    def add_bonus(self, bonuses: Bonuses):
        bonuses.blocking_bonus += self._x_value
