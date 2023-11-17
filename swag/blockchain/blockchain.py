from datetime import datetime
from decimal import ROUND_05UP, ROUND_DOWN, ROUND_UP, Decimal
import os
import random
import shutil
from typing import Dict, List
from arrow import utcnow
from attr import attrs, attrib
from numpy import array, sqrt
from numpy.random import triangular

from swag.artefacts.accounts import Accounts
from swag.artefacts.assets import AssetDict
from swag.artefacts.guild import GuildDict
from swag.blocks.swag_blocks import Transaction
from swag.blocks.system_blocks import AssetUploadBlock
from swag.blocks.yfu_blocks import YfuGenerationBlock

from swag.currencies import Style, Swag
from swag.id import CagnotteId, UserId, YfuId
from swag.powers.power import Active
from swag.yfu import Yfu, YfuDict
from utils import randomly_distribute

from ..artefacts import Guild
from ..stylog import unit_style_generation
from ..blocks import (
    ReturnOnInvestment,
    StyleGeneration,
)
from ..block import Block
from ..cauchy import choice

from .. import powers

from ..errors import StyleStillBlocked
from swag.stylog import stylog


def make_info(obj):
    cls = type(obj)

    class Info(cls):
        def __init__(self, orig):
            self.__dict__ = orig.__dict__

            def setattr(self, __name: str, __value) -> None:
                raise AttributeError

            def delattr(self, __name: str) -> None:
                raise AttributeError

            self.__setattr__ = setattr
            self.__delattr__ = delattr

    return Info(obj)


@attrs
class SwagChain:
    _chain: List[Block] = attrib()
    _accounts: Accounts = attrib(init=False, factory=Accounts)
    _guilds: Dict[int, Guild] = attrib(init=False, factory=GuildDict)
    _yfus: Dict[YfuId, Yfu] = attrib(init=False, factory=YfuDict)
    _assets: Dict[str, str] = attrib(init=False, factory=AssetDict)

    def __attrs_post_init__(self):
        for block in self._chain:
            block.validate(self)
            block.execute(self)

    def append(self, block):
        block.validate(self)
        block.execute(self)
        self._chain.append(block)

    def extend(self, blocks):
        for block in blocks:
            self.append(block)

    def remove(self, block):
        self._chain.remove(block)

    def account(self, user_id):
        return make_info(self._accounts[UserId(user_id)])

    def cagnotte(self, cagnotte_id):
        return make_info(self._accounts[CagnotteId(cagnotte_id)])

    def yfu(self, yfu_id):
        return make_info(self._yfus[YfuId(yfu_id)])

    def _guild(self, guild_id):
        try:
            return self._guilds[guild_id]
        except KeyError:
            self._guilds[guild_id] = Guild()
            return self._guilds[guild_id]

    async def generate_style(self):
        await self.append(
            StyleGeneration(
                issuer_id=self._id,
                amounts={
                    user_id: unit_style_generation(
                        user_account.blocked_swag, user_account.style_rate
                    )
                    for (user_id, user_account) in self._accounts.users.items()
                    if Swag(0) < user_account.blocked_swag
                },
            )
        )

    async def unblock_swag(self):
        for user_id, user_account in self._accounts.users.items():
            try:
                blocked_swag = user_account.blocked_swag
                pending_style = user_account.pending_style
                await self.append(
                    ReturnOnInvestment(
                        issuer_id=self._id,
                        user_id=user_id,
                        amount=pending_style,
                    )
                )
                yield user_id, blocked_swag, pending_style
            except StyleStillBlocked:
                pass

    def update_growth_rates(self):
        forbes = sorted(
            self._accounts.users.values(),
            key=lambda item: item.swag_balance,
            reverse=True,
        )

        # Fonction mathématique, qui permet au premier d'avoir toujours
        # 50%, et à celui à la moitié du classement 10%
        N = len(self._accounts.users)

        def rate(rank):
            return Decimal(100 + 10 / 3 * (pow(16, 1 - rank / N) - 1)).quantize(
                Decimal(".01"), rounding=ROUND_UP
            )

        for rank, user_account in enumerate(forbes):
            user_account.style_rate = (
                rate(rank) + user_account.bonuses(self).blocking_bonus
            )

    async def clean_old_style_gen_block(self):
        ##Get the oldest blocking date of all accounts :
        try:
            oldest_blocking_date = min(
                [
                    user_account.blocking_date
                    for user_account in self._accounts.users.values()
                    if user_account.blocking_date != None
                ]
            )
        except ValueError as e:
            # If no blocking date is found, then we can clean all the StyleGeneration
            oldest_blocking_date = utcnow()

        print(f"Nettoyage de la blockchain avant la date du {oldest_blocking_date}\n")
        ##Get all the StyleGenerationBlock which was added before this date
        old_style_gen_block = [
            block
            for block in self._chain
            if isinstance(block, StyleGeneration)
            and block.timestamp.datetime < oldest_blocking_date
        ]

        ##Remove all those useless block from the chain
        for block in old_style_gen_block:
            await self.remove(block)

    @property
    def forbes(self):
        return sorted(
            (
                (user_id, make_info(user_account))
                for user_id, user_account in self._accounts.users.items()
            ),
            key=lambda item: item[1].swag_balance,
            reverse=True,
        )

    @property
    def cagnottes(self):
        return (
            (cagnotte_id, make_info(cagnotte))
            for cagnotte_id, cagnotte in self._accounts.cagnottes.items()
        )

    @property
    def yfus(self):
        return ((yfu_id, make_info(yfu)) for yfu_id, yfu in self._yfus.items())

    @property
    def swaggest(self):
        for key, _ in self.forbes:
            return key

    @property
    def next_yfu_id(self):
        return len(self._yfus)

    async def cagnotte_lottery(
        self,
        cagnotte_id: CagnotteId,
        issuer_id: UserId,
        participants: List[UserId],
    ):
        cagnotte = self._accounts[cagnotte_id]

        if not participants:
            participants = cagnotte.participants

        swag_reward = cagnotte.swag_balance
        style_reward = cagnotte.style_balance
        weights = array(
            self._accounts[participant].bonuses(self).lottery_luck
            for participant in participants
        )
        weights /= sum(weights)
        winner = choice(tuple(participants), p=weights)

        if swag_reward != Swag(0):
            await self.append(
                Transaction(
                    issuer_id=issuer_id,
                    giver_id=cagnotte_id,
                    recipient_id=winner,
                    amount=swag_reward,
                )
            )
        if style_reward != Style(0):
            await self.append(
                Transaction(
                    issuer_id=issuer_id,
                    giver_id=cagnotte_id,
                    recipient_id=winner,
                    amount=style_reward,
                )
            )

        return winner, swag_reward, style_reward

    async def share_cagnotte(
        self, cagnotte_id: CagnotteId, issuer_id: UserId, account_list: List[UserId]
    ):
        cagnotte = self._accounts[cagnotte_id]

        if not account_list:
            account_list = [account_id for account_id in self._accounts.users]

        swag_gain = Swag(int(cagnotte.swag_balance.value / len(account_list)))
        style_gain = Style(
            (cagnotte.style_balance.value / len(account_list)).quantize(
                Decimal(".0001"), rounding=ROUND_DOWN
            )
        )

        for account_id in account_list:
            if swag_gain != Swag(0):
                await self.append(
                    Transaction(
                        issuer_id=issuer_id,
                        giver_id=cagnotte_id,
                        recipient_id=account_id,
                        amount=swag_gain,
                    )
                )

            if style_gain != Style(0):
                await self.append(
                    Transaction(
                        issuer_id=issuer_id,
                        giver_id=cagnotte_id,
                        recipient_id=account_id,
                        amount=style_gain,
                    )
                )

        if cagnotte.is_empty:
            winner_rest, swag_rest, style_rest = None, None, None
        else:
            winner_rest, swag_rest, style_rest = await self.cagnotte_lottery(
                cagnotte_id, issuer_id, account_list
            )

        return account_list, swag_gain, style_gain, winner_rest, swag_rest, style_rest

    async def generate_yfu(self, author: UserId):
        # Recherche du fichier de l'avatar
        avatar_local_folder = "ressources/Yfu/avatars/GEN_1"
        avatar_file = random.choice(
            [
                os.path.join(avatar_local_folder, file)
                for file in os.listdir(avatar_local_folder)
            ]
        )

        new_yfu_id = YfuId(self.next_yfu_id)

        # Upload de l'avatar par un AssetUploadBlock
        avatar_asset_block = AssetUploadBlock(
            issuer_id=author, asset_key=f"{new_yfu_id}_avatar", local_path=avatar_file
        )

        await self.append(avatar_asset_block)

        # Déplacement de l'image pour pas qu'elle soit une nouvelle fois utilisé par la suite
        used_avatar_local_folder = avatar_local_folder + "/used"
        os.makedirs(used_avatar_local_folder, exist_ok=True)
        shutil.move(avatar_file, used_avatar_local_folder)

        # Powerpoint rolling
        power_points_roll = int(self._accounts.users[author].bonuses(self).unit_roll())

        yfu_powerpoints, power, cost = await self.generate_yfu_power(power_points_roll)

        # Generation de la Yfu
        yfu_block = YfuGenerationBlock(
            issuer_id=author,
            user_id=author,
            yfu_id=new_yfu_id,
            avatar_asset_key=avatar_asset_block.asset_key,
            power_points=yfu_powerpoints,
            power=power,
            initial_activation_cost=cost,
        )

        await self.append(yfu_block)

        return yfu_block.yfu_id

    async def generate_yfu_power(self, powerpoints_roll: int):
        """
        Generate yfu power and Cost
        return : tuple (Powerpoint ,Power, Cost))
        """
        available_power = [
            cls for _, cls in powers.__dict__.items() if isinstance(cls, type)
        ]
        power_found = False

        # PowerPoint de la Yfu, décrivant la puissance générale de la Yfu au vu de son pouvoir et de son coût
        yfu_powerpoints = int(powerpoints_roll / 1_000) + 1

        # Variable aléatoire permettant de faire des yfu qui font pareil que des yfus de puissance inférieur
        # Loi de propabilité 0 et 1 tirée suivant une loi triangulaire de mode 1 (aka p(x) = 2 • x)
        # N'est utilisé que si le pouvoir tiré est actif
        # limiter sert à capper la puissance des yfu 6+ étoiles pour qu'elles restent utilisables et ne
        # coûtent pas déraisonnablement cher à utiliser
        minimum = 0.1 / sqrt(float(powerpoints_roll))
        limiter = min(8_000 / sqrt(float(yfu_powerpoints)), 1)
        dampening = triangular(minimum, limiter, limiter)

        while not power_found:
            power_class = random.choice(available_power)

            if issubclass(power_class, Active):
                effective_powerpoints = int(dampening * yfu_powerpoints)
            else:
                # Pas de Dampening pour les pouvoirs passifs.
                effective_powerpoints = yfu_powerpoints

            if effective_powerpoints >= power_class.minimum_power_points:
                yfu_power = power_class(effective_powerpoints)
                power_found = True

        dampening *= yfu_power._correct_dampening()
        initial_cost = max(
            Style("0.002"),
            Style(4 * dampening * sqrt(yfu_powerpoints / 100)),
        )

        return (yfu_powerpoints, yfu_power, initial_cost)
