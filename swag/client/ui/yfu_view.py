import asyncio
import disnake
from swag.errors import IncorrectYfuName
from swag.id import CagnotteId, UserId
from swag.yfu import Yfu, YfuRarity
from swag.blocks.yfu_blocks import RenameYfuBlock, TokenTransactionBlock

from .ihs_toolkit import *

##TODO apparition du bouton "Renommer" et "Activer" dynamique
class YfuNavigation(disnake.ui.View):
    def __init__(self, swag_client, user_id, first_yfu_id):
        super().__init__(timeout=None)

        self.swag_client = swag_client
        self.user_id = user_id
        self.yfu_ids = sort_yfu_ids(
            swag_client.swagchain.account(self.user_id).yfu_wallet
        )
        self.yfus = [swag_client.swagchain.yfu(yfu_id) for yfu_id in self.yfu_ids]

        # Generation des options du dropdown de waifu
        ##TODO gérer quand il y a plus de 25 options
        for option in yfus_to_select_options(self.yfus):
            self.dropdown_yfu.append_option(option)

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
        label="Baptiser", emoji="✏", style=disnake.ButtonStyle.gray, row=3
    )
    async def baptize_button(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):

        # TODO choisir quand on peut renommer une Yfu (gratuit 1iere fois puis payant ?)
        await interaction.response.send_modal(YfuRename(self, interaction))

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

        # Baptize button
        # Is disabled if it's already baptized
        self.baptize_button.disabled = self.selected_yfu.is_baptized

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

        block = TokenTransactionBlock(
            issuer_id=UserId(self.user_id),
            giver_id=UserId(self.user_id),
            recipient_id=selected_id,
            token_id=self.selected_yfu.id,
        )
        await self.swag_client.swagchain.append(block)

        await interaction.response.edit_message(view=disnake.ui.View())

        await interaction.send(
            f"{block.giver_id} cède "
            f"**{self.selected_yfu.first_name} {self.selected_yfu.last_name}** ({self.selected_yfu.id})"
            f" à {selected_id}",
            embed=YfuEmbed.from_yfu(
                self.swag_client.swagchain.yfu(self.selected_yfu.id)
            ),
        )

    @disnake.ui.button(label="Annuler", emoji="❌", style=disnake.ButtonStyle.red)
    async def cancel(
        self, cancel_button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        # On revient sur la vu précédente
        await interaction.response.edit_message(
            embed=YfuEmbed.from_yfu(
                self.swag_client.swagchain.yfu(self.selected_yfu.id)
            ),
            view=YfuNavigation(self.swag_client, self.user_id, self.selected_yfu.id),
        )


class YfuRename(disnake.ui.Modal):
    def __init__(
        self,
        navigation_view: YfuNavigation,
        navigation_interaction: disnake.MessageInteraction,
    ) -> None:
        self.nav_view = navigation_view
        self.nav_interaction = navigation_interaction
        components = [
            disnake.ui.TextInput(
                label="Nouveau prénom",
                placeholder=f"Doit commencer par {self.nav_view.selected_yfu.first_name[0]}.",
                custom_id="name",
                style=disnake.TextInputStyle.short,
                max_length=50,
            ),
        ]

        super().__init__(
            title="Renommer une ¥fu", custom_id="rename_yfu", components=components
        )

    async def callback(self, inter: disnake.ModalInteraction) -> None:

        new_yfu_name = inter.text_values["name"]

        if new_yfu_name[0] != self.nav_view.selected_yfu.first_name[0]:
            raise IncorrectYfuName(new_yfu_name)

        old_first_name = self.nav_view.selected_yfu.first_name
        # Generation du bloc de renommage
        renaming_block = RenameYfuBlock(
            issuer_id=self.nav_view.user_id,
            user_id=self.nav_view.user_id,
            yfu_id=self.nav_view.yfu_ids[self.nav_view.selected_yfu_index],
            new_first_name=new_yfu_name,
        )
        await self.nav_view.swag_client.swagchain.append(renaming_block)

        self.nav_view.update_view()

        # edit the navigation view to hide buttons
        await self.nav_interaction.edit_original_message(
            embed=YfuEmbed.from_yfu(self.nav_view.selected_yfu), view=disnake.ui.View()
        )

        await inter.send(
            f"**{old_first_name} {self.nav_view.selected_yfu.last_name}** s'appelle maintenant **"
            f"{renaming_block.new_first_name} {self.nav_view.selected_yfu.last_name}**.",
            embed=YfuEmbed.from_yfu(self.nav_view.selected_yfu),
        )

    async def on_error(self, error: Exception, inter: disnake.ModalInteraction) -> None:
        if type(error) == IncorrectYfuName:
            await inter.response.send_message(
                f"Le nouveau prénom de ta ¥fu **({error.name})** ne commence pas par sa lettre de base.",
                ephemeral=True,
            )
        else:
            await inter.response.send_message(
                "Une erreur de type inconnu est survenue !",
                ephemeral=True,
            )
            print(error)


class YfuEmbed(disnake.Embed):
    @classmethod
    def from_yfu(cls, yfu: Yfu):
        yfu_dict = {
            "title": f"{yfu.clan} {yfu.first_name} {yfu.last_name}",
            "image": {"url": yfu.avatar_url},
            "color": YfuRarity.from_power_point(yfu.power_point).get_color(),
            "fields": [
                {"name": yfu.power.type + " " + yfu.power.title, "value": yfu.power.effect, "inline": False},
                {"name": "Coût", "value": f"{yfu.activation_cost}", "inline": True},
                {"name": "Avidité", "value": f"{yfu.greed}", "inline": True},
                {"name": "Zenitude", "value": f"{yfu.zenitude}", "inline": True},
            ],
            "footer": {
                "text": f"{yfu.generation_date.format('YYYY-MM-DD')} \t\t\t\t\t\t {hex(hash(yfu))}-{yfu.id} "
            },
        }
        return disnake.Embed.from_dict(yfu_dict)
