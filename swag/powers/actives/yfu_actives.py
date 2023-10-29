from copy import deepcopy
from typing import TYPE_CHECKING, List
from swag.errors import CantUseYfuPower
from swag.powers.actives.user_actives import Targets
from swag.id import AccountId, GenericId, YfuId
from swag.powers.power import Active
from swag.powers.target import TargetProperty, Targets

if TYPE_CHECKING:
    from swag.blockchain.blockchain import SwagChain


class Kidnapping(Active):
    title = "Kidnapping"
    effect = "Permet de voler une ¥fu ayant au plus {} ₱₱"
    target = Targets().yfu(1)
    cost_factor = 2

    minimum_power_point = 250

    def __init__(self, pp) -> None:
        super().__init__(pp)
        self._raw_x = pp

    @property
    def _x_value(self):
        return self._raw_x

    def _activation(
        self, chain: "SwagChain", owner_id: AccountId, targets: List[YfuId]
    ):
        owner = chain._accounts[owner_id]
        yfu = chain._yfus[targets[0]]
        target = chain._accounts[yfu.owner_id]

        if yfu.power_point > self._x_value:
            raise CantUseYfuPower(owner_id, targets[0])

        target.check_immunity(self)
        target.yfu_wallet.remove(targets[0])
        owner.yfu_wallet.add(targets[0])
        yfu.owner_id = owner_id


class Resurrection(Active):
    title = "Résurrection"
    effect = "Permet de ressusciter une de ses ¥fus."
    target = Targets().yfu(1, [TargetProperty.FROM_CASTER_ONLY])
    cost_factor = 2

    minimum_power_point = 300

    def _activation(
        self, chain: "SwagChain", owner_id: AccountId, targets: List[YfuId]
    ):
        owner = chain._accounts[owner_id]
        yfu = chain._yfus[targets[0]]
        if yfu.owner_id == owner_id:
            owner.yfu_wallet.add(targets[0])
        else:
            raise NotImplementedError


class UltimateResurrection(Active):
    title = "Résurrection suprême"
    effect = "Permet de ressusciter pour soi n'importe quelle ¥fu."
    target = Targets().yfu(1)
    cost_factor = 2.5

    minimum_power_point = 500

    def _activation(
        self, chain: "SwagChain", owner_id: AccountId, targets: List[YfuId]
    ):
        owner = chain._accounts[owner_id]
        yfu = chain._yfus[targets[0]]
        target = chain._accounts[yfu.owner_id]
        if owner_id != yfu.owner_id:
            target.check_immunity(self)
        if targets[0] in target.yfu_wallet:
            raise NotImplementedError
        yfu.owner_id = owner_id
        owner.yfu_wallet.add(targets[0])


class Cloning(Active):
    title = "Clonage"
    effect = "Permet de cloner une ¥fu."
    target = Targets().yfu(1)
    cost_factor = 2

    minimum_power_point = 300

    def _activation(
        self, chain: "SwagChain", owner_id: AccountId, targets: List[YfuId]
    ):
        owner = chain._accounts[owner_id]
        yfu = deepcopy(chain._yfus[targets[0]])
        yfu.owner_id = owner_id
        yfu.id = YfuId(chain.next_yfu_id)
        owner.yfu_wallet.add(yfu)
        chain._yfus[yfu.id] = yfu


# Problematic
class Copy(Active):
    title = "Copie"
    effect = "Permet de copier ponctuellement l'actif d'une ¥fu."
    target = Targets().yfu(1)
    cost_factor = 1.5

    minimum_power_point = 150

    def _activation(
        self, chain: "SwagChain", owner_id: AccountId, targets: List[GenericId]
    ):
        chain._yfus[targets[0]].power._activation(chain, owner_id, targets[1:])


class Clone(Active):
    title = "Clone"
    effect = "Copie de manière permanente le pouvoir d'une ¥fu."
    target = Targets().yfu(1)
    cost_factor = 2

    minimum_power_point = 500

    def _activation(
        self,
        chain: "SwagChain",
        yfu_id: YfuId,
        owner_id: AccountId,
        targets: List[YfuId],
    ):
        # Would it be fun to let the power linked?
        chain._yfus[yfu_id].power = deepcopy(chain._yfus[targets[0]].power)
