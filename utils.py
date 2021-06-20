import discord

import math
import asyncio

ROLE_ID_BOBBY_SWAG = 856280663392649257
GUILD_ID_BOBBYCRATIE = 856278929296195602
# ROLE_ID_BOBBY_SWAG = 846736189310238751  # Identifiant unique du rôle "Le bobby swag"
# GUILD_ID_BOBBYCRATIE = 487244765558210580  # ID unique du serveur Bobbycratie

FORBES_CHANNEL_ID_BOBBYCRATIE = 856279732009304074
COMMAND_CHANNEL_ID_BOBBYCRATIE = 856278929869242380
# FORBES_CHANNEL_ID_BOBBYCRATIE = 848313360306536448  # ID unique du canal du swag forbes
# COMMAND_CHANNEL_ID_BOBBYCRATIE = 848302082150760508  # ID unique du canal swag-command


def formatNumber(n):
    """Fonction qui permet de rajouter des espaces fin entre chaque millier d'un nombre
        100000 -> 100 000

    Args:
        n (int/float): le nombre à formater

    Returns:
        String: le nombre, formaté
    """
    return format(n, ",").replace(",", " ")


def chunks(lst, n):
    """Permet de subdiviser des listes en plusieurs sous-liste de même taille.

    Args:
        lst (liste): La liste à subdiviser
        n (int): taille de chaque sous-liste
    Yields:
        list: liste des sous-listes
    """
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def getGuildMemberName(general_username, guild, return_display_name=True):
    """Permet de récupérer l'objet User en donnant le nom d'utilisateur général discord de quelqu'un

        Le nom d'utilisateur général est le pseudo sous la forme GlitchiKun#4950 (celui qui est impossible de changer)

        Si l'option return_display_name est à True, la fonction renvoie directement le nom d'utilisateur local au serveur
        (Exemple : pour GlitchiKun#4950, son nom d'utilisateur local sur la Bobbycratie est Bobby Ingénieur)

    Args:
        general_username (String): Nom d'utilisateur général (GlitchiKun#4950)
        guild (Guild): Serveur discord
        return_display_name (bool, optional) :  True -> renvoie un string : le nom d'utilisateur local (Bobby Ingénieur).
                                                False -> renvoie l'objet User correspondant à l'utilisateur

    Returns:
        User ou String: Objet User, ou nom local de l'utilisateur (en fonction du return_display_name)
    """

    ## Cette fonction est utilisé pour l'historique, il ne faut donc pas prendre en compte $wag mine et $style generator
    if general_username == "$wag Mine ⛏" or general_username == "$tyle Generator Inc.":
        return general_username
    split_username = general_username.split("#")
    user = discord.utils.get(
        guild.members, name=split_username[0], discriminator=split_username[1]
    )
    if user == None:
        return general_username

    if return_display_name:
        return user.display_name
    else:
        return user


async def reaction_message_building(
    client, lst_to_show, message_user, fonction_message_builder
):
    """Utilisé par toutes les fonctionnalités du bot (Jukebox et $wag)
        Permet de créer un message interactif avec des réactions, pour pouvoir naviguer entre une énorme liste
        d'élément quelconque.

    Args:
        lst_to_show (lst): La grande liste de chose à afficher, qui sera subdiviser en sous-liste
        message_user (Message): Le message de l'utilisateur qui a demandé l'affichage de ce message interactif
        fonction_message_builder (Function): Fonction à appelé pour la création du message approprié pour chaque sous-liste de lst_to_shw.
        Par convention, cette fonction doit commencer par "mini_"

    Returns:
        Message: Le message interractif
    """
    sound_per_page = 15
    chunks_sounds = list(chunks(lst_to_show, sound_per_page))
    nbr_pages = math.ceil(len(lst_to_show) / sound_per_page)
    current_page = 1

    Message = fonction_message_builder(
        chunks_sounds[current_page - 1], current_page, nbr_pages, message_user
    )

    # Envoie du message crée par la fonction_message_builder, défini en entrée.
    message_bot = await message_user.channel.send(Message)

    # Ajout des réactions initiale
    await message_bot.add_reaction("◀️")
    await message_bot.add_reaction("▶️")
    active = True

    def check(reaction, user):
        return (
            user == message_user.author
            and reaction.message == message_bot
            and str(reaction.emoji) in ["◀️", "▶️"]
        )

    while active:
        try:
            reaction, user = await client.wait_for(
                "reaction_add", timeout=60, check=check
            )

            # Si l'émoji suivant est tapé, on avance d'une page
            if str(reaction.emoji) == "▶️" and current_page != nbr_pages:
                current_page += 1
                await message_bot.edit(
                    content=fonction_message_builder(
                        chunks_sounds[current_page - 1],
                        current_page,
                        nbr_pages,
                        message_user,
                    )
                )

            # Si l'émoji précédent est tapé, on recule d'une page
            elif str(reaction.emoji) == "◀️" and current_page > 1:
                current_page -= 1
                await message_bot.edit(
                    content=fonction_message_builder(
                        chunks_sounds[current_page - 1],
                        current_page,
                        nbr_pages,
                        message_user,
                    )
                )

            # On retire la réaction faites par l'utilisateur
            await message_bot.remove_reaction(reaction, user)
        # Passé le time out défini dans le client.wait_for, on empêche les gens de continuer de naviguer.
        except asyncio.TimeoutError:
            await message_bot.clear_reactions()
            active = False


async def connect_to_chan(client, chanToGo):
    """Fonction utilisé par le bot pour se connecter sur un canal vocal,
        En prenant en compte toutes les situations possibles

    Args:
        chanToGo (VoiceChannel): Le canal vocal où il faut aller

    Returns:
        VoiceClient: l'instance de connexion vocale que le bot utilise pour le canal vocal chanToGo
    """
    for actualVoiceClient in client.voice_clients:
        if actualVoiceClient.guild == chanToGo.guild:
            if actualVoiceClient.channel == chanToGo:
                return actualVoiceClient
            else:
                # close the old voiceClient in wrong channel, and move to the new channel
                await actualVoiceClient.move_to(chanToGo)
                return actualVoiceClient

    # If no VoiceClient is already set, create a new one
    return await chanToGo.connect()
