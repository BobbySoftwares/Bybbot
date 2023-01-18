from __future__ import annotations
from decimal import Decimal
import hashlib

from attr import attrib, attrs
from typing import TYPE_CHECKING, Union

from swag.yfu import Yfu

from ..powers.power import Active, Passive, Power

if TYPE_CHECKING:
    from ..blockchain import SwagChain

from ..currencies import Style

from ..id import AccountId,CagnotteId, UserId, YfuId

from ..utils import EMOJI_CLAN_YFU
from ..cauchy import roll

from ..block import Block

import string
import os
import random


@attrs(frozen=True, kw_only=True)
class YfuGenerationBlock(Block):
    user_id = attrib(type=UserId, converter=UserId)
    yfu_id = attrib(type=YfuId, converter=YfuId)
    first_name = attrib(type=str)
    last_name = attrib(type=str)
    clan = attrib(type=str)
    power_point = attrib(type=int)
    initial_activation_cost = attrib(type=Style)
    greed = attrib(type=Decimal)
    zenitude = attrib(type=Decimal)
    avatar_asset_key = attrib(type=str)
    power = attrib(type=Power)

    @first_name.default
    def _generate_letter(self):
        return random.choice(string.ascii_uppercase) + "."

    @last_name.default
    def _generate_last_name(self):
        with open(
            "ressources/Yfu/japanese_familly_name.txt", "r", encoding="utf-8"
        ) as f:  # TODO La lecture du fichier devrait se faire ailleurs ?
            return random.choice(f.readlines()).strip("\n")

    @clan.default
    def _generate_clan(self):
        return random.choice(EMOJI_CLAN_YFU)


    def validate(self, db: SwagChain):
        pass  ##TODO

    def execute(self, db: SwagChain):
        db._accounts[self.user_id].yfu_wallet.add(self.yfu_id)
        db._yfus[self.yfu_id] = Yfu(
            owner_id = self.user_id,
            id = self.yfu_id,
            first_name = self.first_name,
            last_name = self.last_name,
            clan = self.clan,
            avatar_url = db._assets[self.avatar_asset_key],
            generation_date = self.timestamp,
            timezone = db._accounts[self.user_id].timezone,
            power_point = self.power_point,
            initial_activation_cost = self.initial_activation_cost,
            activation_cost = self.initial_activation_cost,
            greed = self.greed,
            zenitude = self.zenitude,
            power = self.power,
        )


class YfuPowerActivation(Block):
    yfu_id = attrib(type=YfuId, converter=YfuId)
    target = attrib(type=YfuId | AccountId)

    def validate(self, db: SwagChain):
        pass  ##TODO Voir si il est bien le propriétaire de la Yfu

    def execute(self, db: SwagChain):
        yfu = db._yfus[self.yfu_id]

        yfu.power._activation(db, yfu.owner_id, self.target)
        
@attrs(frozen=True, kw_only=True)
class TokenTransactionBlock(Block):
    giver_id = attrib(type=Union[UserId, CagnotteId])
    recipient_id = attrib(type=Union[UserId, CagnotteId])
    token_id = attrib(type=YfuId)

    def execute(self, db: SwagChain):
        # moving token through account
        db._accounts[self.giver_id].yfu_wallet.remove(self.token_id)
        # write the owner into the token
        db._yfus[self.token_id].owner_id = self.recipient_id
        db._accounts[self.recipient_id].yfu_wallet.add(self.token_id)
        db._accounts[self.recipient_id].register(self.giver_id)


@attrs(frozen=True, kw_only=True)
class RenameYfuBlock(Block):
    user_id = attrib(type=UserId, converter=UserId)
    yfu_id = attrib(type=YfuId, converter=YfuId)
    new_first_name = attrib(type=str)

    def validate(self, db: SwagChain):
        pass  ##TODO Voir si il est bien le propriétaire de la Yfu

    def execute(self, db: SwagChain):
        db._yfus[self.yfu_id].first_name = self.new_first_name
        db._yfus[self.yfu_id].is_baptized = True

class ZenitudeBlock(Block):
    def execute(self, db: SwagChain):
        for yfu_id in db._yfus.keys():
            db._yfus[yfu_id].reduce_activation_cost()