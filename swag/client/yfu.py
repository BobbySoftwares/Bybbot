from multiprocessing.sharedctypes import Value
from turtle import update
from typing import TYPE_CHECKING
import disnake
from swag.yfu import Yfu
from swag.blocks.yfu_blocks import YfuGenerationBlock


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

        first_yfu_id = swag_client.swagchain.account(message.author.id).yfu_wallet[0]

        # Envoie du message publique
        await message.channel.send(f"{message.author.mention}, regarde ses Yfus 👀")
        # Message privée #TODO voir comment utiliser le mot clef ephemeral
        await message.channel.send(
            embed=YfuEmbed.from_yfu(swag_client.swagchain.yfu(first_yfu_id)),
            view=YfuNavigation(swag_client, message.author.id),
        )


class YfuNavigation(disnake.ui.View):
    def __init__(self, swag_client, user_id):
        super().__init__(timeout=None)

        self.swag_client = swag_client
        self.user_id = user_id
        self.yfu_ids = swag_client.swagchain.account(user_id).yfu_wallet
        self.yfus = [swag_client.swagchain.yfu(yfu_id) for yfu_id in self.yfu_ids]

        # Generation des options du dropdown de waifu
        for index, yfu in enumerate(self.yfus):
            self.dropdown_yfu.append_option(
                disnake.SelectOption(
                    label=f"{yfu.first_name} {yfu.last_name}",
                    description=yfu.power.effect,
                    emoji=yfu.clan,
                    value=index,
                )
            )

        self.selected_yfu_index = 0
        self.update_view()

    @disnake.ui.select(placeholder="Choisis ta Yfu...")
    async def dropdown_yfu(
        self, select: disnake.ui.Select, interaction: disnake.MessageInteraction
    ):
        self.selected_yfu_index = int(self.dropdown_yfu.values[0])

        await self.update_view()

        await self.send_yfu_view(interaction)

    @disnake.ui.button(label="Précédente", emoji="⬅", style=disnake.ButtonStyle.blurple)
    async def previous_yfu(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        self.selected_yfu_index -= 1

        await self.update_view()

        await self.send_yfu_view(interaction)

    @disnake.ui.button(label="Suivante", emoji="➡", style=disnake.ButtonStyle.blurple)
    async def next_yfu(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        self.selected_yfu_index += 1

        await self.update_view()

        await self.send_yfu_view(interaction)

    async def update_view(self):

        if self.selected_yfu_index == 0:
            self.previous_yfu.disabled = True
        else:
            self.previous_yfu.disabled = False

        if self.selected_yfu_index >= len(self.yfu_ids) - 1:
            self.next_yfu.disabled = True
        else:
            self.next_yfu.disabled = False

    async def send_yfu_view(self, interaction: disnake.MessageInteraction):

        selected_yfu = self.swag_client.swagchain.yfu(
            self.yfu_ids[self.selected_yfu_index]
        )
        await interaction.response.edit_message(
            embed=YfuEmbed.from_yfu(selected_yfu), view=self
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
                "text": f"{yfu.generation_date.format('YYYY-MM-DD')} \t{yfu.hash}"
            },
        }
        return disnake.Embed.from_dict(yfu_dict)
