import disnake
import time
from swag.blocks.system_blocks import EventGiveaway
from swag.client.ui.yfu_view import YfuEmbed
from swag.currencies import Currency, get_money_class
from swag.id import UserId
from utils import ADMIN_GUILD_ID, GUILD_ID
from swag.utils import update_forbes_classement
from module import Module
from disnake.ext import commands

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swag import SwagClient
    from disnake.ext.commands import Bot


class MaintenanceClient(Module):
    def __init__(self, client, swag_module) -> None:
        self.client = client
        self.swag_module = swag_module

    def register_commands(self):
        self.client.add_cog(AdminCommand(self.client, self.swag_module))


class AdminCommand(commands.Cog):
    def __init__(self, client: "Bot", swag_client: "SwagClient"):
        self.client = client
        self.swag_client = swag_client

    @commands.slash_command(name="admin", guild_ids=[ADMIN_GUILD_ID])
    async def admin(self, interaction: disnake.ApplicationCommandInteraction):
        pass

    @admin.sub_command(name="reboot")
    async def reboot(self, interaction: disnake.ApplicationCommandInteraction):
        """Permet de redémarrer le bot"""

        interaction.send("Redémarrage du serveur lancé !")
        time.sleep(2)

        await self.client.close()

        await update_forbes_classement(
            self.client.get_guild(GUILD_ID),
            self.swag_client,
            self.client,
        )

    @admin.sub_command(name="générer", guild_ids=[ADMIN_GUILD_ID])
    async def generate(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        montant: str,
        monnaie: Currency,
        destinataire: disnake.Member,
    ):
        """
        Génère du $wag ou du $tyle et l'envoie à l'utilisateur

        Parameters
        ----------
        montant : montant à envoyer.
        monnaie : monnaie à envoyer.
        destinataire : utilisateur qui recevra la monnaie.
        """

        amount_to_generate = get_money_class(monnaie).from_human_readable(montant)

        block = EventGiveaway(
            issuer_id=interaction.author.id,
            user_id=UserId(destinataire.id),
            amount=amount_to_generate,
        )
        await self.swag_client.swagchain.append(block)

        await interaction.response.send_message(
            f"**{block.amount}** a été généré pour {block.user_id}  à des fins de tests !"
        )
        await update_forbes_classement(
            interaction.guild, self.swag_client, self.swag_client.discord_client
        )

    @admin.sub_command(name="créer_yfu", guild_ids=[ADMIN_GUILD_ID])
    async def create_yfu(
        self, interaction: disnake.ApplicationCommandInteraction, exemplaire: int = 1
    ):
        """Génère une ¥fu

        Parameters
        ----------
        exemplaire : Par défaut 1. Peut être utilisé pour généré plusieurs Yfu en même temps !
        """

        for i in range(exemplaire):
            new_yfu_id = await self.swag_client.swagchain.generate_yfu(
                UserId(interaction.author.id)
            )
            new_yfu = self.swag_client.swagchain.yfu(new_yfu_id)

            await interaction.send(
                f"{interaction.author.mention}, **{new_yfu.first_name} {new_yfu.last_name}** a rejoint vos rangs à des fins de test !",
                embed=YfuEmbed.from_yfu(new_yfu),
            )
