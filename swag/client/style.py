from ..blocks import SwagBlocking, Transaction
from .swag import swag_from_command
from ..currencies import Style

from ..errors import InvalidStyleValue, NoReceiver
from ..stylog import BLOCKING_TIME
from ..utils import (
    update_forbes_classement,
)


def style_from_command(command):
    try:
        return Style(
            "".join(
                argent
                for argent in command
                if argent.replace(".", "").replace(",", "").isnumeric()
            )
        )
    except ValueError:
        raise InvalidStyleValue


async def execute_style_command(self, message):
    command_style = message.content.split()
    if "bloquer" in command_style:
        block = SwagBlocking(
            issuer_id=message.author.id,
            user_id=message.author.id,
            amount=swag_from_command(command_style),
        )
        await self.swagchain.append(block)

        await message.channel.send(
            f"{message.author.mention}, vous venez de bloquer `{block.amount}`, "
            f"vous les récupérerez dans **{BLOCKING_TIME} jours** à la même heure\n"
        )
        await update_forbes_classement(message.guild, self, self.client)

    elif "payer" in command_style:
        if len(message.mentions) != 1:
            raise NoReceiver

        block = Transaction(
            issuer_id=message.author.id,
            giver_id=message.author.id,
            recipient_id=message.mentions[0].id,
            amount=style_from_command(command_style),
        )
        await self.swagchain.append(block)

        await message.channel.send(
            "Transaction effectué avec succès ! \n"
            "```ini\n"
            f"[{message.author.display_name}\t{block.amount}\t"
            f"-->\t{message.mentions[0].display_name}]\n"
            "```"
        )
        await update_forbes_classement(message.guild, self, self.client)

    else:
        await message.channel.send(
            f"{message.author.mention}, tu sembles perdu, voici les "
            "commandes que tu peux utiliser avec en relation avec ton "
            "$tyle :\n"
            "```HTTP\n"
            "!$tyle payer [montant] [@destinataire] ~~ Envoie un *montant* "
            "de $tyle au *destinataire* spécifié\n"
            "!$tyle bloquer [montant] ~~ Bloque un *montant* de $wag pour "
            "générer du $tyle pendant quelques jours\n"
            "```"
        )
