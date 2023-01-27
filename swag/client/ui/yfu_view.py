import asyncio
import disnake

from typing import TYPE_CHECKING
from swag.errors import IncorrectYfuName
from swag.id import CagnotteId, UserId, YfuId, get_id_from_str
from swag.powers.target import TargetProperty, TargetType
from swag.yfu import Yfu, YfuRarity
from swag.blocks.yfu_blocks import RenameYfuBlock, TokenTransactionBlock

from .ihs_toolkit import *

if TYPE_CHECKING:
    from swag.yfu import Yfu
    from swag.client import SwagClient

##TODO apparition du bouton "Renommer" et "Activer" dynamique
class YfuNavigation(disnake.ui.View):
    def __init__(self, swag_client : 'SwagClient', user_id : 'UserId', first_yfu_id : 'YfuId'):
        super().__init__(timeout=None)

        self.swag_client = swag_client
        self.user_id = user_id
        self.yfu_ids : List[YfuId] = sort_yfu_ids(
            swag_client.swagchain.account(self.user_id).yfu_wallet
        )
        self.yfus : List[Yfu] = [swag_client.swagchain.yfu(yfu_id) for yfu_id in self.yfu_ids]

        # Generation des options du dropdown de waifu
        self.dropdown_yfu.set_options(yfus_to_select_options(self.yfus))

        self.selected_yfu_id = first_yfu_id
        self.update_view()


    @disnake.ui.string_select(UnlimitedSelectMenu, arg_placeholder="Choisis ta Yfu", arg_row=0)
    async def dropdown_yfu(
        self, select: disnake.ui.StringSelect, interaction: disnake.MessageInteraction
    ):
        self.selected_yfu_id = self.dropdown_yfu.values[0]

        self.update_view()

        await self.send_yfu_view(interaction)

    @disnake.ui.button(
        label="Page précédente", emoji="⬅", style=disnake.ButtonStyle.blurple, row=1
    )
    async def previous_yfu(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        self.dropdown_yfu.go_previous_page()

        self.update_view()

        await self.send_yfu_view(interaction)

    @disnake.ui.button(
        label="Page suivante", emoji="➡", style=disnake.ButtonStyle.blurple, row=1
    )
    async def next_yfu(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        self.dropdown_yfu.go_next_page()

        self.update_view()

        await self.send_yfu_view(interaction)

    @disnake.ui.button(
        label="Activer", emoji="⚡", style=disnake.ButtonStyle.green, row=2
    )
    async def activate_button(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        # TODO Activer Waifu
        self.selected_target = []

        #Si target vide on active le pouvoir
        if not self.selected_yfu.power.target._stack_of_targets :
            await self.activate_yfu_power(self.selected_yfu)
        #Sinon, si il y a des targets, on appelle la vu permettant de gérer les targets
        else:

            await interaction.response.edit_message(
                f"**Choissiez votre cible :**",
                embed=YfuEmbed.from_yfu(self.selected_yfu),
                view=YfuTarget(self)
            )

    async def activate_yfu_power(self,interaction: disnake.MessageInteraction):

        message = f"{UserId(self.user_id)} active sa ¥fu"

        if self.selected_target:
            message += " contre "
            message += ", ".join([str(get_id_from_str(target)) for target in self.selected_target])
            message = " et ".join(message.rsplit(", ", 1))
        
        message += " !"

        #TODO block !

        await interaction.response.edit_message(view=disnake.ui.View())


        await interaction.send(
            message,
            embed=YfuEmbed.from_yfu(self.selected_yfu),
            view=disnake.ui.View(),
        )



    @disnake.ui.button(
        label="Montrer", emoji="🎴", style=disnake.ButtonStyle.grey, row=2
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
        label="Baptiser", emoji="✏", style=disnake.ButtonStyle.gray, row=2
    )
    async def baptize_button(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):

        # TODO choisir quand on peut renommer une Yfu (gratuit 1iere fois puis payant ?)
        await interaction.response.send_modal(YfuRename(self, interaction))

    @disnake.ui.button(
        label="Échanger", emoji="🤝", style=disnake.ButtonStyle.secondary, row=2
    )
    async def exchange_button(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):

        await interaction.response.edit_message(
            embed=YfuEmbed.from_yfu(self.selected_yfu),
            view=YfuExchange(self.swag_client, self.user_id, self.selected_yfu),
        )

    def update_view(self):

        self.selected_yfu = self.swag_client.swagchain.yfu(YfuId(self.selected_yfu_id))

        #Previous/next button
        self.previous_yfu.disabled = self.dropdown_yfu.is_first_page()
        self.next_yfu.disabled = self.dropdown_yfu.is_last_page()

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
    def __init__(self, swag_client, user_id, selected_yfu):
        super().__init__(timeout=None)

        self.swag_client = swag_client
        self.user_id = user_id
        self.selected_yfu = selected_yfu

        self.dropdown_account.set_options(
            forbes_to_select_options(self.swag_client) +
            cagnottes_to_select_options(self.swag_client)
        )

    @disnake.ui.string_select(UnlimitedSelectMenu, arg_placeholder="Choisis le destinataire", arg_row=0)
    async def dropdown_account(
        self, select: disnake.ui.StringSelect, interaction: disnake.MessageInteraction
    ):
        # On attends que l'utilisateur appuie sur confirmé
        await interaction.response.defer()

    @disnake.ui.button(
        label="Page précédente", emoji="⬅", style=disnake.ButtonStyle.blurple, row=1
    )
    async def previous_page(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        self.dropdown_account.go_previous_page()

        self.update_view()

        await self.send_view(interaction)

    @disnake.ui.button(
        label="Page suivante", emoji="➡", style=disnake.ButtonStyle.blurple, row=1
    )
    async def next_page(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        self.dropdown_account.go_next_page()

        self.update_view()

        await self.send_view(interaction)

    @disnake.ui.button(label="Confirmer", emoji="✅", style=disnake.ButtonStyle.green, row=2)
    async def confirm(
        self, confirm_button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        # Si pas de valeur selectionné, alors on ne fait juste rien
        if not self.dropdown_account.values:
            await interaction.response.defer()
            return

        ##TODO methode detection type id en fonction du début
        selected_id = get_id_from_str(self.dropdown_account.values[0])

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

    @disnake.ui.button(label="Annuler", emoji="❌", style=disnake.ButtonStyle.red, row=2)
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

    def update_view(self):

        #Previous/next button
        self.previous_page.disabled = self.dropdown_yfu.is_first_page()
        self.next_page.disabled = self.dropdown_yfu.is_last_page()

    async def send_view(self, interaction: disnake.MessageInteraction):

        await interaction.response.edit_message(view=self)



class YfuTarget(disnake.ui.View):
    def __init__(self, navigation_view : YfuNavigation):
        super().__init__(timeout=None)
        self.nav_view = navigation_view

        #Gestion des options par rapport au type de cible
        target_to_choose = self.nav_view.selected_yfu.power.target._stack_of_targets[len(self.nav_view.selected_target)]

        options = []

        if TargetType.USER in target_to_choose[0] :

            if TargetProperty.CASTER_NOT_INCLUDED in target_to_choose[1]:
                options = options + forbes_to_select_options(self.nav_view.swag_client, exclude=[self.nav_view.user_id])
            else:
                options = options + forbes_to_select_options(self.nav_view.swag_client)

        if TargetType.CAGNOTTE in target_to_choose[0]:
            options = options + cagnottes_to_select_options(self.nav_view.swag_client)

        if TargetType.YFU in target_to_choose[0]:

            if TargetProperty.FROM_CASTER_ONLY in target_to_choose[1]:
                options = options + yfus_to_select_options(self.nav_view.yfus) #yfus de l'utilisateur
            else:
                options = options + yfus_to_select_options([yfu for yfu_id, yfu in self.nav_view.swag_client.swagchain.yfus])

        self.dropdown_target.set_options(options)

    @disnake.ui.string_select(UnlimitedSelectMenu, arg_placeholder="Choisis ta cible", arg_row=0)
    async def dropdown_target(
        self, select: disnake.ui.StringSelect, interaction: disnake.MessageInteraction
    ):
        # On attends que l'utilisateur appuie sur confirmé
        await interaction.response.defer()

    @disnake.ui.button(
        label="Page précédente", emoji="⬅", style=disnake.ButtonStyle.blurple, row=1
    )
    async def previous_page(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        self.dropdown_target.go_previous_page()

        self.update_view()

        await self.send_view(interaction)

    @disnake.ui.button(
        label="Page suivante", emoji="➡", style=disnake.ButtonStyle.blurple, row=1
    )
    async def next_page(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        self.dropdown_target.go_next_page()

        self.update_view()

        await self.send_view(interaction)

    @disnake.ui.button(label="Confirmer", emoji="✅", style=disnake.ButtonStyle.green, row=2)
    async def confirm(
        self, confirm_button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):

        self.nav_view.selected_target.append(self.dropdown_target.values[0])

        #On regarde si assez de cible on été selectionné. Si ce n'est pas le cas, on fait choisir une autre cible
        if len(self.nav_view.selected_target) == len(self.nav_view.selected_yfu.power.target._stack_of_targets):
            await self.nav_view.activate_yfu_power(interaction)
        else:
            await interaction.response.send_message(
                f"**Choissiez la {len(self.nav_view.selected_target) + 1}ème cible :**",
                view=YfuTarget(self.nav_view),
                ephemeral=True
            )

            await interaction.delete_original_message()

    @disnake.ui.button(label="Annuler", emoji="❌", style=disnake.ButtonStyle.red, row=2)
    async def cancel(
        self, cancel_button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        # On revient sur la vu précédente
        await interaction.response.edit_message(
            embed=YfuEmbed.from_yfu(
                self.swag_client.swagchain.yfu(self.nav_view.selected_yfu.id)
            ),
            view=self.nav_view,
        )

    def update_view(self):

        #Previous/next button
        self.previous_page.disabled = self.dropdown_yfu.is_first_page()
        self.next_page.disabled = self.dropdown_yfu.is_last_page()

    async def send_view(self, interaction: disnake.MessageInteraction):

        await interaction.response.edit_message(view=self)
        



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
            yfu_id=self.nav_view.selected_yfu.id,
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
                {"name": yfu.power.type + " " + yfu.power.title, "value": yfu.power.get_effect(), "inline": False},
                {"name": "Coût", "value": f"{yfu.activation_cost}", "inline": True},
                {"name": "Avidité", "value": f"{yfu.greed}", "inline": True},
                {"name": "Zenitude", "value": f"{yfu.zenitude}", "inline": True},
            ],
            "footer": {
                "text": f"{yfu.generation_date.format('YYYY-MM-DD')} \t\t\t\t\t {hex(hash(yfu))}-{yfu.power_point}₱₱-{yfu.id} "
            },
        }
        return disnake.Embed.from_dict(yfu_dict)
