from swag.artefacts.bonuses import Bonuses
from ..power import Passive
from ...stylog import stylog


class InsolentLuck(Passive):
    title = "Chance insolente"
    effect = "Augmente les chances à la loterie"

    minimum_power_point = 10

    def __init__(self, pp) -> None:
        super().__init__(pp)
        self._raw_x = (pp + 1) * 1000

    @property
    def _x_value(self):
        return int(stylog(self._raw_x))

    def add_bonus(self, bonuses: Bonuses):
        bonuses.lottery_luck += self._x_value


class TaxOptimization(Passive):
    title = "Optimisation fiscale"
    effect = "Donne l’avantage X au minage"

    minimum_power_point = 100

    def __init__(self, pp) -> None:
        super().__init__(pp)
        self._raw_x = (pp + 1) * 1000

    @property
    def _x_value(self):
        return int(stylog(self._raw_x))

    def add_bonus(self, bonuses: Bonuses):
        bonuses.avantage += self._x_value


class MauritiusCommercialBank(Passive):
    title = "Mauritius Commercial Bank"
    effect = "Permet de miner X fois de plus par jour"

    minimum_power_point = 500

    def __init__(self, pp) -> None:
        super().__init__(pp)
        self._raw_x = (pp + 1 - self.minimum_power_point) * 1000

    @property
    def _x_value(self):
        return int(stylog(self._raw_x))

    def add_bonus(self, bonuses: Bonuses):
        bonuses.minings += self._x_value


class StockPortfolio(Passive):
    title = "Portefeuille d’actions"
    effect = "Augmente la swag luck de X"

    minimum_power_point = 20

    def __init__(self, pp) -> None:
        super().__init__(pp)
        self._raw_x = pp * 10

    @property
    def _x_value(self):
        return self._raw_x

    def add_bonus(self, bonuses: Bonuses):
        bonuses.luck += self._x_value


class StockMarketMastery(Passive):
    title = "Maîtrise de la bourse"
    effect = "Augmente la swag base de X"

    minimum_power_point = 20

    def __init__(self, pp) -> None:
        super().__init__(pp)
        self._raw_x = pp * 10

    @property
    def _x_value(self):
        return self._raw_x

    def add_bonus(self, bonuses: Bonuses):
        bonuses.base += self._x_value


class StateGuardianship(Passive):
    title = "Tutelle de l’État"
    effect = "Multiplie le résultat du minage par X"

    minimum_power_point = 500

    def __init__(self, pp) -> None:
        super().__init__(pp)
        self._raw_x = (pp + 1 - self.minimum_power_point) * 1000

    @property
    def _x_value(self):
        return stylog(self._raw_x)

    def add_bonus(self, bonuses: Bonuses):
        bonuses.multiplier *= self._x_value


class SuccessfulInvestment(Passive):
    title = "Placement fructueux"
    effect = "Augmente le bonus de blocage de X"

    minimum_power_point = 20

    def __init__(self, pp) -> None:
        super().__init__(pp)
        self._raw_x = (pp + 1 - self.minimum_power_point) * 1000

    @property
    def _x_value(self):
        return stylog(self._raw_x)

    def add_bonus(self, bonuses: Bonuses):
        bonuses.blocking_bonus += self._x_value
