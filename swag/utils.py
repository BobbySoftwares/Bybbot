import discord

import math
import random

from utils import (
    COMMAND_CHANNEL_ID_BOBBYCRATIE,
    FORBES_CHANNEL_ID_BOBBYCRATIE,
    GUILD_ID_BOBBYCRATIE,
    ROLE_ID_BOBBY_SWAG,
    chunks,
    format_number,
    get_guild_member_name,
)

from .errors import StyleStillBlocked


def mini_history_swag_message(chunk_transaction, current_page, nbr_pages, message_user):
    """Fonction utilisé pour la fonctionnalité du $wag
        Appelée lorsqu'on veut afficher une partie de l'historique des
        transactions du $wag ou de $tyle

    Args:
        chunk_transaction (lst): sous-liste de transaction
        current_page (int): La page courante, utilisé pour l'afficher
            en bas du message
        nbr_pages (int): Le nombre de page total, utilisé pour
            l'afficher en bas du message
        message_user (Message): Message de l'utilisateur qui a demandé
            l'affichage de l'historique

    Returns:
        String : message à envoyer pour visualiser une sous-partie de l'historique
    """
    transactions = [
        (
            way,
            format_number(amount),
            get_guild_member_name(second_party, message_user.guild),
            currency[0] if currency else "$wag",
        )
        for (way, second_party, amount, *currency) in chunk_transaction
    ]

    # Besoin de connaître la valeur de swag la plus grande et le nom
    # d'utilisateur le plus grand parmis l'ensemble de la sous liste
    # pour un affichage au top
    col1 = max(len(amount) for _, amount, _, _ in transactions)
    col2 = max(len(second_party) for _, second_party, _, _ in transactions)

    # Écriture du message
    content = "\n".join(
        f"[ {way}\t{amount : <{col1}} {currency}\t{second_party : <{col2}}]"
        for way, amount, second_party, currency in transactions
    )
    return (
        f"```ini\n"  # on met ini pour la couleur
        f"{content}\n"
        f"[Page {current_page}/{nbr_pages}]\n```"
    )


def mini_forbes_swag(forbes_chunk, nbr_pages, guild):
    """Fonction utilisé pour la fonctionnalité du $wag
        Appelé pour construire des parties du classement forbes sous forme de String

    Args:
        chunk_classement (lst): sous-liste d'une partie du classement
        nbr_pages (int): Nombre de page totale du classement
        guild (Guild): Guilde où est affiché le classement

    Returns:
        String: message à envoyer pour visualiser une partie du classement
    """
    forbes = [
        (
            get_guild_member_name(account.discord_id, guild),
            format_number(account.swag_balance),
            format_number(round(account.style_balance, 3)),
            account.blocked_swag != 0,
        )
        for account in forbes_chunk
    ]
    # Besoin de connaître le nom, la valeur de $wag, et la valeur de $tyle
    # le plus long pour l'aligement de chaque colonne
    col1 = max(len(user) for user, _, _, _ in forbes)
    col2 = max(len(swag_amount) for _, swag_amount, _, _ in forbes)
    col3 = max(len(style_amount) for _, _, style_amount, _ in forbes)

    offset = 1 + ((nbr_pages - 1) * 15)
    content = "\n".join(
        f"[#{rank + offset:02} {forbes_medal(rank + offset)}]\t"
        f"{user : <{col1}}\t"
        f"{swag_amount : >{col2}} $wag\t"
        f"#{style_amount : >{col3}} $tyle"
        f"{' 🔒' if is_blocking_swag else ''}"
        for rank, (user, swag_amount, style_amount, is_blocking_swag) in enumerate(
            forbes
        )
    )
    return f"```ini\n{content}\n```"


async def update_the_style(client, swag_client):  # appelé toute les heures
    """Appelée de manière périodique en fonction des paramètres choisi
    dans la fonction "on_ready"

    Permet de faire gagner du $tyle à tout les utilisateurs qui ont
    bloqué leurs $wag, et débloque les comptes déblocables
    """

    bobbycratie_guild = client.get_guild(id=GUILD_ID_BOBBYCRATIE)
    command_channel = client.get_channel(id=COMMAND_CHANNEL_ID_BOBBYCRATIE)

    # Faire gagner du style à ceux qui ont du swag bloqué :
    swag_client.swag_bank.earn_style()

    for account_name in swag_client.swag_bank.get_list_of_account():
        if swag_client.swag_bank.is_blocking_swag(account_name):
            # On essaye de débloquer le comptes. Cela sera refusé systématiquement
            # si le blocage n'est pas terminé
            try:
                blocked_swag = swag_client.swag_bank.get_bloked_swag(account_name)
                swag_client.swag_bank.deblock_swag(account_name)
                member = get_guild_member_name(account_name, bobbycratie_guild, False)
                await command_channel.send(
                    f"{member.mention}, les `{blocked_swag} $wag` que vous aviez"
                    f"bloqué sont à nouveau disponible. Continuez d'en bloquer"
                    f"pour gagner plus de $tyle !"
                )
            except (StyleStillBlocked):
                # Si le blocage n'est pas terminé, on fait R frèr
                pass

    await update_forbes_classement(
        bobbycratie_guild, swag_client
    )  # Mise à jour du classement après les gains de $tyle


async def update_the_swaggest(guild, swag_client):
    """Met à jour l'attribution du rôle "Le Bobby $wag"

    Args:
        guild (Guild): Serveur discord (inutile car c'est uniquement
            pour la Bobbycratie pour le moment)
    """

    # Récupération du nouveau premier au classement
    username_swaggest = swag_client.swag_bank.get_the_new_swaggest()
    if (
        username_swaggest is None
        or username_swaggest == swag_client.the_swaggest
        or guild.id != GUILD_ID_BOBBYCRATIE
    ):  # La gestion de rôle n'est qu'en bobbycratie
        return  # rien ne se passe si le plus riche est toujours le même

    # Mise à jour du plus riche dans $wagBank
    swag_client.the_swaggest = username_swaggest

    # Récupération de l'objet User du plus $wag
    member = guild.get_member(swag_client.the_swaggest)

    if member is None:  # Si l'utilisateur n'existe pas, alors ne rien faire
        return
    # get the role
    role_swag = guild.get_role(ROLE_ID_BOBBY_SWAG)
    # get the older swaggest
    older_swaggers = role_swag.members

    # Retirez le rôle aux anciens "Bobby $wag"
    for old_swagger in older_swaggers:
        await old_swagger.remove_roles(role_swag, reason="N'est plus le plus $wag")

    # Give the role to the new swagger
    await member.add_roles(role_swag, reason="Est maintenant devenu le plus $wag !")


async def update_forbes_classement(guild, swag_client):
    """Met à jour le classement Forbes dans le #swag-forbes

    Args:
        guild (Guild): Guilde où écrire le classement (Ne sert à rien
            en soit, car on le fait toujours que en bobbycratie pour
            le moment)
    """

    personne_par_message = 15  # Chaque message du $wag forbes ne contient que 15 places

    # Récupération du canal #$wag-forbes
    channel_forbes = guild.get_channel(FORBES_CHANNEL_ID_BOBBYCRATIE)

    # Récupération du classement complet
    forbes = swag_client.swag_bank.get_forbes()

    # Subdivision du dictionnaire en sous-liste de taille équitable
    forbes_chunks = list(chunks(forbes, personne_par_message))

    # Récupération du nombre de message nécessaire pour écrire tout le
    # classement (c'est le nombre de sous-listes)
    nbr_pages = math.ceil(len(forbes) / personne_par_message)

    # On compte le nombre de message posté dans le $wag forbes
    nbr_message_in_channel = 0
    async for message in channel_forbes.history(oldest_first=True):
        nbr_message_in_channel += 1

    # Si le nombre de message du canal est plus petit que le nombre
    # de messages nécessaire pour écrire le classement on en créé
    for _ in range(nbr_pages - nbr_message_in_channel):
        await channel_forbes.send("Nouvelle page de classement en cours d'écriture")

    # édition des messages pour mettre à jour le classement
    cpt_message = 0
    async for message in channel_forbes.history(oldest_first=True):
        await message.edit(
            content=mini_forbes_swag(forbes_chunks[cpt_message], cpt_message + 1, guild)
        )
        cpt_message += 1

    # update des bonus de st$le
    swag_client.swag_bank.update_bonus_growth_rate()
    # update du rôle du "Bobby $wag"
    await update_the_swaggest(guild, swag_client)


def forbes_medal(rank):
    if rank == 1:
        return "🥇"
    if rank == 2:
        return "🥈"
    if rank == 3:
        return "🥉"
    return random.choice(EMOJI_NUL)


# Liste des émoji utilisé pour le swag-forbes
EMOJI_NUL = [
    "🤨",
    "😐",
    "😑",
    "🙄",
    "😣",
    "😥",
    "😫",
    "😒",
    "🙃",
    "😲",
    "🙁",
    "😖",
    "😞",
    "😟",
    "😤",
    "😩",
    "😭",
    "😢",
    "😰",
    "😱",
    "🤪",
    "😵",
    "🥴",
    "😠",
    "🤮",
    "🤧",
    "🥺",
    "🙈",
    "🙊",
    "🍞",
    "🤏",
]
