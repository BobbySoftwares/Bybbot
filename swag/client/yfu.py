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
        await interaction.response.defer()

    @yfu.sub_command(name="menu")
    async def open_menu(self, interaction: disnake.ApplicationCommandInteraction):
        """Ouvre le menu des ¥fus"""
        # TODO gérer le cas où il n'y a pas de Yfu

        first_yfu_id = sort_yfu_ids(
            self.swag_client.swagchain.account(interaction.author.id).yfu_wallet
        )[0]

        # Envoie du message publique
        await interaction.send(f"{interaction.author.mention} regarde ses Yfus 👀")

        # Message privée
        await interaction.followup.send(
            embed=YfuEmbed.from_yfu(self.swag_client.swagchain.yfu(first_yfu_id)),
            view=YfuNavigation(self.swag_client, interaction.author.id, first_yfu_id),
            ephemeral=True,
        )

    @yfu.sub_command(name="générer")
    async def generate(self, interaction: disnake.ApplicationCommandInteraction, exemplaire : int = 1):
        """Génère une ¥fu
        
        Parameters
        ----------
        exemplaire : Par défaut 1. Peut être utilisé pour généré plusieurs Yfu en même temps !
        """

        for i in range(exemplaire):

            new_yfu_id = await self.swag_client.swagchain.generate_yfu(UserId(interaction.author.id))
            new_yfu = self.swag_client.swagchain.yfu(new_yfu_id)

            await interaction.send(
                f"{interaction.author.mention}, **{new_yfu.first_name} {new_yfu.last_name}** a rejoint vos rangs à des fins de test !",
                embed=YfuEmbed.from_yfu(new_yfu),
            )
