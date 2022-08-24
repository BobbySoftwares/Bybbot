from copy import deepcopy
from typing import TYPE_CHECKING, List
from swag.powers.actives.user_actives import Targetting
from swag.id import AccountId, YfuId
from swag.powers.power import Active

if TYPE_CHECKING:
    from swag.blockchain.blockchain import SwagChain

class Kidnapping(Active):
    title = "Kidnapping"
    effect = "Permet de voler une ¥fu."
    target = Targetting.YFU
    
    minimum_power_point = 200

    def _activation(self, chain: 'SwagChain', owner_id: AccountId, target_id: YfuId):
        owner = chain._accounts[owner_id]
        yfu = chain._yfus[target_id]
        target = chain._accounts[yfu.owner_id]
        target.check_immunity(self)
        target.yfu_wallet.remove(target_id)
        owner.yfu_wallet.add(target_id)
        yfu.owner_id = owner_id


class Resurrection(Active):
    title = "Résurrection"
    effect = "Permet de ressusciter une de ses ¥fus."
    target = Targetting.YFU

    minimum_power_point = 300


    def _activation(self, chain: 'SwagChain', owner_id: AccountId, target_id: YfuId):
        owner = chain._accounts[owner_id]
        yfu = chain._yfus[target_id]
        if yfu.owner_id == owner_id:
            owner.yfu_wallet.add(target_id)
        else:
            raise NotImplementedError


class UltimateResurrection(Active):
    title = "Résurrection suprême"
    effect = "Permet de ressusciter pour soi n'importe quelle ¥fu."
    target = Targetting.YFU

    minimum_power_point = 500

    def _activation(self, chain: 'SwagChain', owner_id: AccountId, target_id: YfuId):
        owner = chain._accounts[owner_id]
        yfu = chain._yfus[target_id]
        target = chain._accounts[yfu.owner_id]
        if owner_id != yfu.owner_id:
            target.check_immunity(self)
        if target_id in target.yfu_wallet:
            raise NotImplementedError
        yfu.owner_id = owner_id
        owner.yfu_wallet.add(target_id)


class Cloning(Active):
    title = "Clonage"
    effect = "Permet de cloner une ¥fu."
    target = Targetting.YFU

    minimum_power_point = 300


    def _activation(self, chain: 'SwagChain', owner_id: AccountId, target_id: YfuId):
        owner = chain._accounts[owner_id]
        yfu = deepcopy(chain._yfus[target_id])
        yfu.owner_id = owner_id
        yfu.id = YfuId(chain.next_yfu_id)
        owner.yfu_wallet.add(yfu)
        chain._yfus[yfu.id] = yfu


# Problematic
class Copy(Active):
    title = "Copie"
    effect = "Permet de copier ponctuellement l'actif d'une ¥fu."
    target = Targetting.YFU

    minimum_power_point = 400

    def _activation(
        self, chain: 'SwagChain', owner_id: AccountId, target_id: YfuId, payload: List
    ):
        chain._yfus[target_id].power._activation(chain, owner_id, *payload)


class Clone(Active):
    title = "Clone"
    tier = "S"
    effect = "Copie de manière permanente le pouvoir d'une ¥fu."
    target = Targetting.YFU

    minimum_power_point = 500

    def _activation(
        self, chain: 'SwagChain', yfu_id: YfuId, owner_id: AccountId, target_id: YfuId
    ):
        # Would it be fun to let the power linked?
        chain._yfus[yfu_id].power = deepcopy(chain._yfus[target_id].power)
