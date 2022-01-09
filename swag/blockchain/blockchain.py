from decimal import ROUND_DOWN, ROUND_UP, Decimal
from random import choice
from typing import Dict, List
from attr import attrs, attrib

from swag.artefacts.accounts import Accounts, Info
from swag.artefacts.guild import GuildDict
from swag.blocks.swag_blocks import Transaction
from swag.currencies import Swag
from swag.id import CagnotteId, UserId

from ..artefacts import Guild
from ..stylog import unit_style_generation
from ..blocks import (
    ReturnOnInvestment,
    StyleGeneration,
)
from ..block import Block

from ..errors import StyleStillBlocked


@attrs
class SwagChain:
    _chain: List[Block] = attrib()
    _accounts: Accounts = attrib(init=False, factory=Accounts)
    _guilds: Dict[int, Guild] = attrib(init=False, factory=GuildDict)

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

    def account(self, user_id):
        return Info(self._accounts[UserId(user_id)])

    def cagnotte(self, cagnotte_id):
        return Info(self._accounts[CagnotteId(cagnotte_id)])

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
            user_account.style_rate = rate(rank)

    @property
    def forbes(self):
        return sorted(
            (
                (user_id, Info(user_account))
                for user_id, user_account in self._accounts.users.items()
            ),
            key=lambda item: item[1].swag_balance,
            reverse=True,
        )

    @property
    def cagnottes(self):
        return (
            (cagnotte_id, Info(cagnotte))
            for cagnotte_id, cagnotte in self._accounts.cagnottes.items()
        )

    @property
    def swaggest(self):
        for key, _ in self.forbes:
            return key

    def cagnotte_lottery(
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
        winner = choice(tuple(participants))

        self.append(
            Transaction(
                issuer_id=issuer_id,
                giver_id=cagnotte_id,
                recipient_id=winner,
                amount=swag_reward,
            )
        )
        self.append(
            Transaction(
                issuer_id=issuer_id,
                giver_id=cagnotte_id,
                recipient_id=winner,
                amount=style_reward,
            )
        )

        return winner, swag_reward, style_reward

    def share_cagnotte(
        self, cagnotte_id: CagnotteId, issuer_id: UserId, account_list: List[UserId]
    ):
        cagnotte = self._accounts[cagnotte_id]

        if not account_list:
            account_list = [account_id for account_id in self._accounts.users]

        swag_gain = int(cagnotte.swag_balance / len(account_list))
        style_gain = (cagnotte.style_balance / len(account_list)).quantize(
            Decimal(".0001"), rounding=ROUND_DOWN
        )

        for account_id in account_list:
            self.append(
                Transaction(
                    issuer_id=issuer_id,
                    giver_id=cagnotte_id,
                    recipient_id=account_id,
                    amount=swag_gain,
                )
            )
            self.append(
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
            winner_rest, swag_rest, style_rest = self.cagnotte_lottery(
                cagnotte_id, issuer_id, account_list
            )

        return account_list, swag_gain, style_gain, winner_rest, swag_rest, style_rest
