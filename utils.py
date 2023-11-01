import json
import math
import asyncio
import random


with open("config.json", "r") as json_file:
    client_config = json.load(json_file)

# ID unique du serveur
GUILD_ID = client_config.get("guild_id", 487244765558210580)

# ID unique du role du plus swag
ROLE_ID_SWAGGEST = client_config.get("swaggest_role", 846736189310238751)

# ID unique du canal du swag forbes
FORBES_CHANNEL_ID = client_config.get("forbes_channel", 848313360306536448)

# ID unique du canal swag-command
COMMAND_CHANNEL_ID = client_config.get("command_channel", 848302082150760508)

# ID unique du canal de la swag-chain
SWAGCHAIN_CHANNEL_ID = client_config.get("swagchain_channel", 913946510616567848)

# ID unique du canal de log, si il n'est pas défini, sa valeur sera None
LOG_CHANNEL_ID = client_config.get("log_channel", None)

# ID des administrateurs
ADMINS_ID = client_config.get("admins")

# CLEF API DE TENOR GIF
TENOR_API_KEY = client_config.get("tenor_api_key")


def format_number(n):
    """Fonction qui permet de rajouter des espaces fin entre chaque
    millier d'un nombre 100000 -> 100 000

    Args:
        n (int/float): le nombre à formater

    Returns:
        String: le nombre, formaté
    """
    return format(n, ",").replace(",", " ")


def randomly_distribute(total, n):
    """Distribue de manière aléatoire dans n élément la quantité dans 'total'

    Returns:
        List: La liste d'éléments dont la somme fait le total
    """
    random_distributed_vector = [random.random() for i in range(n)]
    vector_sum = sum(random_distributed_vector)
    random_distributed_vector = [
        int(total * i / vector_sum) for i in random_distributed_vector
    ]
    return random_distributed_vector


def chunks(lst, n):
    """Permet de subdiviser des listes en plusieurs sous-liste de même
    taille.

    Args:
        lst (liste): La liste à subdiviser
        n (int): taille de chaque sous-liste
    Yields:
        list: liste des sous-listes
    """
    lst = list(lst)
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


async def get_guild_member_name(user_id, guild, client, return_display_name=True):
    """Permet de récupérer l'objet User en donnant le nom d'utilisateur
    général discord de quelqu'un

    Le nom d'utilisateur général est le pseudo sous la forme
    GlitchiKun#4950 (celui qui est impossible de changer)

    Si l'option return_display_name est à True, la fonction renvoie
    directement le nom d'utilisateur local au serveur (Exemple : pour
    GlitchiKun#4950, son nom d'utilisateur local sur la Bobbycratie
    est Bobby Ingénieur)

    Args:
        general_username (String): Nom d'utilisateur général (GlitchiKun#4950)
        guild (Guild): Serveur discord
        return_display_name (bool, optional) :
            True -> renvoie un string : le nom d'utilisateur local (Bobby Ingénieur).
            False -> renvoie l'objet User correspondant à l'utilisateur

    Returns:
        User ou String: Objet User, ou nom local de l'utilisateur (en
            fonction du return_display_name)
    """

    # Cette fonction est utilisé pour l'historique, il ne faut donc pas
    # prendre en compte $wag mine et $style generator
    if user_id == "$wag Mine ⛏" or user_id == "$tyle Generator Inc.":
        return user_id

    try:
        user_id = user_id.id
    except AttributeError:
        pass

    user = guild.get_member(user_id)
    if user is None:
        user = client.get_user(user_id)

    if user is None:
        return (await client.fetch_user(user_id)).name

    if return_display_name:
        return user.display_name
    else:
        return user.name


async def reaction_message_building(
    client, lst_to_show, message_user, fonction_message_builder, *args
):
    """Utilisé par toutes les fonctionnalités du bot (Jukebox et $wag)
        Permet de créer un message interactif avec des réactions, pour
        pouvoir naviguer entre une énorme liste d'élément quelconque.

    Args:
        lst_to_show (lst): La grande liste de chose à afficher, qui
            sera subdiviser en sous-liste
        message_user (Message): Le message de l'utilisateur qui a
            demandé l'affichage de ce message interactif
        fonction_message_builder (Function): Fonction à appelé pour la
            création du message approprié pour chaque sous-liste de
            lst_to_shw.
            Par convention, cette fonction doit commencer par "mini_"

    Returns:
        Message: Le message interractif
    """
    sound_per_page = 15
    chunks_sounds = list(chunks(lst_to_show, sound_per_page))
    nbr_pages = math.ceil(len(lst_to_show) / sound_per_page)
    current_page = 1

    # Envoie du message crée par la fonction_message_builder, défini en entrée.
    message_bot = await message_user.channel.send(
        await fonction_message_builder(
            chunks_sounds[current_page - 1],
            current_page,
            nbr_pages,
            message_user,
            client,
            *args
        )
    )

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
                    content=await fonction_message_builder(
                        chunks_sounds[current_page - 1],
                        current_page,
                        nbr_pages,
                        message_user,
                        client,
                        *args
                    )
                )

            # Si l'émoji précédent est tapé, on recule d'une page
            elif str(reaction.emoji) == "◀️" and current_page > 1:
                current_page -= 1
                await message_bot.edit(
                    content=await fonction_message_builder(
                        chunks_sounds[current_page - 1],
                        current_page,
                        nbr_pages,
                        message_user,
                        client,
                        *args
                    )
                )

            # On retire la réaction faites par l'utilisateur
            await message_bot.remove_reaction(reaction, user)
        # Passé le time out défini dans le client.wait_for, on empêche les
        # gens de continuer de naviguer.
        except asyncio.TimeoutError:
            await message_bot.clear_reactions()
            active = False


async def connect_to_chan(client, chan_to_go):
    """Fonction utilisé par le bot pour se connecter sur un canal vocal,
        En prenant en compte toutes les situations possibles

    Args:
        chan_to_go (VoiceChannel): Le canal vocal où il faut aller

    Returns:
        VoiceClient: l'instance de connexion vocale que le bot utilise
            pour le canal vocal chan_to_go
    """
    for actual_voice_client in client.voice_clients:
        if actual_voice_client.guild == chan_to_go.guild:
            if actual_voice_client.channel == chan_to_go:
                return actual_voice_client
            else:
                # close the old voiceClient in wrong channel, and move to the new
                # channel
                await actual_voice_client.move_to(chan_to_go)
                return actual_voice_client

    # If no VoiceClient is already set, create a new one
    return await chan_to_go.connect()
