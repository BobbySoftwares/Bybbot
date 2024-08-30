from __future__ import annotations
from typing import TYPE_CHECKING, Any, Coroutine, Dict
from re import A
from arrow import Arrow
import disnake

from swag.artefacts.accounts import CagnotteRank
from swag.artefacts.services import Payment
from swag.blockchain.blockchain import SwagChain
from swag.blocks.cagnotte_blocks import (
    CagnotteAddRankBlock,
    CagnotteRemoveRankBlock,
    CancelService,
    ServiceCreation,
    ServiceDelation,
    UseService,
)
from swag.artefacts.services import Service

if TYPE_CHECKING:
    from swag.artefacts.accounts import CagnotteAccount
    from swag.id import CagnotteId, UserId
    from swag.client.client import SwagClient


class CagnotteMenuView(disnake.ui.View):
    def __init__(
        self, cagnotte_id: CagnotteId, user_id: UserId, swag_client: SwagClient
    ):
        super().__init__()

        self.cagnotte_id = cagnotte_id
        self.user_id = user_id
        self.cagnotte_account = swag_client.swagchain._accounts[cagnotte_id]
        self.swag_client = swag_client

        self.cagnotte_embed = CagnotteAccountEmbed.from_cagnotte_account(
            cagnotte_id, self.cagnotte_account, swag_client.discord_client
        )

    @disnake.ui.button(
        label="Services",
        style=disnake.ButtonStyle.green,
        custom_id="service_button",
        emoji="📑",
    )
    async def service_button_callback(
        self, button: disnake.ui.Button, interaction: disnake.Interaction
    ):
        await interaction.response.edit_message(
            embed=CagnotteServiceEmbed(self.swag_client.swagchain),
            view=CagnotteServicesView(
                self.cagnotte_id,
                self.cagnotte_account,
                None,
                self.user_id,
                self.swag_client,
            ),
        )

    @disnake.ui.button(
        label="Rangs",
        style=disnake.ButtonStyle.primary,
        custom_id="rank_button",
        emoji="🪪",
    )
    async def rank_button_callback(
        self, button: disnake.ui.Button, interaction: disnake.Interaction
    ):
        await interaction.response.edit_message(
            "Voici les rangs de la €agnotte",
            embed=CagnotteRankEmbed(self.cagnotte_account),
            view=CagnotteRanksView(
                self.cagnotte_id,
                self.cagnotte_account,
                self.user_id,
                self.swag_client,
            ),
        )


class CagnotteServicesView(disnake.ui.View):
    def __init__(
        self,
        cagnotte_id: CagnotteId,
        cagnotte_account: CagnotteAccount,
        selected_service: Service,
        user_id: UserId,
        swag_client: SwagClient,
    ):
        super().__init__()

        self.cagnotte_id = cagnotte_id
        self.cagnotte_account = cagnotte_account
        self.selected_service = selected_service
        self.user_id = user_id
        self.swag_client = swag_client

        # Ajouter la dropdown menu pour naviguer entre les services si il y a des services

        if len(cagnotte_account.services) > 0:
            self.service_dropdown = disnake.ui.Select(
                placeholder="Sélectionner un service",
                options=[
                    disnake.SelectOption(
                        emoji=service.emojis[0],
                        label=service.name,
                        value=service.name,
                        description=service.type,
                    )
                    for service in cagnotte_account.services
                ],
                custom_id="service_dropdown",
            )
            self.service_dropdown.callback = self.service_dropdown_callback
            self.add_item(self.service_dropdown)

        # Boutons
        self.use_button = disnake.ui.Button(
            style=disnake.ButtonStyle.green,
            label="Utiliser",
            custom_id="use_button",
            emoji="🟢",
        )
        self.use_button.callback = (
            self.use_button_callback
        )  # Associer le callback au bouton
        self.add_item(self.use_button)  # Ajouter le bouton à la vue

        # Bouton grisé si le service est déjà utilisé par l'utilisateur ou si selected_service est None
        self.use_button.disabled = (
            selected_service
            not in swag_client.swagchain._accounts[user_id].subscribed_services
            or selected_service is None
        )

        self.cancel_button = disnake.ui.Button(
            style=disnake.ButtonStyle.red,
            label="Annuler",
            custom_id="cancel_button",
            emoji="🔴",
        )
        self.cancel_button.callback = self.cancel_button_callback
        self.add_item(self.cancel_button)

        # Bouton grisé si le service n'est pas utilisé par l'utilisateur ou si selected_service est None
        self.cancel_button.disabled = (
            selected_service
            in swag_client.swagchain._accounts[user_id].subscribed_services
            or selected_service is None
        )

        # Ajouter des boutons supplémentaires si l'utilisateur est un gestionnaire
        if user_id in cagnotte_account.managers:
            self.create_button = disnake.ui.Button(
                style=disnake.ButtonStyle.primary,
                label="Créer",
                custom_id="create_button",
                emoji="➕",
            )
            self.create_button.callback = self.create_button_callback
            self.add_item(self.create_button)

            self.delete_button = disnake.ui.Button(
                style=disnake.ButtonStyle.danger,
                label="Supprimer",
                custom_id="delete_button",
                emoji="🗑️",
            )
            self.delete_button.callback = self.delete_button_callback
            self.add_item(self.delete_button)

            self.delete_button.disabled = selected_service is None

    # Définition des callbacks

    async def service_dropdown_callback(self, interaction: disnake.Interaction):
        self.selected_service = next(
            (
                service
                for service in self.cagnotte_account.services
                if service.name == self.service_dropdown.values[0]
            ),
            None,
        )
        await interaction.response.edit_message(
            embed=CagnotteServiceEmbed(
                self.swag_client.swagchain, self.selected_service
            ),
            view=CagnotteServicesView(
                self.cagnotte_id,
                self.cagnotte_account,
                self.selected_service,
                self.user_id,
                self.swag_client,
            ),
        )

    async def use_button_callback(self, interaction: disnake.Interaction):
        useBlock = UseService(self.user_id, self.cagnotte_id, self.selected_service)
        self.swag_client.swagchain.append(useBlock)

        await interaction.response.send_message(
            f"{self.user_id} a souscrit au service {self.selected_service.emojis} **{self.selected_service.name}** proposé par la €agnotte {self.cagnotte_id} {self.cagnotte_account.name}."
        )

    async def cancel_button_callback(self, interaction: disnake.Interaction):
        cancelBlock = CancelService(
            self.user_id, self.cagnotte_id, self.selected_service
        )
        self.swag_client.swagchain.append(cancelBlock)

        await interaction.response.send_message(
            f"{self.user_id} a annulé sa souscription au service {self.selected_service.emojis} **{self.selected_service.name}** proposé par la €agnotte {self.cagnotte_id} {self.cagnotte_account.name}."
        )

    async def create_button_callback(self, interaction: disnake.Interaction):

        service_creation_view = CagnotteSelectServiceView(
            self.user_id,
            self.cagnotte_id,
            self.cagnotte_account,
            self.swag_client,
            self,
            CagnotteServiceEmbed(self.swag_client.swagchain, self.selected_service),
        )
        await interaction.response.edit_message(
            embed=service_creation_view.get_embed_from_service_in_creation(),
            view=service_creation_view,
        )

    async def delete_button_callback(self, interaction: disnake.Interaction):
        service_id = self.cagnotte_account.services.index(self.selected_service)
        delationBlock = ServiceDelation(self.user_id, self.cagnotte_id, service_id)
        self.swag_client.swagchain.append(delationBlock)

        await interaction.response.send_message(
            f"{self.user_id} a supprimé le service {self.selected_service.emojis} {self.selected_service.name} de la €agnotte {self.cagnotte_id} {self.cagnotte_account.name}."
        )


class CagnotteRanksView(disnake.ui.View):
    def __init__(
        self,
        cagnotte_id: CagnotteId,
        cagnotte_account: CagnotteAccount,
        user_id: UserId,
        swag_client: SwagClient,
    ):
        super().__init__()

        self.cagnotte_id = cagnotte_id
        self.cagnotte_account = cagnotte_account
        self.user_id = user_id
        self.swag_client = swag_client
        self.selected_rank = None

        self.rank_dropdown = disnake.ui.Select(
            placeholder="Sélectionner un rang",
            options=[
                disnake.SelectOption(
                    emoji=rank.emoji,
                    label=rank.name,
                    value=rank.name,
                    description=rank.description,
                )
                for rank in cagnotte_account.accounts_ranking.values()
            ],
            custom_id="rank_dropdown",
        )
        self.rank_dropdown.callback = self.rank_dropdown_callback

        if len(cagnotte_account.accounts_ranking) > 0:
            self.add_item(self.rank_dropdown)

        self.create_rank_button = disnake.ui.Button(
            style=disnake.ButtonStyle.green,
            label="Créer un rang",
            emoji="➕",
            custom_id="create_rank_button",
        )
        self.create_rank_button.callback = self.create_rank_button_callback
        self.add_item(self.create_rank_button)

        self.delete_rank_button = disnake.ui.Button(
            style=disnake.ButtonStyle.red,
            label="Supprimer un rang",
            emoji="🗑️",
            custom_id="delete_rank_button",
            disabled=self.selected_rank is None,
        )
        self.delete_rank_button.callback = self.delete_rank_button_callback
        self.add_item(self.delete_rank_button)

    async def rank_dropdown_callback(self, interaction: disnake.Interaction):
        self.selected_rank = next(
            (
                rank
                for rank in self.cagnotte_account.accounts_ranking.values()
                if rank.name == self.rank_dropdown.values[0]
            ),
            None,
        )

        self.delete_rank_button.disabled = self.selected_rank is None

        await interaction.response.edit_message(
            embed=CagnotteRankEmbed(self.cagnotte_account, self.selected_rank),
            view=self,
        )

    async def create_rank_button_callback(self, interaction: disnake.Interaction):
        await interaction.response.send_modal(CagnotteRankCreationModal(self))

    async def delete_rank_button_callback(self, interaction: disnake.Interaction):
        rank_name = self.selected_rank.name
        delation_block = CagnotteRemoveRankBlock(
            issuer_id=self.user_id,
            user_id=self.user_id,
            cagnotte_id=self.cagnotte_id,
            rank_name=rank_name,
        )
        self.swag_client.swagchain.append(delation_block)

        await interaction.response.send_message(
            f"{self.user_id} a supprimé le rang {self.selected_rank.emoji} {rank_name} de la €agnotte {self.cagnotte_id} {self.cagnotte_account.name}."
        )


class CagnotteServiceCreationBaseView(disnake.ui.View):
    def __init__(
        self,
        user_id: UserId,
        cagnotte_id: CagnotteId,
        cagnotte_account: CagnotteAccount,
        swag_client: SwagClient,
        previous_view: disnake.ui.View,
        previous_embed: disnake.Embed,
        service_in_creation: Service = None,
    ):
        super().__init__()

        self.user_id = user_id
        self.cagnotte_id = cagnotte_id
        self.cagnotte_account = cagnotte_account
        self.previous_view = previous_view
        self.previous_embed = previous_embed
        self.swag_client = swag_client
        self.service_in_creation = service_in_creation

    @disnake.ui.button(
        style=disnake.ButtonStyle.secondary,
        label="Retour",
        custom_id="back_button",
        emoji="⬅️",
        row=4,  # On le place à 4 pour être sur qu'il soit à la fin
    )
    async def back_button_callback(self, interaction: disnake.Interaction):
        await interaction.response.edit_message(
            embed=self.previous_embed,
            view=self.previous_view,
        )

    def get_embed_from_service_in_creation(self):
        if self.service_in_creation is not None:
            embed = CagnotteServiceEmbed(
                self.swag_client.swagchain, self.service_in_creation
            )
            embed.title = "Création d'un service : " + embed.title
        else:
            embed = disnake.Embed()
            embed.title = "Création d'un service"
            embed.description = "Choississez un type de service à créer"

        return embed


class CagnotteSelectServiceView(CagnotteServiceCreationBaseView):

    @disnake.ui.select(
        placeholder="Sélectionner un type de service",
        options=[
            disnake.SelectOption(
                emoji=service_class.emojis[0],
                label=service_class.type,
                value=service_class.__name__,
            )
            for service_class in Service.__subclasses__()
        ],
        custom_id="service_dropdown",
    )
    async def service_dropdown_callback(
        self, select: disnake.ui.Select, interaction: disnake.Interaction
    ):
        self.selected_service = next(
            (
                service_class
                for service_class in Service.__subclasses__()
                if service_class.__name__ == select.values[0]
            ),
            None,
        )

        if self.selected_service is not None:
            self.service_in_creation = self.selected_service(
                cagnotte_id=self.cagnotte_id
            )
            await interaction.response.edit_message(
                embed=self.get_embed_from_service_in_creation(),
                view=CagnotteSelectRankView(
                    self.user_id,
                    self.cagnotte_id,
                    self.cagnotte_account,
                    self.swag_client,
                    self,
                    self.get_embed_from_service_in_creation(),
                    self.service_in_creation,
                ),
            )


class CagnotteSelectRankView(CagnotteServiceCreationBaseView):
    def __init__(
        self,
        user_id: UserId,
        cagnotte_id: CagnotteId,
        cagnotte_account: CagnotteAccount,
        swag_client: SwagClient,
        previous_view: disnake.ui.View,
        previous_embed: disnake.Embed,
        service_in_creation: Service = None,
    ):
        super().__init__(
            user_id=user_id,
            cagnotte_id=cagnotte_id,
            cagnotte_account=cagnotte_account,
            swag_client=swag_client,
            previous_view=previous_view,
            previous_embed=previous_embed,
            service_in_creation=service_in_creation,
        )

        everyoneRank = CagnotteRank(
            "Tout le monde", "Tous les utilisateurs peuvent utiliser ce service.", "👫"
        )
        managersRank = CagnotteRank(
            "Managers Uniquement",
            "Seuls les managers peuvent utiliser ce service.",
            "👑",
        )

        ranks = list(cagnotte_account.accounts_ranking.values()) + [
            everyoneRank,
            managersRank,
        ]

        self.rank_dropdown = disnake.ui.Select(
            options=[
                disnake.SelectOption(
                    label=rank.name[:100],
                    value=rank.name[:100],
                    emoji=rank.emoji[:1],
                    description=rank.description[:100],
                )
                for rank in ranks
            ],
            placeholder="Sélectionner le(s) rang(s) autorisé(s) à utiliser ce service…",
            custom_id="rank_dropdown",
            min_values=1,
            max_values=len(ranks),
        )
        self.rank_dropdown.callback = self.rank_dropdown_callback
        self.add_item(self.rank_dropdown)

    async def rank_dropdown_callback(self, interaction: disnake.Interaction):
        self.selected_ranks = (
            self.rank_dropdown.values
        )  # Store the selected ranks in a list

        if "Tout le monde" in self.selected_ranks:
            self.service_in_creation.authorized_rank = None
        elif "Managers Uniquement" in self.selected_ranks:
            self.service_in_creation.authorized_rank = []
        else:
            self.service_in_creation.authorized_rank = self.selected_ranks

        await interaction.response.edit_message(
            embed=self.get_embed_from_service_in_creation(),
            view=CagnotteSelectPaymentView(
                self.user_id,
                self.cagnotte_id,
                self.cagnotte_account,
                self.swag_client,
                self,
                self.get_embed_from_service_in_creation(),
                self.service_in_creation,
            ),
        )


class CagnotteSelectPaymentView(CagnotteServiceCreationBaseView):
    def __init__(
        self,
        user_id: UserId,
        cagnotte_id: CagnotteId,
        cagnotte_account: CagnotteAccount,
        swag_client: SwagClient,
        previous_view: disnake.ui.View,
        previous_embed: disnake.Embed,
        service_in_creation: Service = None,
    ):
        super().__init__(
            user_id=user_id,
            cagnotte_id=cagnotte_id,
            cagnotte_account=cagnotte_account,
            swag_client=swag_client,
            previous_view=previous_view,
            previous_embed=previous_embed,
            service_in_creation=service_in_creation,
        )

        self.payment_dropdown = disnake.ui.Select(
            options=[
                disnake.SelectOption(
                    emoji=payment_class.emoji,
                    label=payment_class.name,
                    value=payment_class.__name__,
                    description=payment_class.description,
                )
                for payment_class in Payment.__subclasses__()
            ],
            placeholder="Sélectionner un mode de paiement",
            custom_id="payment_dropdown",
        )
        self.payment_dropdown.callback = self.payment_dropdown_callback
        self.add_item(self.payment_dropdown)

        self.reset_button = disnake.ui.Button(
            style=disnake.ButtonStyle.danger,
            label="Réinitialiser les paiements",
            emoji="🔄",
            custom_id="reset_button",
        )

        self.reset_button.callback = self.reset_button_callback
        self.add_item(self.reset_button)

        self.validation_button = disnake.ui.Button(
            style=disnake.ButtonStyle.green,
            label="Continuer",
            emoji="➡️",
            custom_id="validation_button",
        )

        self.validation_button.callback = self.validation_button_callback
        self.add_item(self.validation_button)

    async def payment_dropdown_callback(self, interaction: disnake.Interaction):
        self.selected_payment = next(
            (
                payment_class
                for payment_class in Payment.__subclasses__()
                if payment_class.__name__ == self.payment_dropdown.values[0]
            ),
            None,
        )
        if self.selected_payment is not None:
            await interaction.response.send_modal(
                CagnottePaymentCreationModal(
                    self.selected_payment(), self.service_in_creation, self
                )
            )

    async def reset_button_callback(self, interaction: disnake.Interaction):
        self.service_in_creation.costs = []
        await interaction.response.edit_message(
            message="Les paiements ont été réinitialisés.",
            embed=self.get_embed_from_service_in_creation(),
            view=self,
        )

    async def validation_button_callback(self, interaction: disnake.Interaction):
        await interaction.response.send_modal(
            CagnotteServiceDetailsModal(self.service_in_creation, self)
        )


class CagnotteServiceValidation(CagnotteServiceCreationBaseView):
    def __init__(
        self,
        user_id: UserId,
        cagnotte_id: CagnotteId,
        cagnotte_account: CagnotteAccount,
        swag_client: SwagClient,
        previous_view: disnake.ui.View,
        previous_embed: disnake.Embed,
        service_in_creation: Service = None,
    ):
        super().__init__(
            user_id=user_id,
            cagnotte_id=cagnotte_id,
            cagnotte_account=cagnotte_account,
            swag_client=swag_client,
            previous_view=previous_view,
            previous_embed=previous_embed,
            service_in_creation=service_in_creation,
        )

        self.validation_button = disnake.ui.Button(
            style=disnake.ButtonStyle.green,
            label="Valider",
            emoji="✅",
            custom_id="validation_button",
        )

        self.validation_button.callback = self.validation_button_callback
        self.add_item(self.validation_button)

    async def validation_button_callback(self, interaction: disnake.Interaction):

        # le block !
        service_creation_block = ServiceCreation(
            issuer_id=self.user_id,
            user_id=self.user_id,
            cagnotte_id=self.cagnotte_id,
            service=self.service_in_creation,
        )
        # TODO la génération de block est pété
        await self.swag_client.swagchain.append(service_creation_block)

        await interaction.response.send_message(
            f'Le service {self.service_in_creation.emojis} **{self.service_in_creation.type}** "***{self.service_in_creation.name}***" a été ajouté à la €agnotte **{self.cagnotte_id}** ***{self.cagnotte_account.name}*** par {self.user_id}.'
        )


class CagnottePaymentCreationModal(disnake.ui.Modal):
    def __init__(
        self,
        payment: Payment,
        service_in_creation: Service,
        select_payment_view: CagnotteSelectPaymentView,
    ):
        self.payment = payment
        self.service_in_creation = service_in_creation
        self.select_payment_view = select_payment_view

        components = payment.get_modal_components()

        super().__init__(
            title=f"{payment.name} - Configuration", components=components, timeout=60
        )

    async def callback(
        self, interaction: disnake.ModalInteraction
    ) -> Coroutine[Any, Any, None]:

        try:
            self.payment.update_from_modal(interaction.text_values)
            self.service_in_creation.costs.append(self.payment)
            message = "Le paiement a été configuré avec succès. Vous pouvez ajouter un autre mode de paiement ou continuer."
        except ValueError:
            message = "La configuration du paiement a échoué, regardez bien les exemples. Veuillez réessayer."

        await interaction.response.send_message(
            content=message,
            view=self.select_payment_view,
            embed=self.select_payment_view.get_embed_from_service_in_creation(),
            ephemeral=True,
        )


class CagnotteServiceDetailsModal(disnake.ui.Modal):
    def __init__(
        self,
        service_in_creation: Service,
        previous_service_creation_view: CagnotteServiceCreationBaseView,
    ):
        self.service_in_creation = service_in_creation
        self.previous_service_creation_view = previous_service_creation_view

        components = [
            disnake.ui.TextInput(
                label="Nom du service",
                placeholder="Ex : Service après-vente, L'assurance des mineurs…",
                custom_id="name",
                style=disnake.TextInputStyle.short,
            ),
            disnake.ui.TextInput(
                label="Description du service",
                placeholder="Ex : C'est le meilleur service de l'univers que vous allez adorer !",
                custom_id="description",
                style=disnake.TextInputStyle.long,
            ),
        ]

        super().__init__(
            title=f"{self.service_in_creation.type} - Description",
            components=components,
            timeout=60,
        )

    async def callback(
        self, interaction: disnake.ModalInteraction
    ) -> Coroutine[Any, Any, None]:
        for custom_id, text_input in interaction.text_values.items():
            setattr(self.service_in_creation, custom_id, text_input)

        validation_view = CagnotteServiceValidation(
            user_id=self.previous_service_creation_view.user_id,
            cagnotte_id=self.previous_service_creation_view.cagnotte_id,
            cagnotte_account=self.previous_service_creation_view.cagnotte_account,
            swag_client=self.previous_service_creation_view.swag_client,
            previous_view=self.previous_service_creation_view.previous_view,
            previous_embed=self.previous_service_creation_view.previous_embed,
            service_in_creation=self.service_in_creation,
        )

        await interaction.response.send_message(
            content="Le service a été configuré avec succès. Vous pouvez revenir en arrière ou valider la création du service.",
            view=validation_view,
            embed=validation_view.get_embed_from_service_in_creation(),
            ephemeral=True,
        )


class CagnotteRankCreationModal(disnake.ui.Modal):
    def __init__(self, rank_creation_view: CagnotteRanksView):

        self.rank_creation_view = rank_creation_view

        components = [
            disnake.ui.TextInput(
                label="Emoji du rang",
                placeholder="Ex : 🏅, 🥇, 🥈…",
                custom_id="emoji",
                style=disnake.TextInputStyle.short,
            ),
            disnake.ui.TextInput(
                label="Nom du rang",
                placeholder="Ex : Gold, Silver, Bronze…",
                custom_id="name",
                style=disnake.TextInputStyle.short,
            ),
            disnake.ui.TextInput(
                label="Description du rang",
                placeholder="Ex : Les membres de ce rang ont accès à des services exclusifs…",
                custom_id="description",
                style=disnake.TextInputStyle.long,
            ),
        ]

        super().__init__(
            title=f"Création rang €agnotte {rank_creation_view.cagnotte_account.name}"[
                :45
            ],
            components=components,
            timeout=60,
        )

    async def callback(
        self, interaction: disnake.ModalInteraction
    ) -> Coroutine[Any, Any, None]:
        rank = CagnotteRank(
            name=interaction.text_values["name"],
            description=interaction.text_values["description"],
            emoji=interaction.text_values["emoji"],
        )

        add_rank_block = CagnotteAddRankBlock(
            issuer_id=self.rank_creation_view.user_id,
            user_id=self.rank_creation_view.user_id,
            cagnotte_id=self.rank_creation_view.cagnotte_id,
            rank=rank,
        )

        await self.rank_creation_view.swag_client.swagchain.append(add_rank_block)

        await interaction.response.send_message(
            content=f"Le rang {rank.emoji} **{rank.name}** a été créé avec succès dans la €agnotte ***{self.rank_creation_view.cagnotte_account.name}***.",
            ephemeral=False,
        )


class CagnotteServiceEmbed(disnake.Embed):
    def __init__(self, swagchain: SwagChain, service: Service = None):
        super().__init__()

        if service is not None:
            self.title = f"{service.name}"
            self.description = (
                f"{service.emojis} **{service.type}**\n\n{service.description}"
            )
            self.add_field(
                name="📝 Offre", value=service.get_full_effect(swagchain), inline=False
            )
            if service.authorized_rank is None:
                self.add_field(name="🪪 Rang(s) autorisé(s)", value="Tout le monde")
            elif len(service.authorized_rank) == 0:
                self.add_field(
                    name="🪪 Rang(s) autorisé(s)",
                    value="Managers Uniquement",
                    inline=False,
                )
            else:
                self.add_field(
                    name="🪪 Rang(s) autorisé(s)",
                    value=", ".join(service.authorized_rank),
                    inline=False,
                )

            self.add_field(
                name="💸 Coût",
                value=(
                    "Gratuit"
                    if len(service.costs) == 0
                    else "\n".join([str(cost) for cost in service.costs])
                ),
                inline=False,
            )
        else:
            self.description = "Aucun service sélectionné"


class CagnotteRankEmbed(disnake.Embed):
    def __init__(self, cagnotte_account: CagnotteAccount, rank: CagnotteRank = None):
        super().__init__()

        self.title = "Rangs de la €agnotte " + cagnotte_account.name
        self.color = int("0x3498db", base=16)

        if rank is not None:
            formated_members = "\n".join(
                [
                    f"- {member}"
                    for member in cagnotte_account.accounts_ranking[rank.name].members
                ]
            )
            self.add_field(
                name=f"{rank.emoji} {rank.name}",
                value=rank.description + "\n\n**Membre(s) :** \n" + formated_members,
                inline=False,
            )
        else:
            self.description = "Aucun rang sélectionné"


class CagnotteAccountEmbed(disnake.Embed):
    @classmethod
    def from_cagnotte_account(
        cls,
        cagnotte_id: CagnotteId,
        cagnotte_account: CagnotteAccount,
        bot: disnake.Client,
    ):
        managers = ", ".join(
            [
                bot.get_user(user_id.id).display_name
                for user_id in cagnotte_account.managers
            ]
        )

        services = "\n".join(
            [
                f"- {service.emojis} {service.name} - {service.type}"
                for service in cagnotte_account.services
            ]
        )
        if len(services) == 0:
            services = "N/A"

        yfu_wallet = ", ".join([f"{yfu_id}" for yfu_id in cagnotte_account.yfu_wallet])
        if len(cagnotte_account.yfu_wallet) == 0:
            yfu_wallet = "N/A"

        account_dict = {
            "title": f"€agnotte {cagnotte_account.name}",
            "color": int("0xcfac23", base=16),
            "thumbnail": {
                "url": f"https://dummyimage.com/1024x756/cfac23/333333&text={cagnotte_id.id}"
            },
            "fields": [
                {"name": "👑 Gestionnaire(s)", "value": managers, "inline": False},
                {
                    "name": "💰 $wag",
                    "value": f"{cagnotte_account.swag_balance}",
                    "inline": True,
                },
                {
                    "name": "👛 $tyle",
                    "value": f"{cagnotte_account.style_balance}",
                    "inline": True,
                },
                {"name": "👩‍🎤 ¥fus", "value": yfu_wallet, "inline": True},
                {
                    "name": "📑 Service(s)",
                    "value": services,
                    "inline": False,
                },
            ],
        }

        return disnake.Embed.from_dict(account_dict)
