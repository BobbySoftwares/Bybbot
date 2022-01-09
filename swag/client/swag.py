from arrow.arrow import Arrow
from swag.blocks import AccountCreation, Mining, SwagBlocking, Transaction
from swag.blocks import UserTimezoneUpdate
from swag.currencies import Swag
from swag.id import UserId

from ..errors import InvalidSwagValue, NoReceiver
from ..stylog import BLOCKING_TIME
from ..utils import update_forbes_classement

from utils import format_number


def swag_from_command(command):
    try:
        return Swag("".join(argent for argent in command if argent.isnumeric()))
    except ValueError:
        raise InvalidSwagValue


async def execute_swag_command(swag_client, message):
    command_swag = message.content.split()

    if "créer" in command_swag:
        await swag_client.swagchain.append(
            AccountCreation(
                issuer_id=message.author.id,
                user_id=message.author.id,
                # timezone=self.guilds.get(message.guild, "UTC").timezone,
                timezone="UTC",
            )
        )

        await message.channel.send(
            f"Bienvenue sur la $wagChain™ {message.author.mention} !\n\n"
            "Tu peux maintenant miner du $wag avec la commande `!$wag miner` 💰"
        )

    elif "miner" in command_swag:
        block = Mining(issuer_id=message.author.id, user_id=message.author.id)
        await swag_client.swagchain.append(block)

        await message.channel.send(
            f"⛏ {message.author.mention} a miné `{block.amount}` !"
        )
        await update_forbes_classement(
            message.guild, swag_client, swag_client.discord_client
        )

    elif "info" in command_swag:
        user = message.author
        user_infos = swag_client.swagchain.account(user.id)

        # TODO : Changer l'affichage pour avoir une affichage en français
        release_info = (
            f"-Date du déblocage sur $wag : {Arrow.fromdatetime(user_infos.unblocking_date).to(user_infos.timezone)}\n"
            if user_infos.blocked_swag != 0
            else ""
        )
        await message.channel.send(
            "```diff\n"
            f"Relevé de compte de {message.author.display_name}\n"
            f"-Balance : {user_infos.swag_balance}\n"
            f"           {user_infos.style_balance}\n"
            f"-Taux de bloquage : {format_number(user_infos.style_rate)} %\n"
            "-$wag actuellement bloqué : "
            f"{user_infos.blocked_swag}\n"
            f"-$tyle généré : {user_infos.pending_style}\n"
            f"{release_info}"
            f"-Timezone du compte : {user_infos.timezone}"
            "```"
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

    elif "bloquer" in command_swag:
        block = SwagBlocking(
            issuer_id=message.author.id,
            user_id=message.author.id,
            amount=swag_from_command(command_swag),
        )
        await swag_client.swagchain.append(block)

        await message.channel.send(
            f"{message.author.mention}, vous venez de bloquer `{block.amount}`, "
            f"vous les récupérerez dans **{BLOCKING_TIME} jours** à la même heure\n"
        )
        await update_forbes_classement(
            message.guild, swag_client, swag_client.discord_client
        )

    elif "payer" in command_swag:
        if len(message.mentions) != 1:
            raise NoReceiver

        block = Transaction(
            issuer_id=message.author.id,
            giver_id=UserId(message.author.id),
            recipient_id=UserId(message.mentions[0].id),
            amount=swag_from_command(command_swag),
        )
        await swag_client.swagchain.append(block)

        await message.channel.send(
            "Transaction effectué avec succès ! \n"
            "```ini\n"
            f"[{message.author.display_name}\t{block.amount}\t"
            f"-->\t{message.mentions[0].display_name}]\n"
            "```"
        )
        await update_forbes_classement(
            message.guild, swag_client, swag_client.discord_client
        )

    elif "timezone" in command_swag:
        timezone = command_swag[2]
        user = message.author

        block = UserTimezoneUpdate(
            issuer_id=message.author.id, user_id=user.id, timezone=timezone
        )
        await swag_client.swagchain.append(block)

        await message.channel.send(
            f"Ta timezone est désormais {timezone} !\n"
            "Pour des raisons de sécurité, tu ne pourras plus changer celle-ci "
            f"avant {block.lock_date}. Merci de ta compréhension."
        )

    else:
        # Si l'utilisateur se trompe de commande, ce message s'envoie par défaut
        await message.channel.send(
            f"{message.author.mention}, tu sembles perdu, "
            "voici les commandes que tu peux utiliser avec ton $wag :\n"
            "```HTTP\n"
            "!$wag créer ~~ Crée un compte sur la $wagChain™\n"
            "!$wag info ~~ Voir ton solde et toutes les infos de ton compte \n"
            "!$wag miner ~~ Gagner du $wag gratuitement tout les jours\n"
            "!$wag payer [montant] [@destinataire] ~~ Envoie un *montant* "
            "de $wag au *destinataire* spécifié\n"
            "!$wag bloquer [montant] ~~ Bloque un *montant* de $wag pour "
            "générer du $tyle pendant quelques jours\n"
            "!$wag historique ~~ Visualiser l'ensemble des transactions "
            "effectuées sur ton compte\n"
            "```"
        )
    await update_forbes_classement(
        message.guild, swag_client, swag_client.discord_client
    )
