from swag.blocks import GuildTimezoneUpdate
from ..utils import (
    update_the_style,
)


async def execute_swagdmin_command(self, message):
    user = message.author
    guild = message.guild

    if not user.guild_permissions.administrator:
        return

    command = message.content.split()
    if "timezone" in command:
        timezone = command[2]

        await self.swagchain.append(
            GuildTimezoneUpdate(
                issuer_id=message.author.id, guild_id=guild.id, timezone=timezone
            )
        )

        await message.channel.send(
            f"La timezone par défaut du serveur est désormais {timezone}.\n"
            "Les futurs comptes de la $wagChain™ créés sur ce serveur seront "
            "configurés pour utiliser cette timezone par défaut."
        )

    elif "jobs" in command:
        await update_the_style(self.client, self)

    else:
        await message.channel.send(
            f"{message.author.mention}, tu sembles perdu, voici les "
            "commandes administrateur que tu peux utiliser avec en relation "
            "avec le $wag\n"
            "```HTTP\n"
            "!$wagdmin timezone [timezone] ~~ Configure la timezone par défaut "
            "du serveur\n"
            "```"
        )
