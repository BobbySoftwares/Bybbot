from typing import TYPE_CHECKING, List
from swag.currencies import Style, Swag
from swag.errors import NotEnoughStyleInBalance, NotEnoughSwagInBalance
from swag.id import AccountId, CagnotteId
from swag.powers.actives.user_actives import Targets
from swag.powers.target import Targets
from ..power import Active
from swag.stylog import stylog
from math import sqrt

if TYPE_CHECKING:
    from swag.blockchain.blockchain import SwagChain


class Embezzlement(Active):
    title = "Détournement de fonds"
    effect = "Permet de voler {} à une €agnotte."
    target = Targets().cagnotte(1)
    cost_factor = 0.5

    minimum_power_points = 10

    @property
    def _x_value(self):
        return Swag(self._raw_x * 1.5)

    def _activation(
        self, chain: "SwagChain", owner_id: AccountId, targets: List[CagnotteId]
    ):
        owner = chain._accounts[owner_id]
        target = chain._accounts[targets[0]]
        target.check_immunity(self)
        try:
            target -= self._x_value
            owner += self._x_value
        except NotEnoughSwagInBalance:
            owner += target.swag_balance
            target.swag_balance = Swag(0)


class DishonestJointVenture(Active):
    title = "Joint-venture malhonnête"
    effect = "Permet de voler {} à une €agnotte."
    target = Targets().cagnotte(1)
    cost_factor = 0.15

    minimum_power_points = 10

    @property
    def _x_value(self):
        return Style(sqrt(self._raw_x / 100_000))

    def _activation(
        self, chain: "SwagChain", owner_id: AccountId, targets: List[CagnotteId]
    ):
        owner = chain._accounts[owner_id]
        target = chain._accounts[targets[0]]
        target.check_immunity(self)
        try:
            target -= self._x_value
            owner += self._x_value
        except NotEnoughStyleInBalance:
            owner += target.style_balance
            target.style_balance = Style(0)
