import disnake
from disnake.ext import commands
from swag.blocks import GuildTimezoneUpdate
from swag.blocks.system_blocks import EventGiveaway
from swag.client.ui.yfu_view import YfuEmbed
from swag.currencies import Currency
from swag.id import UserId
from utils import ADMIN_GUILD_ID, GUILD_ID
from ..utils import (
    update_forbes_classement,
    update_the_style,
)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swag import SwagClient


class SwagminCommand(commands.Cog):
    def __init__(self, swag_client: "SwagClient"):
        self.swag_client = swag_client

    @commands.slash_command(name="swagdmin", guild_ids=[GUILD_ID])
    async def swagdmin(self, interaction: disnake.ApplicationCommandInteraction):
        pass

    @swagdmin.sub_command(name="set_timezone", guild_ids=[GUILD_ID])
    async def set_timezone(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        guild_id: str,
        timezone: str,
    ):
        """
        Permet de changer la timezone d'un serveur

        Parameters
        ----------
        guild_id : id du serveur.
        timezone : nouvelle timezone du serveur.
        """
        guild = self.swag_client.discord_client.get_guild(int(guild_id))

        if not interaction.user.guild_permissions.administrator:
            await interaction.send(
                "Désolé, vous devez être administrateur du serveur pour pouvoir utiliser cette commande",
                ephemeral=True,
            )
            return

        await self.swag_client.swagchain.append(
            GuildTimezoneUpdate(
                issuer_id=interaction.author.id, guild_id=guild.id, timezone=timezone
            )
        )

        await interaction.send(
            f"La timezone par défaut du serveur {guild.name} est désormais {timezone}.\n"
            "Les futurs comptes de la $wagChain™ créés sur ce serveur seront "
            "configurés pour utiliser cette timezone par défaut."
        )
