from copy import deepcopy
from typing import List
from swag.blockchain.blockchain import SwagChain
from swag.powers.actives.user_actives import Targetting
from swag.id import AccountId, YfuId


class Kidnapping:
    title = "Kidnapping"
    effect = "Permet de voler une waifu"
    target = Targetting.YFU
    has_value = False

    def _activation(self, chain: SwagChain, owner_id: AccountId, target_id: YfuId):
        owner = chain._accounts[owner_id]
        yfu = chain._yfus[target_id]
        target = chain._accounts[yfu.owner_id]
        target.check_immunity(self)
        target.yfu_wallet.remove(target_id)
        owner.yfu_wallet.add(target_id)
        yfu.owner_id = owner_id


class Resurrection:
    title = "Résurrection"
    effect = "Permet de ressusciter une de ses waifu"
    target = Targetting.YFU
    has_value = False

    def _activation(self, chain: SwagChain, owner_id: AccountId, target_id: YfuId):
        owner = chain._accounts[owner_id]
        yfu = chain._yfus[target_id]
        if yfu.owner_id == owner_id:
            owner.yfu_wallet.add(target_id)
        else:
            raise NotImplementedError


class UltimateResurrection:
    title = "Résurrection suprême"
    effect = "Permet de ressusciter pour soi n'importe quelle waifu"
    target = Targetting.YFU
    has_value = False

    def _activation(self, chain: SwagChain, owner_id: AccountId, target_id: YfuId):
        owner = chain._accounts[owner_id]
        yfu = chain._yfus[target_id]
        target = chain._accounts[yfu.owner_id]
        if owner_id != yfu.owner_id:
            target.check_immunity(self)
        if target_id in target.yfu_wallet:
            raise NotImplementedError
        yfu.owner_id = owner_id
        owner.yfu_wallet.add(target_id)


class Cloning:
    title = "Clonage"
    effect = "Permet de cloner une waifu"
    target = Targetting.YFU
    has_value = False

    def _activation(self, chain: SwagChain, owner_id: AccountId, target_id: YfuId):
        owner = chain._accounts[owner_id]
        yfu = deepcopy(chain._yfus[target_id])
        yfu.owner_id = owner_id
        yfu.id = YfuId(chain.next_yfu_id)
        owner.yfu_wallet.add(yfu)
        chain._yfus[yfu.id] = yfu


class Copy:
    title = "Copie"
    effect = "Permet de copier ponctuellement l'actif d'une waifu"
    target = Targetting.YFU
    has_value = False

    def _activation(
        self, chain: SwagChain, owner_id: AccountId, target_id: YfuId, payload: List
    ):
        chain._yfus[target_id].power._activation(chain, owner_id, *payload)


class Clone:
    title = "Clone"
    tier = "S"
    effect = "Copie de manière permanente le pouvoir d'une waifu"
    target = Targetting.YFU
    has_value = False

    def _activation(
        self, chain: SwagChain, yfu_id: YfuId, owner_id: AccountId, target_id: YfuId
    ):
        # Would it be fun to let the power linked?
        chain._yfus[yfu_id].power = deepcopy(chain._yfus[target_id].power)
