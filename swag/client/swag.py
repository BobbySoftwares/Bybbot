from disnake.ext import commands
import disnake
from arrow.arrow import Arrow
from swag.blocks import AccountCreation, Mining, SwagBlocking, Transaction
from swag.blocks import UserTimezoneUpdate
from swag.currencies import Currency, Style, Swag
from swag.id import UserId

from ..errors import InvalidSwagValue
from ..stylog import BLOCKING_TIME
from ..utils import update_forbes_classement

from utils import GUILD_ID, format_number



YFU_GENERATION_MINING_THRESHOLD = Swag(1000000)


class SwagCommand(commands.Cog):
    def __init__(self, swag_client):
        self.swag_client = swag_client

    @commands.slash_command(name="swag", guild_ids=[GUILD_ID])
    async def swag(self, interaction: disnake.ApplicationCommandInteraction):
        pass

    @swag.sub_command(name="créer")
    async def create(self, interaction: disnake.ApplicationCommandInteraction):
        """Ouvre un porte-monnaie sur la $wagChain™."""

        await self.swag_client.swagchain.append(
            AccountCreation(
                issuer_id=interaction.author.id,
                user_id=interaction.author.id,
                timezone=self.swag_client.swagchain._guild(interaction.guild.id).timezone,
            )
        )

        await interaction.response.send_message(
            f"Bienvenue sur la $wagChain™ {interaction.author.mention} !\n\n"
            "Tu peux maintenant miner du $wag avec la commande `!$wag miner` 💰"
        )

    @swag.sub_command(name="miner")
    async def mine(self, interaction: disnake.ApplicationCommandInteraction):
        """Mine du $wag et deviens riche!"""

        # Mining Swag
        block = Mining(issuer_id=interaction.author.id, user_id=interaction.author.id)
        await self.swag_client.swagchain.append(block)

        await interaction.response.send_message(
            f"⛏ {interaction.author.mention} a miné `{block.amount}` !"
        )
        await update_forbes_classement(
            interaction.guild, self.swag_client, self.swag_client.discord_client
        )

    @swag.sub_command(name="info")
    async def info(self, interaction: disnake.ApplicationCommandInteraction, utilisateur : disnake.Member = None):
        """
        Affiche les informations du porte-monnaie d'un utilisateur.
        
        Parameters
        ----------
        utilisateur : Par défaut, l'utilisateur ayant fait la commande.
        """

        if utilisateur == None:
            utilisateur = interaction.author

        user_infos = self.swag_client.swagchain.account(utilisateur.id)

        # TODO : Changer l'affichage pour avoir une affichage en français
        release_info = (
            f"-Date du déblocage sur $wag : {Arrow.fromdatetime(user_infos.unblocking_date).to(user_infos.timezone)}\n"
            if user_infos.blocked_swag != Swag(0)
            else ""
        )
        await interaction.response.send_message(
            "```diff\n"
            f"Relevé de compte de {utilisateur.display_name}\n"
            f"-Balance : {user_infos.swag_balance}\n"
            f"           {user_infos.style_balance}\n"
            f"-Taux de bloquage : {format_number(user_infos.style_rate)} %\n"
            "-$wag actuellement bloqué : "
            f"{user_infos.blocked_swag}\n"
            f"-$tyle généré : {user_infos.pending_style}\n"
            f"{release_info}"
            f"-Timezone du compte : {user_infos.timezone}"
            "```",
            ephemeral=True
            )

    @swag.sub_command(name="bloquer")
    async def block(self, interaction: disnake.ApplicationCommandInteraction, montant : str):
        """
        Bloque un montant de $wag pour générer du $tyle.
        
        Parameters
        ----------
        montant : nombre de $wag à bloquer.
        """

        block = SwagBlocking(
            issuer_id=interaction.author.id,
            user_id=interaction.author.id,
            amount=Swag.from_command(montant),
        )
        await self.swag_client.swagchain.append(block)

        await interaction.response.send_message(
            f"{interaction.author.mention}, vous venez de bloquer `{block.amount}`, "
            f"vous les récupérerez dans **{BLOCKING_TIME} jours** à la même heure\n"
        )
        await update_forbes_classement(
            interaction.guild, self.swag_client, self.swag_client.discord_client
        )

    @swag.sub_command(name="garder")
    async def keep(self, interaction: disnake.ApplicationCommandInteraction, montant : str):
        """
        Garde un montant de $wag et utilise le reste pour générer du $tyle.
        
        Parameters
        ----------
        montant : nombre de $wag à garder avant blocage.
        """
        account_info = self.swag_client.swagchain.account(interaction.author.id)
        block = SwagBlocking(
            issuer_id=interaction.author.id,
            user_id=interaction.author.id,
            amount=(account_info.swag_balance + account_info.blocked_swag)
            - Swag.from_command(montant),
        )
        await self.swag_client.swagchain.append(block)

        await interaction.response.send_message(
            f"{interaction.author.mention}, vous venez de bloquer `{block.amount}`, "
            f"vous les récupérerez dans **{BLOCKING_TIME} jours** à la même heure\n"
        )
        await update_forbes_classement(
            interaction.guild, self.swag_client, self.swag_client.discord_client
        )

    @swag.sub_command(name="payer")
    async def pay(self, interaction: disnake.ApplicationCommandInteraction, montant : str, monnaie : Currency ,destinataire : disnake.Member):
        """
        Envoie un montant de $wag au destinataire spécifié

        Parameters
        ----------
        montant : montant à envoyer.
        monnaie : monnaie à envoyer.
        destinataire : utilisateur à qui donner la monnaie.
        """

        # Il y a sans doute un moyen plus habile de le faire
        # En passant par une méthode de l'énum, pour eviter de faire ca dans chaque cas
        if monnaie == Currency.Swag:
            amount_to_send = Swag.from_command(montant)
        elif monnaie == Currency.Style:
            amount_to_send = Style.from_command(montant)
        else:
            return

        block = Transaction(
            issuer_id=interaction.author.id,
            giver_id=UserId(interaction.author.id),
            recipient_id=UserId(destinataire.id),
            amount=amount_to_send
        )
        await self.swag_client.swagchain.append(block)

        await interaction.response.send_message(
            "Transaction effectué avec succès ! \n"
            "```ini\n"
            f"[{interaction.author.display_name}\t{block.amount}\t"
            f"-->\t{destinataire.display_name}]\n"
            "```"
        )
        await update_forbes_classement(
            interaction.guild, self.swag_client, self.swag_client.discord_client
        )

    @swag.sub_command(name="timezone")
    async def change_timezone(self, interaction: disnake.ApplicationCommandInteraction, timezone : str):
        """
        Change la timezone du porte-monnaie.

        Parameters
        ----------
        timezone : nouvelle timezone du porte-monnaie.
        """

        user = interaction.author

        block = UserTimezoneUpdate(
            issuer_id=interaction.author.id, user_id=user.id, timezone=timezone
        )
        await self.swag_client.swagchain.append(block)

        await interaction.response.send_message(
            f"Ta timezone est désormais {timezone} !\n"
            "Pour des raisons de sécurité, tu ne pourras plus changer celle-ci "
            f"avant {block.lock_date}. Merci de ta compréhension.",
            ephemeral=True
        )

# elif "historique" in command_swag:
#     user = message.author
#     user_account = self.swag_bank.get_account_info(user.id)
#     history = list(reversed(self.swag_bank.get_history(user.id)))
#     await message.channel.send(
#         f"{user.mention}, voici l'historique de tes transactions de $wag :\n"
#     )
#     await reaction_message_building(
#         self.client,
#         history,
#         message,
#         mini_history_swag_message,
#         self.swag_bank,
#         user_account.timezone,
#     )