from typing import TYPE_CHECKING, List
from swag.currencies import Swag
from swag.errors import NotEnoughSwagInBalance
from swag.id import AccountId, UserId
from swag.powers.target import TargetProperty, Targets
from ..power import Active

if TYPE_CHECKING:
    from swag.blockchain.blockchain import SwagChain


class AfricanPrince(Active):
    title = "Prince africain"
    effect = "Permet de transférer {} d'un utilisateur vers un autre (sauf vous)."
    target = Targets().user(2, [TargetProperty.CASTER_NOT_INCLUDED])
    cost_factor = 1.25

    minimum_power_points = 1

    @property
    def _x_value(self):
        return Swag(self.power_points * 3_000)

    def _activation(
        self, chain: "SwagChain", owner_id: AccountId, targets: List[UserId]
    ):
        if len(targets) != 2:
            raise NotImplementedError
        if owner_id in targets:
            raise NotImplementedError
        target0 = chain._accounts[targets[0]]
        target1 = chain._accounts[targets[1]]
        target0.check_immunity(self)
        target1.check_immunity(self)
        try:
            target0 -= self._x_value
            target1 += self._x_value
        except NotEnoughSwagInBalance:
            target1 += target0.swag_balance
            target0 = Swag(0)


class BankAdministrationError(Active):
    title = "Erreur de l'administration bancaire"
    effect = "Permet d'échanger le swag de deux joueurs"
    target = Targets().user(2)
    cost_factor = 3

    minimum_power_points = 16000

    def _activation(
        self, chain: "SwagChain", owner_id: AccountId, targets: List[UserId]
    ):
        if len(targets) != 2:
            raise NotImplementedError
        target0 = chain._accounts[targets[0]]
        target1 = chain._accounts[targets[1]]
        if owner_id != targets[0]:
            target0.check_immunity(self)
        if owner_id != targets[1]:
            target1.check_immunity(self)

        target0_swag = target0.swag_balance
        target1_swag = target1.swag_balance
        target0.swag_balance = target1_swag
        target1.swag_balance = target0_swag
