from disnake.ext import commands
import disnake
from swag.id import UserId
from utils import GUILD_ID

from .ui.ihs_toolkit import sort_yfu_ids
from .ui.yfu_view import YfuEmbed, YfuNavigation


class YfuCommand(commands.Cog):
    def __init__(self, swag_client):
        self.swag_client = swag_client

    @commands.slash_command(name="yfu", guild_ids=[GUILD_ID])
    async def yfu(self, interaction: disnake.ApplicationCommandInteraction):
        """Ouvre le menu des ¥fus"""
        pass

    @yfu.sub_command(name="menu")
    async def open_menu(self, interaction: disnake.ApplicationCommandInteraction):
        """Ouvre le menu des ¥fus"""
        # TODO gérer le cas où il n'y a pas de Yfu

        yfu_wallet = self.swag_client.swagchain.account(
            interaction.author.id
        ).yfu_wallet

        if len(yfu_wallet) == 0:
            await interaction.response.send_message(
                f"Tu n'as pas encore de ¥fu ! Retape cette commande lorsque tu auras récupérer une ¥fu.",
                ephemeral=True,
            )
        else:
            first_yfu_id = sort_yfu_ids(yfu_wallet)[0]

            # Message privée
            await interaction.response.send_message(
                embed=YfuEmbed.from_yfu(self.swag_client.swagchain.yfu(first_yfu_id)),
                view=YfuNavigation(
                    self.swag_client, interaction.author.id, first_yfu_id
                ),
                ephemeral=True,
            )
