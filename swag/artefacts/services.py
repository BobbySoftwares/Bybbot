from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Dict, List

from abc import abstractmethod
from decimal import Decimal
from arrow import Arrow
from attr import attrib, attrs
import disnake

from swag.currencies import Money, Swag, get_money_from_input
from swag.artefacts.bonuses import Bonuses
from swag.id import CagnotteId, AccountId
from swag.powers.power import Passive

from swag.errors import NotEnoughStyleInBalance, NotEnoughSwagInBalance

if TYPE_CHECKING:
    from swag.block import Block
    from swag.blocks import Transaction
    from swag.blockchain.blockchain import SwagChain


@attrs(auto_attribs=True, kw_only=True)
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

    @abstractmethod
    def get_transaction(
        self,
        swagchain: SwagChain,
        block: Block,
        account_client: AccountId,
        service: Service,
    ) -> Transaction:
        pass

    @classmethod
    @abstractmethod
    def get_modal_components(cls) -> List[disnake.ui.TextInput]:
        pass

    def update_from_modal(self, data: Dict[str, str]):
        for key, value in data.items():
            if isinstance(getattr(self, key), Money):
                setattr(self, key, get_money_from_input(value))
            else:
                setattr(self, key, int(value))


@attrs(auto_attribs=True, kw_only=True)
class OneTimePayment(Payment):
    name = "Paiement unique"
    description = "Le paiement ne se fait qu'une seule fois"
    emoji = "1️⃣"
    amount: Money = attrib(default=Swag(0))

    def get_transaction(
        self,
        swagchain: SwagChain,
        block: Block,
        account_client: AccountId,
        service: Service,
    ) -> Transaction:

        from swag.blocks.cagnotte_blocks import UseService
        from swag.blocks.swag_blocks import Transaction

        if isinstance(block, UseService):

            service_in_block = swagchain._accounts[block.cagnotte_id].services[
                block.service_id
            ]

            if service_in_block == service:

                transaction_block = Transaction(
                    issuer_id=account_client,  # TODO devrait être la cagnotte en vrai
                    giver_id=account_client,
                    recipient_id=service.cagnotte_id,
                    amount=self.amount,
                )

                return transaction_block

    def __str__(self) -> str:
        return f"{self.amount} à l'activation"

    @classmethod
    def get_modal_components(cls) -> List[disnake.ui.TextInput]:
        return [
            disnake.ui.TextInput(
                label="Montant en $wag ou $tyle du paiement",
                placeholder="Ex: 1000 $wag ou 10.5 $tyle...",
                custom_id="amount",
                style=disnake.TextInputStyle.short,
            )
        ]


@attrs(auto_attribs=True, kw_only=True)
class Subscription(Payment):
    name = "Abonnement"
    description = "Le paiement sur une fréquence à définir"
    emoji = "🔄"
    frequency_day: int = attrib(default=0)
    last_payment: Dict[AccountId, Arrow] = attrib(factory=dict)
    amount: Money = attrib(default=Swag(0))

    def get_transaction(
        self,
        swagchain: SwagChain,
        block: Block,
        account_client: AccountId,
        service: Service,
    ) -> Transaction:

        from swag.blocks.system_blocks import NewDayBlock
        from swag.blocks.cagnotte_blocks import UseService
        from swag.blocks.swag_blocks import Transaction

        account_tz = swagchain._accounts[account_client].timezone

        # Premier paiement
        if isinstance(block, UseService):

            transaction_block = Transaction(
                issuer_id=account_client,  # TODO devrait être la cagnotte en vrai
                giver_id=account_client,
                recipient_id=service.cagnotte_id,
                amount=self.amount,
            )

            self.last_payment[account_client] = Arrow.now(account_tz)

            return transaction_block

        if isinstance(block, NewDayBlock):
            if (
                block.timestamp.to(account_tz).date()
                > self.last_payment[account_client]
                .shift(days=self.frequency_day)
                .date()
            ):

                transaction_block = Transaction(
                    issuer_id=account_client,  # TODO devrait être la cagnotte en vrai
                    giver_id=account_client,
                    recipient_id=service.cagnotte_id,
                    amount=self.amount,
                )

                self.last_payment[account_client] = Arrow.now(account_tz)

                return transaction_block

    def __str__(self) -> str:
        if self.frequency_day == 1:
            return f"{self.amount} tous les jours"
        return f"{self.amount} tous les {self.frequency_day} jours"

    @classmethod
    def get_modal_components(cls) -> List[disnake.ui.TextInput]:
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


@attrs(auto_attribs=True, kw_only=True)
class MiningPourcentage(Payment):
    name = "Pourcentage de minage"
    description = "Le paiement est prélevé à chaque minage avec un pourcentage"
    emoji = "⛏️"
    pourcentage: int = attrib(default=None)

    def get_transaction(
        self,
        swagchain: SwagChain,
        block: Block,
        account_client: AccountId,
        service: Service,
    ) -> Transaction:

        from swag.blocks.swag_blocks import Mining
        from swag.blocks.swag_blocks import Transaction

        if isinstance(block, Mining):

            transaction_block = Transaction(
                issuer_id=account_client,  # TODO devrait être la cagnotte en vrai
                giver_id=account_client,
                recipient_id=service.cagnotte_id,
                amount=Swag((Decimal(self.pourcentage) / 100) * block.amount.value),
            )

            return transaction_block

    def __str__(self) -> str:
        return f"{self.pourcentage}% du minage"

    @classmethod
    def get_modal_components(cls) -> List[disnake.ui.TextInput]:
        return [
            disnake.ui.TextInput(
                label="Pourcentage du minage",
                placeholder="Ex: 3 pour 3%, 25 pour 25%...",
                custom_id="pourcentage",
                style=disnake.TextInputStyle.short,
            )
        ]


@attrs(auto_attribs=True, kw_only=True)
class ServiceTransaction:
    service: Service
    payment: Payment
    transaction: Transaction
    success: bool = attrib(default=True)

    def __str__(self):
        if self.success:
            return f"{self.service} - {self.payment}"
        else:
            return f"⚠️ {self.service} - {self.payment}  **Le paiement a échoué, vous ne faites plus partie des bénéficiaires de ce service.**"


@attrs(auto_attribs=True, kw_only=True, eq=False)
class Service:
    cagnotte_id: CagnotteId = attrib(converter=CagnotteId)
    name: str = attrib(default="")
    description: str = attrib(default="")
    costs: List[Payment] = attrib(factory=list)
    authorized_rank: Optional[List[str]] = attrib(default=None)
    beneficiaries: Optional[List[AccountId]] = attrib(factory=list)

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

    async def handle_payments(
        self, swagchain: SwagChain, block: Block, account_client: AccountId
    ) -> List[ServiceTransaction]:

        service_transactions = []

        for payment in self.costs:
            transaction = payment.get_transaction(
                swagchain, block, account_client, self
            )
            if transaction is not None:

                service_transaction = ServiceTransaction(
                    service=self,
                    payment=payment,
                    transaction=transaction,
                )
                try:
                    await swagchain.append(transaction)
                    service_transactions.append(service_transaction)
                except (NotEnoughSwagInBalance, NotEnoughStyleInBalance):
                    # Si le paiement ne peut pas être effectué, on annule la subscription
                    self.cancel(swagchain, account_client)
                    service_transaction.success = False
                    service_transactions.append(service_transaction)
                    break

        return service_transactions

    def execute(self, swagchain: SwagChain, account_client: AccountId):
        swagchain._accounts[account_client].subscribed_services.add(self)
        self.beneficiaries.append(account_client)

    def cancel(self, swagchain: SwagChain, account_client: AccountId):
        swagchain._accounts[account_client].subscribed_services.remove(self)
        self.beneficiaries.remove(account_client)

    def __hash__(self):
        return hash((self.cagnotte_id, self.name))

    def __eq__(self, other):
        if not isinstance(other, Service):
            return False
        return self.cagnotte_id == other.cagnotte_id and self.name == other.name

    def __str__(self):
        return f"**{self.cagnotte_id}** - {self.emojis} {self.type} - {self.name}"


@attrs(auto_attribs=True, kw_only=True, eq=False)
class PassiveYfuRenting(Service):
    type = "Location de Yfu passive"
    emojis = "🎴"

    def get_full_effect(self, swagchain: SwagChain) -> str:
        cagnotte = swagchain._accounts[self.cagnotte_id]
        bonuses = Bonuses(0, 0, 0, 0, 0, 0, 0)
        effet = "(L'effet change en fonction des Yfus dans la €agnotte)\n"

        for yfu_id in cagnotte.yfu_wallet:
            if issubclass(type(swagchain._yfus[yfu_id].power), Passive):
                swagchain._yfus[yfu_id].power.add_bonus(bonuses)

        return effet + str(bonuses).replace(": ", ": +")


@attrs(auto_attribs=True, kw_only=True, eq=False)
class NoEffect(Service):
    type = "Service sans effet"
    emojis = "✨"

    def get_full_effect(self, swagchain: SwagChain) -> str:
        return "Ce service n'a aucun effet particulier, il peut être utilisé à des fins RP."
