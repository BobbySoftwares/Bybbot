from disnake.ext import commands
import disnake
from swag.blocks.cagnotte_blocks import (
    CagnotteAddManagerBlock,
    CagnotteCreation,
    CagnotteDeletion,
    CagnotteParticipantsReset,
    CagnotteRenaming,
    CagnotteRevokeManagerBlock,
)
from swag.blocks.swag_blocks import Transaction
from swag.currencies import Currency
from swag.id import CagnotteId, UserId

from ..utils import (
    # currency_to_str,
    # mini_history_swag_message,
    update_forbes_classement,
)

from utils import (
    GUILD_ID,
    format_number,
    get_guild_member_name,
    reaction_message_building,
)


def cagnotte_id_converter(
    interaction: disnake.ApplicationCommandInteraction, user_input: str
):
    # €agnotte id should be one word. If there is multiple words in the input, we take the first
    if " " in user_input:
        user_input = user_input.split()[0]

    # We check if "€" is missing at the beggining. In this case, we add it.
    if not user_input.startswith("€"):
        user_input = "€" + user_input

    return user_input


class CagnotteCommand(commands.Cog):
    def __init__(self, swag_client):
        self.swag_client = swag_client

    async def cagnotte_id_autocomplete(
        self, interaction: disnake.ApplicationCommandInteraction, user_input: str
    ):
        return [
            cagnotte_id[0].id
            for cagnotte_id in self.swag_client.swagchain.cagnottes
            if user_input in cagnotte_id[0].id
        ]

    async def cagnotte_id_autocomplete_manager(
        self, interaction: disnake.ApplicationCommandInteraction, user_input: str
    ):
        return [
            cagnotte_id[0].id
            for cagnotte_id in self.swag_client.swagchain.cagnottes
            if user_input in cagnotte_id[0].id
            and UserId(interaction.author.id) in cagnotte_id[1].managers
        ]

    @commands.slash_command(name="cagnotte", guild_ids=[GUILD_ID])
    async def cagnotte(self, interaction: disnake.ApplicationCommandInteraction):
        pass

    @cagnotte.sub_command(name="créer")
    async def create(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        nom: str,
        identifiant: str = commands.Param(converter=cagnotte_id_converter),
    ):
        """
        Crée une €agnotte dans la $wagChain™.

        Parameters
        ----------
        nom : Nom de la €agnotte.
        identifiant : Identifiant de la €agnotte : le X dans €X. Ne peut être qu'un seul mot.
        """

        await self.swag_client.swagchain.append(
            CagnotteCreation(
                issuer_id=UserId(interaction.author.id),
                cagnotte_id=CagnotteId(identifiant),
                name=nom,
                creator=UserId(interaction.author.id),
            )
        )

        await interaction.response.send_message(
            f"{interaction.author.mention} vient de créer une €agnotte nommée **["
            f"{nom}]**. "
            f"Son identifiant est **{identifiant}**"
        )

        await update_forbes_classement(
            interaction.guild, self.swag_client, self.swag_client.discord_client
        )

    @cagnotte.sub_command(name="info")
    async def info(
        self, interaction: disnake.ApplicationCommandInteraction, identifiant: str
    ):
        """
        Affiche les informations d'une €agnotte.

        Parameters
        ----------
        identifiant : Identifiant de la €agnotte sous la forme €X.
        """

        cagnotte_info = self.swag_client.swagchain.cagnotte(CagnotteId(identifiant))

        managers = [
            await get_guild_member_name(
                manager, interaction.guild, self.swag_client.discord_client
            )
            for manager in cagnotte_info.managers
        ]
        participants = [
            await get_guild_member_name(
                participant, interaction.guild, self.swag_client.discord_client
            )
            for participant in cagnotte_info.participants
        ]
        await interaction.response.send_message(
            f"Voici les informations de la €agnotte {identifiant}\n"
            "```\n"
            f"Nom de €agnotte : {cagnotte_info.name}\n"
            f"Montant de la €agnotte : {cagnotte_info.swag_balance} "
            f"{cagnotte_info.style_balance}\n"
            f"Gestionnaire de la €agnotte : {managers}\n"
            f"Participants : {participants}\n"
            "```",
            ephemeral=True,
        )

    # Add autocompletion for the argument identifiant for the "info" command
    info.autocomplete("identifiant")(cagnotte_id_autocomplete)

    @cagnotte.sub_command(name="donner")
    async def give(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        identifiant: str,
        destinataire: disnake.Member,
        montant: int,
        monnaie: Currency,
    ):
        """
        👑 Donne au destinataire mentionné un montant venant de la €agnotte.

        Parameters
        ----------
        identifiant : Identifiant de la €agnotte sous la forme €X.
        destinataire : Destinataire du don.
        montant : Montant à envoyer.
        monnaie : Type de monnaie.
        """

        cagnotte_id = CagnotteId(identifiant)
        cagnotte_info = self.swag_client.swagchain.cagnotte(cagnotte_id)

        block = Transaction(
            issuer_id=UserId(interaction.author.id),
            giver_id=cagnotte_id,
            recipient_id=UserId(destinataire.id),
            amount=Currency.get_class(monnaie)(montant),
        )

        await self.swag_client.swagchain.append(block)

        await interaction.response.send_message(
            "Transaction effectuée avec succès ! \n"
            "```ini\n"
            f"[{cagnotte_id}[{cagnotte_info.name}]\t{block.amount}\t"
            f"-->\t{destinataire.display_name}]\n"
            "```"
        )

        await update_forbes_classement(
            interaction.guild, self.swag_client, self.swag_client.discord_client
        )

    # Add autocompletion for the argument identifiant for the "give" command
    give.autocomplete("identifiant")(cagnotte_id_autocomplete_manager)

    @cagnotte.sub_command(name="partager")
    async def share(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        identifiant: str,
    ):
        """
        👑 Partage l'intégralité de la €agnotte entre les utilisateurs.

        Parameters
        ----------
        identifiant : Identifiant de la €agnotte sous la forme €X
        """
        cagnotte_id = CagnotteId(identifiant)
        cagnotte_info = self.swag_client.swagchain.cagnotte(cagnotte_id)

        # TODO disnake ne gère pas encore les parametres sous forme de liste
        participant_ids = []

        (
            participant_ids,
            swag_gain,
            style_gain,
            winner_rest,
            swag_rest,
            style_rest,
        ) = await self.swag_client.swagchain.share_cagnotte(
            cagnotte_id, UserId(interaction.author.id), participant_ids
        )

        participants_mentions = ", ".join(
            f"{participant_id}" for participant_id in participant_ids
        )

        await interaction.response.send_message(
            f"{participants_mentions} vous avez chacun récupéré `{swag_gain}` "
            f"et `{style_gain}` de la cagnotte **{cagnotte_id}[{cagnotte_info.name}]** 💸"
        )

        if winner_rest is not None:
            await interaction.followup.send(
                f"{winner_rest} récupère les `{swag_rest}` et `{style_rest}` "
                "restants ! 🤑"
            )

        await update_forbes_classement(
            interaction.guild, self.swag_client, self.swag_client.discord_client
        )

    # Add autocompletion for the argument identifiant for the "share" command
    share.autocomplete("identifiant")(cagnotte_id_autocomplete_manager)

    @cagnotte.sub_command(name="loto")
    async def loto(
        self, interaction: disnake.ApplicationCommandInteraction, identifiant: str
    ):
        """
        👑 Tire au sort un participant et lui partage l'intégralité de la €agnotte.

        Parameters
        ----------
        identifiant : Identifiant de la €agnotte sous la forme €X
        """

        cagnotte_id = CagnotteId(identifiant)
        cagnotte_info = self.swag_client.swagchain.cagnotte(cagnotte_id)

        # TODO idem share
        participant_ids = []

        (
            gagnant,
            swag_gain,
            style_gain,
        ) = await self.swag_client.swagchain.cagnotte_lottery(
            cagnotte_id, UserId(interaction.author.id), participant_ids
        )

        await interaction.response.send_message(
            f"{gagnant} vient de gagner l'intégralité de la €agnotte "
            f"**{cagnotte_id}[{cagnotte_info.name}]**, à savoir "
            f"`{swag_gain}` et `{style_gain}` ! 🎰"
        )

        await update_forbes_classement(
            interaction.guild, self.swag_client, self.swag_client.discord_client
        )

    # Add autocompletion for the argument identifiant for the "loto" command
    loto.autocomplete("identifiant")(cagnotte_id_autocomplete_manager)

    @cagnotte.sub_command(name="renommer")
    async def rename(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        identifiant: str,
        nom: str,
    ):
        """
        👑 Renomme une €agnotte.

        Parameters
        ----------
        identifiant : Identifiant de la €agnotte sous la forme €X.
        nom : Nouveau nom de la €agnotte.
        """

        cagnotte_id = CagnotteId(identifiant)
        cagnotte_info = self.swag_client.swagchain.cagnotte(cagnotte_id)

        old_name = cagnotte_info.name

        await self.swag_client.swagchain.append(
            CagnotteRenaming(
                issuer_id=UserId(interaction.author.id),
                cagnotte_id=cagnotte_id,
                new_name=nom,
            )
        )

        await interaction.response.send_message(
            f"La €agnotte {cagnotte_id} anciennement nommé **[{old_name}]"
            f"** s'appelle maintenant **[{nom}]**"
        )

        await update_forbes_classement(
            interaction.guild, self.swag_client, self.swag_client.discord_client
        )

    # Add autocompletion for the argument identifiant for the "loto" command
    rename.autocomplete("identifiant")(cagnotte_id_autocomplete_manager)

    @cagnotte.sub_command(name="reset")
    async def reset(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        identifiant: str,
    ):

        """
        👑 Enlève tout les participants de la €agnotte de sa liste des participants.

        Parameters
        ----------
        identifiant : Identifiant de la €agnotte sous la forme €X.
        """

        cagnotte_id = CagnotteId(identifiant)
        cagnotte_info = self.swag_client.swagchain.cagnotte(cagnotte_id)

        await self.swag_client.swagchain.append(
            CagnotteParticipantsReset(
                issuer_id=UserId(interaction.author.id),
                cagnotte_id=cagnotte_id,
            )
        )

        await interaction.response.send_message(
            f"La liste des participants de la €agnotte **{cagnotte_id}"
            f"[{cagnotte_info.name}]** a été remis à zéro 🔄"
        )

        await update_forbes_classement(
            interaction.guild, self.swag_client, self.swag_client.discord_client
        )

    # Add autocompletion for the argument identifiant for the "loto" command
    reset.autocomplete("identifiant")(cagnotte_id_autocomplete_manager)

    @cagnotte.sub_command(name="détruire")
    async def destroy(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        identifiant: str,
    ):
        """
        👑 Détruit la €agnotte si elle est vide.

        Parameters
        ----------
        identifiant : Identifiant de la €agnotte sous la forme €X.
        """

        cagnotte_id = CagnotteId(identifiant)
        cagnotte_info = self.swag_client.swagchain.cagnotte(cagnotte_id)

        await self.swag_client.swagchain.append(
            CagnotteDeletion(
                issuer_id=UserId(interaction.author.id),
                cagnotte_id=cagnotte_id,
            )
        )

        await interaction.response.send_message(
            f"La €agnotte **{cagnotte_id}[{cagnotte_info.name}]** est maintenant "
            "détruite de ce plan de l'existence ❌"
        )
        await update_forbes_classement(
            interaction.guild, self.swag_client, self.swag_client.discord_client
        )

    # Add autocompletion for the argument identifiant for the "loto" command
    destroy.autocomplete("identifiant")(cagnotte_id_autocomplete_manager)

    @cagnotte.sub_command(name="payer")
    async def pay(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        identifiant: str,
        montant: int,
        monnaie: Currency,
    ):

        """
        Envoie un montant d'une monnaie à la €agnotte.

        Parameters
        ----------
        identifiant : Identifiant de la €agnotte sous la forme €X.
        montant : montant à envoyer à la €agnotte.
        monnaie : type de monnaie à envoyer à la €agnotte.
        """

        cagnotte_id = CagnotteId(identifiant)
        cagnotte_info = self.swag_client.swagchain.cagnotte(cagnotte_id)

        block = Transaction(
            issuer_id=UserId(interaction.author.id),
            giver_id=UserId(interaction.author.id),
            recipient_id=cagnotte_id,
            amount=Currency.get_class(monnaie)(montant),
        )

        await self.swag_client.swagchain.append(block)

        await interaction.response.send_message(
            "Transaction effectuée avec succès ! \n"
            "```ini\n"
            f"[{interaction.author.display_name}\t{block.amount}\t"
            f"-->\t{cagnotte_id}[{cagnotte_info.name}]]\n"
            "```"
        )
        await update_forbes_classement(
            interaction.guild, self.swag_client, self.swag_client.discord_client
        )

    # Add autocompletion for the argument identifiant for the "loto" command
    pay.autocomplete("identifiant")(cagnotte_id_autocomplete)

    @cagnotte.sub_command_group(name="gestionnaire")
    async def manager(self, interaction: disnake.ApplicationCommandInteraction):
        pass

    @manager.sub_command(name="ajouter")
    async def add_manager(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        identifiant: str,
        utilisateur: disnake.Member,
    ):
        """
        👑 Ajoute un gestionnaire à la €agnotte.

        Parameters
        ----------
        identifiant : Identifiant de la €agnotte sous la forme €X.
        utilisateur : Utilisateur à ajouter à la liste des gestionnaires.
        """

        cagnotte_id = CagnotteId(identifiant)
        cagnotte_info = self.swag_client.swagchain.cagnotte(cagnotte_id)

        block = CagnotteAddManagerBlock(
            issuer_id=interaction.author.id,
            cagnotte_id=cagnotte_id,
            new_manager=UserId(utilisateur.id),
        )

        await self.swag_client.swagchain.append(block)

        await interaction.response.send_message(
            f"{block.new_manager} fait maintenant partie des gestionnaires de la €agnotte "
            f"**{cagnotte_id}[{cagnotte_info.name}]**."
        )
        await update_forbes_classement(
            interaction.guild, self.swag_client, self.swag_client.discord_client
        )

    add_manager.autocomplete("identifiant")(cagnotte_id_autocomplete_manager)

    @manager.sub_command(name="révoquer")
    async def revoke_manager(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        identifiant: str,
        utilisateur: disnake.Member,
    ):
        """
        👑 Enlève à un utilisateur son titre de gestionnaire d'une €agnotte.

        Parameters
        ----------
        identifiant : Identifiant de la €agnotte sous la forme €X.
        utilisateur : Utilisateur à révoquer dela liste des gestionnaires.
        """
        cagnotte_id = CagnotteId(identifiant)
        cagnotte_info = self.swag_client.swagchain.cagnotte(cagnotte_id)

        block = CagnotteRevokeManagerBlock(
            issuer_id=interaction.author.id,
            cagnotte_id=cagnotte_id,
            manager_to_revoke=UserId(utilisateur.id),
        )

        await self.swag_client.swagchain.append(block)

        await interaction.response.send_message(
            f"{block.manager_to_revoke} **a été révoqué** des gestionnaires de la €agnotte "
            f"**{cagnotte_id}[{cagnotte_info.name}]**."
        )
        await update_forbes_classement(
            interaction.guild, self.swag_client, self.swag_client.discord_client
        )

    revoke_manager.autocomplete("identifiant")(cagnotte_id_autocomplete_manager)

    # elif "historique" in splited_command:
    #     user = message.author
    #     user_account = self.swag_bank.get_account_info(user.id)

    #     cagnotte_id = get_cagnotte_id_from_command(splited_command)
    #     history = list(reversed(self.swag_bank.get_cagnotte_history(cagnotte_id)))

    #     cagnotte_info = self.swag_bank.get_active_cagnotte_info(cagnotte_id)
    #     await message.channel.send(
    #         f"{message.author.mention}, voici l'historique de tes transactions de "
    #         f"la cagnotte **{cagnotte_info.name}** :\n"
    #     )
    #     await reaction_message_building(
    #         self.client,
    #         history,
    #         message,
    #         mini_history_swag_message,
    #         self.swag_bank,
    #         user_account.timezone,
    #     )
