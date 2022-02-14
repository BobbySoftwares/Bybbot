import asyncio
from multiprocessing.sharedctypes import Value
from turtle import update
from typing import TYPE_CHECKING
import disnake
from swag.blocks.swag_blocks import Transaction
from swag.client import swag
from swag.id import CagnotteId, UserId
from swag.yfu import Yfu
from swag.blocks.yfu_blocks import RenameYfuBlock, YfuGenerationBlock

from .IHS_toolkit import *


async def execute_yfu_command(swag_client, message):
    command_yfu = message.content.split()

    if "générer" in command_yfu:
        yfu_block = YfuGenerationBlock(
            issuer_id=message.author.id,
            user_id=message.author.id,
            yfu_id=swag_client.swagchain.yfu_nbr,
        )
        await swag_client.swagchain.append(yfu_block)

        await message.channel.send(
            f"{message.author.mention}, **{yfu_block.first_name} {yfu_block.last_name}** a rejoint vos rangs à des fins de test !",
            embed=YfuEmbed.from_yfu(swag_client.swagchain._yfus[yfu_block.yfu_id]),
        )
    else:

        # TODO gérer le cas où il n'y a pas de Yfu

        first_yfu_id = sort_yfus_id(
            swag_client.swagchain.account(message.author.id).yfu_wallet
        )[0]

        # Envoie du message publique
        await message.channel.send(f"{message.author.mention} regarde ses Yfus 👀")
        # Message privée #TODO voir comment utiliser le mot clef ephemeral
        await message.channel.send(
            embed=YfuEmbed.from_yfu(swag_client.swagchain.yfu(first_yfu_id)),
            view=YfuNavigation(swag_client, message.author.id, first_yfu_id),
        )


##TODO apparition du bouton "Renommer" et "Activer" dynamique
class YfuNavigation(disnake.ui.View):
    def __init__(self, swag_client, user_id, first_yfu_id):
        super().__init__(timeout=None)

        self.swag_client = swag_client
        self.user_id = user_id
        self.yfu_ids = sort_yfus_id(
            swag_client.swagchain.account(self.user_id).yfu_wallet
        )
        self.yfus = [swag_client.swagchain.yfu(yfu_id) for yfu_id in self.yfu_ids]

        # Generation des options du dropdown de waifu
        for option in yfus_to_select_options(self.yfus):
            self.dropdown_yfu.append_option(
                option
            )  ##TODO gérer quand il y a plus de 25 options

        self.selected_yfu_index = self.yfu_ids.index(first_yfu_id)
        self.update_view()

    @disnake.ui.select(placeholder="Choisis ta Yfu...", row=1)
    async def dropdown_yfu(
        self, select: disnake.ui.Select, interaction: disnake.MessageInteraction
    ):
        self.selected_yfu_index = int(self.dropdown_yfu.values[0])

        self.update_view()

        await self.send_yfu_view(interaction)

    @disnake.ui.button(
        label="Précédente", emoji="⬅", style=disnake.ButtonStyle.blurple, row=2
    )
    async def previous_yfu(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        self.selected_yfu_index -= 1

        self.update_view()

        await self.send_yfu_view(interaction)

    @disnake.ui.button(
        label="Suivante", emoji="➡", style=disnake.ButtonStyle.blurple, row=2
    )
    async def next_yfu(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        self.selected_yfu_index += 1

        self.update_view()

        await self.send_yfu_view(interaction)

    @disnake.ui.button(
        label="Activer", emoji="⚡", style=disnake.ButtonStyle.green, row=2
    )
    async def activate_button(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        # TODO Activer Waifu
        self.update_view()

    @disnake.ui.button(
        label="Montrer", emoji="🎴", style=disnake.ButtonStyle.grey, row=3
    )
    async def show_button(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        await interaction.send(
            f"{UserId(self.user_id)} montre fièrement sa ¥fu !",
            embed=YfuEmbed.from_yfu(self.selected_yfu),
            view=disnake.ui.View(),
        )

    @disnake.ui.button(
        label="Renommer", emoji="✏", style=disnake.ButtonStyle.gray, row=3
    )
    async def rename_button(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):

        await interaction.response.edit_message(
            embed=YfuEmbed.from_yfu(self.selected_yfu),
            view=disnake.ui.View(),  # view vide
        )

        await interaction.send(
            content=f"Quel prénom souhaites-tu donner cette ¥fu ? (Doit commencer par **{self.selected_yfu.first_name[0]}**).",
            ephemeral=True,
        )

        def check_yfu_name(new_yfu_name_message):
            return (
                new_yfu_name_message.author.id == self.user_id
                and new_yfu_name_message.content[0] == self.selected_yfu.first_name[0]
            )

        try:
            name_message = await self.swag_client.discord_client.wait_for(
                "message", timeout=60.0, check=check_yfu_name
            )
        except asyncio.TimeoutError:
            await self.send_yfu_view(
                interaction
            )  # Retour au menu par défaut lors du timeout
        else:

            old_first_name = self.selected_yfu.first_name
            # Generation du bloc de renommage
            renaming_block = RenameYfuBlock(
                issuer_id=self.user_id,
                user_id=self.user_id,
                yfu_id=self.yfu_ids[self.selected_yfu_index],
                new_first_name=name_message.content,
            )
            await self.swag_client.swagchain.append(renaming_block)

            self.update_view()
            await interaction.send(
                f"**{old_first_name} {self.selected_yfu.last_name}** s'appelle maintenant **{renaming_block.new_first_name} {self.selected_yfu.last_name}**.",
                embed=YfuEmbed.from_yfu(self.selected_yfu),
            )

    @disnake.ui.button(
        label="Échanger", emoji="🤝", style=disnake.ButtonStyle.secondary, row=3
    )
    async def exchange_button(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        # Oblige de l'appelle ici à cause du await TODO trouver une meilleure solution.
        exchange_option = await forbes_to_select_options(
            self.swag_client
        ) + cagnottes_to_select_options(self.swag_client)
        await interaction.response.edit_message(
            embed=YfuEmbed.from_yfu(self.selected_yfu),
            view=YfuExchange(
                self.swag_client, self.user_id, self.selected_yfu, exchange_option
            ),
        )

    def update_view(self):

        self.selected_yfu = self.swag_client.swagchain.yfu(
            self.yfu_ids[self.selected_yfu_index]
        )
        # previous button
        if self.selected_yfu_index == 0:
            self.previous_yfu.disabled = True
        else:
            self.previous_yfu.disabled = False

        # next button
        if self.selected_yfu_index >= len(self.yfu_ids) - 1:
            self.next_yfu.disabled = True
        else:
            self.next_yfu.disabled = False

        # activate button
        if (
            self.swag_client.swagchain.account(self.user_id).style_balance
            < self.selected_yfu.activation_cost
        ):
            self.activate_button.style = disnake.ButtonStyle.red
            self.activate_button.disabled = True
        else:
            self.activate_button.style = disnake.ButtonStyle.green
            self.activate_button.disabled = False

    async def send_yfu_view(self, interaction: disnake.MessageInteraction):

        await interaction.response.edit_message(
            embed=YfuEmbed.from_yfu(self.selected_yfu), view=self
        )


class YfuExchange(disnake.ui.View):
    def __init__(self, swag_client, user_id, selected_yfu, select_options):
        super().__init__(timeout=None)

        self.swag_client = swag_client
        self.user_id = user_id
        self.selected_yfu = selected_yfu

        for option in select_options:
            self.dropdown_account.append_option(option)

    @disnake.ui.select(placeholder="Destinataire de la ¥fu...")
    async def dropdown_account(
        self, select: disnake.ui.Select, interaction: disnake.MessageInteraction
    ):
        # On attends que l'utilisateur appuie sur confirmé
        await interaction.response.defer()

    @disnake.ui.button(label="Confirmer", emoji="✅", style=disnake.ButtonStyle.green)
    async def confirm(
        self, confirm_button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        # Si pas de valeur selectionné, alors on ne fait juste rien
        if not self.dropdown_account.values:
            await interaction.response.defer()
            return

        ##TODO methode detection type id en fonction du début
        selected_id = self.dropdown_account.values[0]
        if selected_id.startswith("€"):
            selected_id = CagnotteId(selected_id)
        else:
            selected_id = UserId(selected_id)

        block = Transaction(
            issuer_id=UserId(self.user_id),
            giver_id=UserId(self.user_id),
            recipient_id=selected_id,
            amount=self.selected_yfu.yfu_id,
        )
        await self.swag_client.swagchain.append(block)

        await interaction.response.edit_message(view=disnake.ui.View())

        await interaction.send(
            f"{block.giver_id} cède "
            f"**{self.selected_yfu.first_name} {self.selected_yfu.last_name}** ({self.selected_yfu.yfu_id})"
            f" à {selected_id}",
            embed=YfuEmbed.from_yfu(
                self.swag_client.swagchain.yfu(self.selected_yfu.yfu_id)
            ),
        )

    @disnake.ui.button(label="Annuler", emoji="❌", style=disnake.ButtonStyle.red)
    async def cancel(
        self, cancel_button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        # On revient sur la vu précédente
        await interaction.response.edit_message(
            embed=YfuEmbed.from_yfu(
                self.swag_client.swagchain.yfu(self.selected_yfu.yfu_id)
            ),
            view=YfuNavigation(
                self.swag_client, self.user_id, self.selected_yfu.yfu_id
            ),
        )


class YfuEmbed(disnake.Embed):
    @classmethod
    def from_yfu(cls, yfu: Yfu):
        yfu_dict = {
            "title": f"{yfu.clan} {yfu.first_name} {yfu.last_name}",
            "image": {"url": yfu.avatar_url},
            "color": yfu.YfuRarity.from_power_point(yfu.power_point).get_color(),
            "fields": [
                {"name": yfu.power.name, "value": yfu.power.effect, "inline": False},
                {"name": "Coût", "value": f"{yfu.activation_cost}", "inline": True},
                {"name": "Avidité", "value": f"{yfu.greed}", "inline": True},
                {"name": "Zenitude", "value": f"{yfu.zenitude}", "inline": True},
            ],
            "footer": {
                "text": f"{yfu.generation_date.format('YYYY-MM-DD')} \t{yfu.hash}-{yfu.yfu_id} "
            },
        }
        return disnake.Embed.from_dict(yfu_dict)
