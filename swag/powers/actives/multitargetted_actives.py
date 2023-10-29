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

    minimum_power_point = 1

    def __init__(self, pp) -> None:
        super().__init__(pp)
        self._raw_x = (pp) * 1000

    @property
    def _x_value(self):
        return Swag(self._raw_x * 3)

    def _activation(
        self, chain: "SwagChain", owner_id: AccountId, target_id: List[UserId]
    ):
        if len(target_id) != 2:
            raise NotImplementedError
        if owner_id in target_id:
            raise NotImplementedError
        target0 = chain._accounts[target_id[0]]
        target1 = chain._accounts[target_id[1]]
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
    tier = "SSS"
    effect = "Permet d'échanger le swag de deux joueurs"
    target = Targets().user(2)
    cost_factor = 3

    minimum_power_point = 16000

    def _activation(
        self, chain: "SwagChain", owner_id: AccountId, target_id: List[UserId]
    ):
        if len(target_id) != 2:
            raise NotImplementedError
        target0 = chain._accounts[target_id[0]]
        target1 = chain._accounts[target_id[1]]
        if owner_id != target_id[0]:
            target0.check_immunity(self)
        if owner_id != target_id[1]:
            target1.check_immunity(self)

        target0_swag = target0.swag_balance
        target1_swag = target1.swag_balance
        target0.swag_balance = target1_swag
        target1.swag_balance = target0_swag
