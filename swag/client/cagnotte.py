from swag.blocks.cagnotte_blocks import (
    CagnotteCreation,
    CagnotteDeletion,
    CagnotteParticipantsReset,
    CagnotteRenaming,
)
from swag.blocks.swag_blocks import Transaction
from swag.currencies import Style, Swag
from swag.errors import CagnotteUnspecifiedException, NoReceiver
from swag.id import CagnotteId, UserId

from ..utils import (
    # currency_to_str,
    # mini_history_swag_message,
    update_forbes_classement,
)

from utils import (
    format_number,
    get_guild_member_name,
    reaction_message_building,
)


async def execute_cagnotte_command(swag_client, message):
    def get_cagnotte_id_from_command(splited_command):
        try:
            cagnotte_idx = [
                identifiant
                for identifiant in splited_command
                if identifiant.startswith("€")
            ][0]
            return CagnotteId(cagnotte_idx)
        except (IndexError):
            raise CagnotteUnspecifiedException

    splited_command = message.content.split()

    if "créer" in splited_command:
        try:
            cagnotte_id = splited_command[2]
            cagnotte_name = " ".join(splited_command[3:])
        except ValueError:
            await message.channel.send(
                f"{message.author.mention}, merci de spécifier un index "
                "pour ta €agnotte."
            )
            return
            cagnotte_id = self.swagchain.next_cagnotte_id
            cagnotte_name = " ".join(splited_command[2:])

        if len(cagnotte_name) == 0:
            await message.channel.send(
                f"{message.author.mention}, merci de mentionner un nom "
                "pour ta €agnotte."
            )
            return

        await swag_client.swagchain.append(
            CagnotteCreation(
                issuer_id=UserId(message.author.id),
                cagnotte_id=cagnotte_id,
                name=cagnotte_name,
                creator=UserId(message.author.id),
            )
        )

        await message.channel.send(
            f"{message.author.mention} vient de créer une €agnotte nommée **« "
            f"{cagnotte_name} »**. "
            f"Son identifiant est le {cagnotte_id}"
        )

        await update_forbes_classement(
            message.guild, swag_client, swag_client.discord_client
        )

    # À partir d'ici, toutes les commandes doivent impérativement passer l'identifiant
    # de €agnotte (sous forme de €n)

    elif "info" in splited_command:
        cagnotte_id = get_cagnotte_id_from_command(splited_command)
        cagnotte_info = swag_client.swagchain.cagnotte(cagnotte_id)

        managers = [
            await get_guild_member_name(
                manager, message.guild, swag_client.discord_client
            )
            for manager in cagnotte_info.managers
        ]
        participants = [
            await get_guild_member_name(
                participant, message.guild, swag_client.discord_client
            )
            for participant in cagnotte_info.participants
        ]
        await message.channel.send(
            f"Voici les informations de la €agnotte {cagnotte_id}\n"
            "```\n"
            f"Nom de €agnotte : {cagnotte_info.name}\n"
            f"Montant de la €agnotte : {cagnotte_info.swag_balance} "
            f"{cagnotte_info.style_balance}\n"
            f"Gestionnaire de la €agnotte : {managers}\n"
            f"Participants : {participants}\n"
            "```"
        )

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

    elif "payer" in splited_command:
        cagnotte_id = get_cagnotte_id_from_command(splited_command)
        cagnotte_info = swag_client.swagchain.cagnotte(cagnotte_id)

        if "$wag" in splited_command:
            amount = Swag.from_command(splited_command)
        elif "$tyle" in splited_command:
            amount = Style.from_command(splited_command)
        else:
            await message.channel.send(
                f"{message.author.mention}, avec le nom de la monnaie c'est mieux !"
            )
            return

        await swag_client.swagchain.append(
            Transaction(
                issuer_id=UserId(message.author.id),
                giver_id=UserId(message.author.id),
                recipient_id=cagnotte_id,
                amount=amount,
            )
        )

        await message.channel.send(
            "Transaction effectuée avec succès ! \n"
            "```ini\n"
            f"[{message.author.display_name}\t{amount}\t"
            f"-->\t€{cagnotte_id} {cagnotte_info.name}]\n"
            "```"
        )
        await update_forbes_classement(
            message.guild, swag_client, swag_client.discord_client
        )

    elif "donner" in splited_command:
        cagnotte_id = get_cagnotte_id_from_command(splited_command)
        cagnotte_info = swag_client.swagchain.cagnotte(cagnotte_id)
        receiver = message.mentions
        if len(receiver) != 1:
            raise NoReceiver
        receiver = receiver[0]

        if "$wag" in splited_command:
            amount = Swag.from_command(splited_command)
        elif "$tyle" in splited_command:
            amount = Style.from_command(splited_command)
        else:
            await message.channel.send(
                f"{message.author.mention}, avec le nom de la monnaie c'est mieux !"
            )
            return

        await swag_client.swagchain.append(
            Transaction(
                issuer_id=UserId(message.author.id),
                giver_id=cagnotte_id,
                recipient_id=UserId(message.author.id),
                amount=amount,
            )
        )

        await message.channel.send(
            "Transaction effectuée avec succès ! \n"
            "```ini\n"
            f"[{cagnotte_id} {cagnotte_info.name}\t{amount}\t"
            f"-->\t{receiver.display_name}]\n"
            "```"
        )

        await update_forbes_classement(
            message.guild, swag_client, swag_client.discord_client
        )

    elif "partager" in splited_command:
        cagnotte_id = get_cagnotte_id_from_command(splited_command)
        cagnotte_info = swag_client.swagchain.cagnotte(cagnotte_id)

        participant_ids = [UserId(participant.id) for participant in message.mentions]

        (
            participant_ids,
            swag_gain,
            style_gain,
            winner_rest,
            swag_rest,
            style_rest,
        ) = await swag_client.swagchain.share_cagnotte(
            cagnotte_id, UserId(message.author.id), participant_ids
        )

        participants_mentions = ", ".join(
            f"{participant_id}" for participant_id in participant_ids
        )

        await message.channel.send(
            f"{participants_mentions} vous avez chacun récupéré `{swag_gain}` "
            f"et `{style_gain}` de la cagnotte **{cagnotte_info.name}** 💸"
        )

        if winner_rest is not None:
            await message.channel.send(
                f"{winner_rest} récupère les `{swag_rest}` et `{style_rest}` "
                "restants ! 🤑"
            )

        await update_forbes_classement(
            message.guild, swag_client, swag_client.discord_client
        )

    elif "loto" in splited_command:
        cagnotte_id = get_cagnotte_id_from_command(splited_command)
        cagnotte_info = swag_client.swagchain.cagnotte(cagnotte_id)

        participant_ids = [UserId(participant.id) for participant in message.mentions]

        gagnant, swag_gain, style_gain = await swag_client.swagchain.cagnotte_lottery(
            cagnotte_id, UserId(message.author.id), participant_ids
        )

        await message.channel.send(
            f"{gagnant} vient de gagner l'intégralité de la €agnotte "
            f"{cagnotte_id} *{cagnotte_info.name}*, à savoir "
            f"`{swag_gain}` et `{style_gain}` ! 🎰"
        )

        await update_forbes_classement(
            message.guild, swag_client, swag_client.discord_client
        )

    elif "renommer" in splited_command:
        cagnotte_id = get_cagnotte_id_from_command(splited_command)
        cagnotte_info = swag_client.swagchain.cagnotte(cagnotte_id)

        new_name = [
            word
            for word in splited_command[1:]
            if word not in {f"{cagnotte_id}", "renommer"}
        ]

        new_name = " ".join(new_name)

        await swag_client.swagchain.append(
            CagnotteRenaming(
                issuer_id=UserId(message.author.id),
                cagnotte_id=cagnotte_id,
                new_name=new_name,
            )
        )

        await message.channel.send(
            f'La €agnotte {cagnotte_id} anciennement nommé **"{cagnotte_info.name}"'
            f'** s\'appelle maintenant **"{new_name}"**'
        )

        await update_forbes_classement(
            message.guild, swag_client, swag_client.discord_client
        )

    elif "reset" in splited_command:
        cagnotte_id = get_cagnotte_id_from_command(splited_command)
        cagnotte_info = swag_client.swagchain.cagnotte(cagnotte_id)

        await swag_client.swagchain.append(
            CagnotteParticipantsReset(
                issuer_id=UserId(message.author.id),
                cagnotte_id=cagnotte_id,
            )
        )

        await message.channel.send(
            f"La liste des participants de la €agnotte {cagnotte_id} **"
            f'"{cagnotte_info.name}"** a été remis à zéro 🔄'
        )

        await update_forbes_classement(
            message.guild, swag_client, swag_client.discord_client
        )

    elif "détruire" in splited_command:
        cagnotte_id = get_cagnotte_id_from_command(splited_command)
        cagnotte_info = swag_client.swagchain.cagnotte(cagnotte_id)

        await swag_client.swagchain.append(
            CagnotteDeletion(
                issuer_id=UserId(message.author.id),
                cagnotte_id=cagnotte_id,
            )
        )

        await message.channel.send(
            f"La €agnotte {cagnotte_id} *{cagnotte_info.name}* est maintenant "
            "détruite de ce plan de l'existence ❌"
        )
        await update_forbes_classement(
            message.guild, swag_client, swag_client.discord_client
        )

    else:
        await message.channel.send(
            f"{message.author.mention}, tu as l'air perdu "
            "(c'est un peu normal, avec ces commandes pétées du cul...) 🙄\nVoici "
            "les commandes "
            "que tu peux utiliser avec les €agnottes :\n"
            "```HTTP\n"
            "!€agnotte créer [$wag/$tyle] [Nom_de_la_€agnotte] ~~ "
            "Permet de créer une nouvelle €agnotte, de $wag ou de $tyle "
            "avec le nom de son choix\n"
            "!€agnotte info €[n] ~~ Affiche des informations détaillés sur la "
            "€agnotte n\n"
            "!€agnotte historique €[n] ~~ Affiche les transactions en lien avec la "
            "€agnotte n\n"
            "!€agnotte payer €[n] [montant] ~~ fait don "
            "de la somme choisi à la €agnotte numéro €n\n"
            "⭐!€agnotte donner €[n] [montant] [@mention] ~~ donne à l'utilisateur "
            "mentionné "
            "un montant venant de la cagnotte\n"
            "⭐!€agnotte partager €[n] [@mention1 @mention2 ...] ~~ "
            "Partage l'intégralité de la €agnotte entre les utilisateurs mentionné. "
            "Si personne n'est mentionné, la €agnotte sera redistribué parmis les "
            "personnes ayant un compte à la $wagBank\n"
            "⭐!€agnotte loto €[n] [@mention1 @mention2 ...] ~~ "
            "Tire au sort parmis les utilisateurs mentionnés celui qui remportera "
            "l'intégralité "
            "de la €agnotte. Si personne n'est mentionné, le tirage au sort parmis "
            "les participants à la €agnotte\n"
            "⭐!€agnotte renommer €[n] [Nouveau nom] ~~ Change le nom de la €agnotte\n"
            "⭐!€agnotte reset €[n] ~~ Enlève tout les participants de la €agnotte de "
            "la liste des participants\n"
            "⭐!€agnotte détruire €[n] ~~ Détruit la €agnotte si elle est vide\n"
            "```\n"
            "*Seul le gestionnaire de la €agnotte peut faire les commandes précédées "
            "d'une  ⭐*"
        )
