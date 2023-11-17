from decimal import ROUND_HALF_UP, Decimal
from swag.artefacts.bonuses import Bonuses
from ..power import Passive
from ...stylog import stylog


class InsolentLuck(Passive):
    title = "Chance insolente"
    effect = "Augmente les chances à la loterie de {}."

    minimum_power_points = 10

    @property
    def _x_value(self):
        return int(stylog(self._raw_x))

    def add_bonus(self, bonuses: Bonuses):
        bonuses.lottery_luck += self._x_value


class TaxOptimization(Passive):
    title = "Optimisation fiscale"
    effect = "Donne l’avantage {} au minage."

    minimum_power_points = 1000

    @property
    def _x_value(self):
        return int(stylog(self._raw_x))

    def add_bonus(self, bonuses: Bonuses):
        bonuses.avantage += self._x_value


class MauritiusCommercialBank(Passive):
    title = "Mauritius Commercial Bank"
    effect = "Permet de miner {} fois de plus par jour."

    minimum_power_points = 4000

    @property
    def _x_value(self):
        return int(stylog(self._raw_x / 4))

    def add_bonus(self, bonuses: Bonuses):
        bonuses.minings += self._x_value


class StockPortfolio(Passive):
    title = "Portefeuille d’actions"
    effect = "Augmente la $wag Luck de {}."

    minimum_power_points = 1

    @property
    def _x_value(self):
        return self._raw_x / 100

    def add_bonus(self, bonuses: Bonuses):
        bonuses.luck += self._x_value


class StockMarketMastery(Passive):
    title = "Maîtrise de la bourse"
    effect = "Augmente la $wag Base de {}."

    minimum_power_points = 1

    @property
    def _x_value(self):
        return self._raw_x / 100

    def add_bonus(self, bonuses: Bonuses):
        bonuses.base += self._x_value


class StateGuardianship(Passive):
    title = "Tutelle de l’État"
    effect = "Augmente le résultat du minage de {}%."

    minimum_power_points = 500

    @property
    def _x_value(self):
        return Decimal(stylog(self._raw_x / 8) * 100).quantize(
            Decimal(".01"), rounding=ROUND_HALF_UP
        )

    def add_bonus(self, bonuses: Bonuses):
        bonuses.multiplier += self._x_value / 100


class SuccessfulInvestment(Passive):
    title = "Placement fructueux"
    effect = "Augmente le bonus de blocage de {}%."

    minimum_power_points = 1

    @property
    def _x_value(self):
        return Decimal((stylog(self._raw_x)) * 100).quantize(
            Decimal(".01"), rounding=ROUND_HALF_UP
        )

    def add_bonus(self, bonuses: Bonuses):
        bonuses.blocking_bonus += self._x_value
