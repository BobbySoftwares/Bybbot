from __future__ import annotations
import hashlib

from attr import attrib, attrs
from typing import TYPE_CHECKING
from ..yfu import Yfu, YfuPower

if TYPE_CHECKING:
    from ..blockchain import SwagChain

from ..currencies import Style

from ..id import UserId, YfuId
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
    power_point = attrib(type=float)
    activation_cost = attrib(type=Style)
    greed = attrib(type=float)
    zenitude = attrib(type=float)
    avatar_local_path = attrib(type=str)
    power = attrib(type=YfuPower)
    hash = attrib(type=str)

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

    @power_point.default
    def _roll_powerpoint(self):
        return roll(0, 30)  # TODO

    ##TODO à modifier, car vont dépendre des powerpoint
    @activation_cost.default
    def _roll_cost(self):
        return Style(random.randint(1, 100))

    @greed.default
    def _roll_greed(self):
        return round((random.random() + 1) * 2, 1)  # TODO

    @zenitude.default
    def _roll_zenitude(self):
        return round(random.random(), 1)  # TODO

    @avatar_local_path.default
    def _generate_avatar(self):
        avatar_local_folder = "ressources/Yfu/avatar/psi-1.0/"  # TODO à renseigner ailleurs ? psi different en fonction des powerpoint
        return random.choice(
            [
                os.path.join(avatar_local_folder, file)
                for file in os.listdir(avatar_local_folder)
            ]
        )

    @power.default
    def _generate_power(self):
        # Pouvoir temporaire, en attendant gggto #TODO
        return YfuPower("POUVOIR X", "EFFET DU POUVOIR X")

    @hash.default
    def _calculate_hash(self):
        with open(self.avatar_local_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()

    def validate(self, db: SwagChain):
        pass  ##TODO

    def execute(self, db: SwagChain):
        db._accounts[self.user_id] += self.yfu_id
        db._yfus[self.yfu_id] = Yfu(
            self.user_id,
            self.yfu_id,
            self.first_name,
            self.last_name,
            self.clan,
            self.timestamp,
            db._accounts[self.user_id].timezone,
            self.power_point,
            self.activation_cost,
            self.greed,
            self.zenitude,
            self.avatar_local_path,
            self.power,
            self.hash,
        )


@attrs(frozen=True, kw_only=True)
class RenameYfuBlock(Block):
    user_id = attrib(type=UserId, converter=UserId)
    yfu_id = attrib(type=YfuId, converter=YfuId)
    new_first_name = attrib(type=str)

    def validate(self, db: SwagChain):
        pass  ##TODO

    def execute(self, db: SwagChain):
        db._yfus[self.yfu_id].first_name = self.new_first_name
