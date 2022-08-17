from swag.artefacts.bonuses import Bonuses
from ...stylog import stylog


class InsolentLuck:
    title = "Chance insolente"
    effect = "Augmente les chances à la loterie"

    @property
    def _x_value(self):
        return int(stylog(self._raw_x))

    def add_bonus(self, bonuses: Bonuses):
        bonuses.lottery_luck += self._x_value


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
