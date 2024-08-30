from __future__ import annotations
from typing import TYPE_CHECKING

from abc import abstractmethod
from decimal import Decimal
from typing import Dict, List
from arrow import Arrow
from attr import attrib, attrs
import disnake

from swag.currencies import Money, Swag, get_money_from_input
from swag.artefacts.bonuses import Bonuses

if TYPE_CHECKING:
    from swag.block import Block
    from swag.blockchain.blockchain import SwagChain
    from swag.errors import NotEnoughStyleInBalance, NotEnoughSwagInBalance
    from swag.powers.power import Passive
    from swag.id import AccountId, CagnotteId


@attrs(auto_attribs=True)
class Payment:

    @property
    @abstractmethod
    def name(self):
        pass

    @property
    @abstractmethod
    def description(self):
        pass

    @property
    @abstractmethod
    def emoji(self):
        pass

    @property
    @abstractmethod
    def execute(self, swagchain: SwagChain, block: Block, account_client: AccountId):
        pass

    @classmethod
    @abstractmethod
    def get_modal_components(self) -> List[disnake.ui.TextInput]:
        pass

    def update_from_modal(self, data: Dict[str, str]):
        for key, value in data.items():
            if isinstance(getattr(self, key), Money):
                setattr(self, key, get_money_from_input(value))
            else:
                setattr(self, key, int(value))


@attrs(auto_attribs=True)
class oneTimePayment(Payment):
    name = "Paiement unique"
    description = "Le paiement ne se fait qu'une seule fois"
    emoji = "1️⃣"
    amount: Money = attrib(default=Swag(0))

    def execute(self, swagchain: SwagChain, block: Block, account_client: AccountId):

        from swag.blocks.cagnotte_blocks import UseService

        if isinstance(block, UseService):
            swagchain._accounts[account_client] -= self.amount

    def __str__(self) -> str:
        return f"{self.amount} à l'activation"

    def get_modal_components(self) -> List[disnake.ui.TextInput]:
        return [
            disnake.ui.TextInput(
                label="Montant en $wag ou $tyle du paiement",
                placeholder="Ex: 1000 $wag ou 10.5 $tyle...",
                custom_id="amount",
                style=disnake.TextInputStyle.short,
            )
        ]


@attrs(auto_attribs=True)
class Subscription(Payment):
    name = "Abonnement"
    description = "Le paiement sur une fréquence à définir"
    emoji = "🔄"
    frequency_day: int = attrib(default=0)
    lastPayment: Dict[AccountId, Arrow] = attrib(init=False, default={})
    amount: Money = attrib(default=Swag(0))

    def execute(self, swagchain: SwagChain, block: Block, account_client: AccountId):

        from swag.blocks.system_blocks import NewDayBlock
        from swag.blocks.cagnotte_blocks import UseService

        account_tz = swagchain._accounts[account_client].timezone

        # Premier paiement
        if isinstance(block, UseService):
            swagchain._accounts[account_client] -= self.amount
            self.lastPayment[account_client] = Arrow.now(account_tz)

        if isinstance(block, NewDayBlock):
            if (
                block.timestamp.to(account_tz).date()
                > self.lastPayment[account_client].shift(days=self.frequency_day).date()
            ):
                swagchain._accounts[account_client] -= self.amount
                self.lastPayment[account_client] = Arrow.now(account_tz)

    def __str__(self) -> str:
        if self.frequency_day == 1:
            return f"{self.amount} tous les jours"
        return f"{self.amount} tous les {self.frequency_day} jours"

    def get_modal_components(self) -> List[disnake.ui.TextInput]:
        return [
            disnake.ui.TextInput(
                label="Montant en $wag ou $tyle de l'abonnement",
                placeholder="Ex: 1000 $wag ou 10.5 $tyle...",
                custom_id="amount",
                style=disnake.TextInputStyle.short,
            ),
            disnake.ui.TextInput(
                label="Fréquence de l'abonnement (en jours)",
                placeholder="Ex: 1 pour tous les jours, 2 pour tous les 2 jours...",
                custom_id="frequency_day",
                style=disnake.TextInputStyle.short,
            ),
        ]


@attrs(auto_attribs=True)
class MiningPourcentage(Payment):
    name = "Pourcentage de minage"
    description = "Le paiement est prélevé à chaque minage avec un pourcentage"
    emoji = "⛏️"
    pourcentage: int = attrib(default=None)

    def execute(self, swagchain: SwagChain, block: Block, account_client: AccountId):

        from swag.blocks.swag_blocks import Mining

        if isinstance(block, Mining):
            swagchain._accounts[account_client] -= (
                Swag((Decimal(self.pourcentage) / 100)) * block.amount
            )

    def __str__(self) -> str:
        return f"{self.pourcentage}% du minage"

    def get_modal_components(self) -> List[disnake.ui.TextInput]:
        return [
            disnake.ui.TextInput(
                label="Pourcentage du minage",
                placeholder="Ex: 3 pour 3%, 25 pour 25%...",
                custom_id="pourcentage",
                style=disnake.TextInputStyle.short,
            )
        ]


@attrs(auto_attribs=True)
class Service:
    cagnotte_id: CagnotteId
    name: str = attrib(default="")
    description: str = attrib(default="")
    costs: List[Payment] = attrib(default=[])
    authorized_rank: List[str] = attrib(default=None)

    @property
    @abstractmethod
    def type(self):
        pass

    @property
    @abstractmethod
    def emojis(self):
        pass

    @abstractmethod
    def get_full_effect(self, swagchain: SwagChain) -> str:
        pass

    def handle_payments(
        self, swagchain: SwagChain, block: Block, account_client: AccountId
    ):

        try:
            for payment in self.costs:
                payment.execute(swagchain, block, account_client)
        except (NotEnoughSwagInBalance, NotEnoughStyleInBalance) as e:
            self.cancel(swagchain, account_client)
            raise e

    def execute(self, swagchain: SwagChain, account_client: AccountId):
        swagchain._accounts[account_client].subscribed_services.add(self)

    def cancel(self, swagchain: SwagChain, account_client: AccountId):
        swagchain._accounts[account_client].subscribed_services.pop(self)


@attrs(auto_attribs=True)
class PassiveYfuRenting(Service):
    type = "Location de Yfu passive"
    emojis = "🎴🔁"

    def get_full_effect(self, swagchain: SwagChain) -> str:
        cagnotte = swagchain._accounts[self.cagnotte_id]
        bonuses = Bonuses(0, 0, 0, 0, 0, 0, 0)

        for yfu_id in cagnotte.yfu_wallet:
            if issubclass(type(swagchain._yfus[yfu_id].power), Passive):
                swagchain._yfus[yfu_id].power.add_bonus(bonuses)

        return bonuses.__str__().replace(": ", ": +")
