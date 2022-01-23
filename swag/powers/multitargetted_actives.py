from typing import List
from swag.blockchain.blockchain import SwagChain
from swag.currencies import Swag
from swag.errors import NotEnoughSwagInBalance
from swag.id import AccountId, UserId
from swag.powers.actives import Targetting


class AfricanPrince:
    title = "Prince africain"
    effect = "Permet de transférer du swag d'un joueur vers un autre (autre que vous)"
    target = Targetting.USERS
    has_value = True

    @property
    def _x_value(self):
        return Swag(self._raw_x)

    def _activation(
        self, chain: SwagChain, owner_id: AccountId, target_id: List[UserId]
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


class BankAdministrationError:
    title = "Erreur de l'administration bancaire"
    tier = "SSS"
    effect = "Permet d'échanger le swag de deux joueurs"
    target = Targetting.USERS
    has_value = False

    def _activation(
        self, chain: SwagChain, owner_id: AccountId, target_id: List[UserId]
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
