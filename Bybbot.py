import discord

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

import jukebox
import swag
import time
import math
import asyncio
import random

############################## INITIALISATION ################################################

print("Lancement du jukebox...\n")
bot_jukebox = jukebox.jukebox(
    "sounds"
)  # On indique le fichier qui contient tout les sons, ici "sounds"
print(
    bot_jukebox.jukebox_stat()
)  # Affichage du nombre de son enregistré par famille (aoe, kaa, duke...)

print("Initialisation de la Banque Centrale du $wag...\n")
bot_SwagBank = swag.SwagBank()

print("Lancement du bot...")

ROLE_ID_BOBBY_SWAG = 846736189310238751  # Identifiant unique du rôle "Le bobby swag"
GUILD_ID_BOBBYCRATIE = 487244765558210580  # ID unique du serveur Bobbycratie

FORBES_CHANNEL_ID_BOBBYCRATIE = 848313360306536448  # ID unique du canal du swag forbes
COMMAND_CHANNEL_ID_BOBBYCRATIE = 848302082150760508  # ID unique du canal swag-command


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

# Mise à jour des droit du bot, qui lui permet d'avoir la liste entière des membres d'un serveur
intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)  # Lancement du client

############################## Fonctions utilitaire ##########################################


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


async def connect_to_chan(chanToGo):
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


############################## Fonction ajouté pour le Jukebox  ##############################


def well_aligned_jukebox_tab(lst_sound, prefix="", suffix=""):
    """Affiche sur plusieurs lignes les informations (numéro, [tag],
    transcription) associées à la liste de sons spécifiée.

    Fait partie de la fonctionnalité jukebox.

    Args:
        lst_sound (List[jukebox.son]): Liste des sons à afficher
        prefix (str): Caractère préfixant chaque ligne (utile pour
            utiliser les couleurs)
        suffix (str): Caractère suffixant chaque ligne

    Returns:
        str : La chaîne de caractère à afficher
    """
    # TODO: Check if replace("'", "") is needed
    # TODO: Remove need for this list
    tags = [str(sound.tags).replace("'", "") for sound in lst_sound]

    # Détermination de la chaîne de caractère la plus longue pour les tags
    width = max(len(tag) for tag in tags)

    if width > 2:
        return "\n".join(
            f"{prefix}{tag : <{width})} || {sound.transcription}{suffix}"
            for sound, tag in zip(lst_sound, tags)
        )
    else:  ## Si il n'y a que des sons sans aucun tag dans le tableau
        return "\n".join(
            f"{prefix}{sound.transcription}{suffix}" for sound in lst_sound
        )


############################## Fonctions ajouté pour le $wag #################################


async def updateForbesClassement(guild):
    """Met à jour le classement Forbes dans le #swag-forbes

    Args:
        guild (Guild): Guilde où écrire le classement (Ne sert à rien en soit, car on le fait toujours que en bobbycratie pour le moment)
    """

    Personne_par_message = 15  # Chaque message du $wag forbes ne contient que 15 places

    # Récupération du canal #$wag-forbes
    channelForbes = guild.get_channel(FORBES_CHANNEL_ID_BOBBYCRATIE)

    # Récupération du classement complet
    dico_classement = list(bot_SwagBank.getClassement().items())

    # Subdivision du dictionnaire en sous-liste de taille équitable
    chunks_classement = list(chunks(dico_classement, Personne_par_message))

    # Récupération du nombre de message nécessaire pour écrire tout le classement (c'est le nombre de sous-listes)
    nbr_pages = math.ceil(len(dico_classement) / Personne_par_message)

    # On compte le nombre de message posté dans le $wag forbes
    nbr_message_in_channel = 0
    async for message in channelForbes.history(oldest_first=True):
        nbr_message_in_channel += 1

    # Si le nombre de message du canal est plus petît que le nombre message nécessaire pour écrire le classement
    if nbr_message_in_channel < nbr_pages:  # Il faut écrire un nouveau message
        Message = "Nouvelle page de classement en cours d'écriture"
        nouveau_message = await channelForbes.send(
            Message
        )  # écriture du nouveau message temporaire

    # édition des messages pour mettre à jour le classement
    cpt_message = 0
    async for message in channelForbes.history(oldest_first=True):
        await message.edit(
            content=mini_forbes_swag(
                chunks_classement[cpt_message], cpt_message + 1, guild
            )
        )
        cpt_message += 1

    # update des bonus de st$le
    bot_SwagBank.updateBonusGrowthRate()
    # update du rôle du "Bobby $wag"
    await updateTheSwaggest(guild)


async def updateTheSwaggest(guild):
    """Met à jour l'attribution du rôle "Le Bobby $wag"

    Args:
        guild (Guild): Serveur discord (inutile car c'est uniquement pour la Bobbycratie pour le moment)

    Returns:
        void
    """

    username_swaggest = (
        bot_SwagBank.getTheNewSwaggest()
    )  # Récupération du nouveau premier au classement
    if (
        username_swaggest == bot_SwagBank.theSwaggest
        or guild.id != GUILD_ID_BOBBYCRATIE
    ):  # La gestion de rôle n'est qu'en bobbycratie
        return  # rien ne se passe si le plus riche est toujours le même

    bot_SwagBank.theSwaggest = (
        username_swaggest  # Mise à jour du plus riche dans $wagBank
    )

    # Récupération de l'objet User du plus $wag
    member = discord.utils.get(
        guild.members,
        name=username_swaggest.split("#")[0],
        discriminator=username_swaggest.split("#")[1],
    )

    if member == None:  # Si l'utilisateur n'existe pas, alors ne rien faire
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


############################## Fonctions ajouté pour le $tyle ################################


async def update_the_style():  # appelé toute les heures
    """Appelée de manière périodique en fonction des paramètres choisi dans la fonction "on_ready"
    Permet de faire gagner du $tyle à tout les utilisateurs qui ont bloqué leurs $wag, et débloque les comptes déblocables
    """

    bobbycratie_guild = client.get_guild(id=GUILD_ID_BOBBYCRATIE)
    command_channel = client.get_channel(id=COMMAND_CHANNEL_ID_BOBBYCRATIE)

    ## Faire gagner du style à ceux qui ont du swag bloqué :
    bot_SwagBank.everyoneEarnStyle()

    for account_name in bot_SwagBank.getListOfAccount():
        if bot_SwagBank.isBlockingSwag(account_name):
            # On essaye de débloquer le comptes. Cela sera refusé systématiquement si le blocage n'est pas terminé
            try:
                blockedSwag = bot_SwagBank.getBlokedSwag(account_name)
                bot_SwagBank.deblockSwag(account_name)
                member = getGuildMemberName(account_name, bobbycratie_guild, False)
                await command_channel.send(
                    f"{member.mention}, les `{blockedSwag} $wag` que vous aviez"
                    f"bloqué sont à nouveau disponible. Continuez d'en bloquer"
                    f"pour gagner plus de $tyle !"
                )
            except (swag.StyleStillBlocked):
                # Si le blocage n'est pas terminé, on fait R frèr
                pass

    await updateForbesClassement(
        bobbycratie_guild
    )  # Mise à jour du classement après les gains de $tyle


############################## Fonctions pour messages interactifs ###########################


async def reaction_message_building(
    lst_to_show, message_user, fonction_message_builder
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


def mini_help_message_string(sub_soundlst, current_page, nbr_pages, message_user=None):
    """Fonction utilisé par la fonctionnalité du Jukebox
        Appelée lorsqu'on veut afficher un message d'aide pour l'affichage du catalogue est son disponible en fonction de la commande

    Args:
        sub_soundlst (lst): sous-liste de son
        current_page (int): La page courante, utilisé pour l'afficher en bas du message
        nbr_pages (int): Le nombre de page total, utilisé pour l'afficher en bas du message
        message_user ([type], optional): Ce paramètre n'a aucune incidence ici. Defaults to None.

    Returns:
        String: Une chaîne de caractère correspondant à un message d'aide pour le jukebox
    """
    return (
        "Voici ce que j'ai en stock <:cozmo:774656738469216287>.\n"
        "Tu dois choisir judicieusement <:ris:800855908859117648> !\n"
        "```fix\n"
        f"{well_aligned_jukebox_tab(sub_soundlst)}\n"
        f"Page {current_page}/{nbr_pages}\n```"
    )


def mini_history_swag_message(chunk_transaction, current_page, nbr_pages, message_user):
    """Fonction utilisé pour la fonctionnalité du $wag
        Appelée lorsqu'on veut afficher une partie de l'historique des transactions du $wag ou de $tyle

    Args:
        chunk_transaction (lst): sous-liste de transaction
        current_page (int): La page courante, utilisé pour l'afficher en bas du message
        nbr_pages (int): Le nombre de page total, utilisé pour l'afficher en bas du message
        message_user (Message): Message de l'utilisateur qui a demandé l'affichage de l'historique

    Returns:
        String : message à envoyer pour visualiser une sous-partie de l'historique
    """
    transactions = [
        (
            way,
            formatNumber(amount),
            getGuildMemberName(second_party, message_user.guild),
            currency if currency else "$wag",
        )
        for (way, second_party, amount, *currency) in chunk_transaction
    ]

    # Besoin de connaître la valeur de swag la plus grande et le nom d'utilisateur le plus grand parmis
    # l'ensemble de la sous liste pour un affichage au top
    col1 = max(len(amount) for _, amount, _ in transactions)
    col2 = max(len(second_party) for _, _, second_party in transactions)

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


def mini_forbes_swag(chunk_classement, nbr_pages, guild):
    """Fonction utilisé pour la fonctionnalité du $wag
        Appelé pour construire des parties du classement forbes sous forme de String

    Args:
        chunk_classement (lst): sous-liste d'une partie du classement
        nbr_pages (int): Nombre de page totale du classement
        guild (Guild): Guilde où est affiché le classement

    Returns:
        String: message à envoyer pour visualiser une partie du classement
    """

    def display_style_of(user):
        style_amount = bot_SwagBank.getStyleBalanceOf(user)
        formatNumber(round(style_amount, 3))

    forbes = [
        (
            getGuildMemberName(user, guild),
            formatNumber(swag_amount),
            display_style_of(user),
        )
        for (user, swag_amount) in chunk_classement
    ]
    # Besoin de connaître le nom, la valeur de $wag, et la valeur de $tyle le plus long pour l'aligement de chaque colonne
    col1 = max(len(user) for user, _, _ in forbes)
    col2 = max(len(swag_amount) for _, swag_amount, _ in forbes)
    col3 = max(len(style_amount) for _, _, style_amount in forbes)

    offset = 1 + ((nbr_pages - 1) * 15)
    content = "\n".join(
        f"[#{rank + offset:02} {forbes_medal(rank + offset)}]\t"
        f"{user : <{col1}}\t"
        f"{swag_amount : >{col2}} $wag\t"
        f"#{style_amount : >{col3}} $tyle"
        f"#{' 🔒' if bot_SwagBank.isBlockingSwag(user) else ''}"
        for rank, (user, swag_amount, style_amount) in enumerate(forbes)
    )
    return f"```ini\n{content}"


############################## Évènements Bot ################################################


@client.event
async def on_ready():
    """Fonction lancé lorsque le bot se lance.
    Utilisé pour programmer les fonctions récurrentes, comme la mise à jour du $tyle
    """
    await client.change_presence(status=discord.Status.online)
    print("Le bot est loggué avec les id {0.user}".format(client))

    print("Mise à jour du classement et des bonus de blocage\n\n")
    await updateForbesClassement(client.get_guild(GUILD_ID_BOBBYCRATIE))

    print("Lancement des commandes périodiques\n\n")

    print("Génération du style toute les heures...\n")

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        update_the_style, CronTrigger(hour="*")
    )  # La fonction update_the_style, est programmé pour toute les heures
    # scheduler.add_job(update_the_style,CronTrigger(hour=*)) #Toute les 10 secondes (test uniquement)
    scheduler.start()

    print("Bybbot opérationnel !")


@client.event
async def on_disconnect():
    """Fonction lancé lorsque le bot se déconnecte"""
    await client.change_presence(status=discord.Status.offline)


@client.event
async def on_voice_state_update(member, before, after):
    """Fonction appelé lorsque n'importe quel membre d'un serveur où le bot est présent change de statut vocal
        (Changer de canal vocal, de déconnecter d'un canal vocal, se connecter d'un canal vocal, se mute etc...)

        Utilisée pour deconnecter automatiquement le bot si il se retrouve tout seul

    Args:
        member (Member): Le membre qui vient de changer de statut vocal
        before ([type]): L'ancien statut vocal du membre
        after ([type]) : Le nouveau statut vocal
    """
    if (
        before == after
    ):  ## Si l'utilisateur reste au même endroit, pas besoin de faire quoi que ce soit
        return
    else:
        if client.voice_clients:  # si le bot est connecté à des voices chat
            for (
                botChan
            ) in (
                client.voice_clients
            ):  # on vérifie, dans tout les channels vocaux où le bot est présent, si le bot est tout seul
                if (
                    before.channel == botChan.channel
                    and len(botChan.channel.members) == 1
                ):  # un gars est parti et le bot est tout seul
                    await botChan.disconnect()


async def execute_swag_command(message):
    command_swag = message.content.split()

    if len(command_swag) > 1:
        try:
            if "créer" in command_swag:
                bot_SwagBank.addAccount(str(message.author))
                await message.channel.send(
                    f"Bienvenue chez $wagBank™ {message.author.mention} !\n\n"
                    "Tu peux maintenant miner du $wag avec la commande `!$wag miner` 💰"
                )

            elif "miner" in command_swag:
                mining_booty = bot_SwagBank.mine(str(message.author))
                await message.channel.send(
                    f"⛏ {message.author.mention} a miné `{formatNumber(mining_booty)} $wag` !"
                )
                await updateForbesClassement(message.guild)

            elif "solde" in command_swag:
                montant_swag = bot_SwagBank.getBalanceOf(str(message.author))
                await message.channel.send(
                    "```diff\n"
                    f"$wag de {message.author.display_name} : {formatNumber(montant_swag)}\n"
                    "```"
                )

            elif "historique" in command_swag:
                history = bot_SwagBank.getHistory(str(message.author))
                await message.channel.send(
                    f"{message.author.mention}, voici l'historique de tes transactions de $wag :\n"
                )
                await reaction_message_building(
                    history, message, mini_history_swag_message
                )

            elif "payer" in command_swag:
                # Récupération du destinataire
                destinataire = message.mentions
                if len(destinataire) != 1:
                    await message.channel.send(
                        "Merci de mentionner un destinataire (@Bobby Machin) pour lui donner de ton $wag !"
                    )
                    return

                # Récupération de la valeur envoyé
                valeur = [argent for argent in command_swag if argent.isnumeric()]
                if len(valeur) != 1:
                    raise swag.InvalidValue

                # envoie du swag
                bot_SwagBank.giveSwag(
                    str(message.author),
                    str(destinataire[0]),
                    int(valeur[0]),
                )
                await message.channel.send(
                    "Transaction effectué avec succès ! \n"
                    "```ini\n"
                    f"[{message.author.display_name}\t{formatNumber(int(valeur[0]))} $wag\t-->\t{destinataire[0].display_name}]\n"
                    "```"
                )
                await updateForbesClassement(message.guild)

        except (swag.NotEnoughSwagInBalance):
            await message.channel.send(
                f"{message.author.mention} ! Tu ne possèdes pas assez de $wag pour faire cette transaction, vérifie ton solde avec `!$wag solde`"
            )
            return
        except (swag.InvalidValue):
            await message.channel.send(
                f"{message.author.mention}, la valeur que tu as écrite est incorrecte, elle doit être supérieur à 0 et entière, car le $wag est **indivisible** !"
            )
            return
        except (swag.AlreadyMineToday):
            await message.channel.send(
                f"Désolé {message.author.mention}, mais tu as déjà miné du $wag aujourd'hui 😮 ! Reviens donc demain !"
            )
        except (swag.NoAccountRegistered) as e:
            no_account_guy = "NO_NAME"
            if e.name == str(message.author):
                no_account_guy = message.author.mention
            elif e.name == str(destinataire[0]):
                no_account_guy = destinataire[0]
            await message.channel.send(
                f"{no_account_guy}, tu ne possèdes pas de compte chez $wagBank™ <:rip:817165391846703114> !\n\n"
                "Remédie à ce problème en lançant la commande `!$wag créer` et devient véritablement $wag 😎!"
            )
            return

    # Si l'utilisateur se trompe de commande, ce message s'envoie par défaut
    await message.channel.send(
        f"{message.author.mention}, tu sembles perdu, voici les commandes que tu peux utiliser avec ton $wag :\n"
        "```HTTP\n"
        "!$wag créer ~~ Crée un compte chez $wagBank™\n"
        "!$wag solde ~~ Voir ton solde de $wag sur ton compte\n"
        "!$wag miner ~~ Gagner du $wag gratuitement tout les jours\n"
        "!$wag payer [montant] [@destinataire] ~~ Envoie un *montant* de $wag au *destinataire* spécifié\n"
        "!$wag historique ~~ Visualiser l'ensemble des transactions effectuées sur ton compte\n"
        "```"
    )
    await updateForbesClassement(message.guild)


async def execute_style_command(message):
    command_style = message.content.split()

    try:
        if len(command_style) > 1:
            if "info" in command_style:
                style_amount = bot_SwagBank.getStyleBalanceOf(str(message.author))
                growth_rate = bot_SwagBank.getStyleTotalGrowthRate(str(message.author))
                blocked_swag = bot_SwagBank.getBlokedSwag(str(message.author))
                # TODO : Changer l'affichage pour avoir une affichage à la bonne heure, et en français
                release_info = (
                    f"-Date du déblocage sur $wag : {bot_SwagBank.getDateOfUnblockingSwag(str(message.author))}\n"
                    if bot_SwagBank.isBlockingSwag(str(message.author))
                    else ""
                )
                await message.channel.send(
                    "```diff\n"
                    f"$tyle de {message.author.display_name} : {formatNumber(style_amount)}\n"
                    f"-Taux de bloquage : {formatNumber(growth_rate)} %\n"
                    f"-$wag actuellement bloqué : {formatNumber(blocked_swag)}\n"
                    f"{release_info}"
                    "```"
                )

            elif "bloquer" in command_style:
                # Récupération de la valeur envoyé
                valeur = [argent for argent in command_style if argent.isnumeric()]
                if len(valeur) != 1:
                    raise swag.InvalidValue

                bot_SwagBank.blockSwagToGetStyle(str(message.author), int(valeur[0]))
                await message.channel.send(
                    f"{message.author.mention}, vous venez de bloquer `{formatNumber(int(valeur[0]))}$wag` vous les récupérerez dans **{swag.TIME_OF_BLOCK} jours** à la même heure\n"
                )
                await updateForbesClassement(message.guild)

            elif "payer" in command_style:
                # Récupération du destinataire
                destinataire = message.mentions
                if len(destinataire) != 1:
                    Message = "Merci de mentionner un destinataire (@Bobby Machin) pour lui donner de ton $tyle !"
                    await message.channel.send(Message)
                    return

                # Récupération de la valeur envoyé
                valeur = [
                    argent
                    for argent in command_style
                    if argent.replace(".", "").replace(",", "").isnumeric()
                ]
                if len(valeur) != 1:
                    raise swag.InvalidValue

                # envoie du style
                bot_SwagBank.giveStyle(
                    str(message.author),
                    str(destinataire[0]),
                    float(valeur[0]),
                )
                await message.channel.send(
                    "Transaction effectué avec succès ! \n"
                    "```ini\n"
                    f"[{message.author.display_name}\t{formatNumber(float(valeur[0]))} $tyle\t-->\t{destinataire[0].display_name}]\n"
                    "```"
                )
                await updateForbesClassement(message.guild)
    except (
        swag.InvalidValue,
        swag.NotEnoughSwagInBalance,
        swag.StyleStillBlocked,
    ) as e:
        if isinstance(e, swag.InvalidValue):
            Message = f"{message.author.mention}, la valeur que tu as écrite est incorrecte, elle doit être supérieur à 0 et entière, car le $wag est **indivisible** !"
        elif isinstance(e, swag.NotEnoughSwagInBalance):
            Message = f"{message.author.mention} ! Tu ne possèdes pas assez de $wag pour faire cette transaction, vérifie ton solde avec `!$wag solde`"
        elif isinstance(e, swag.StyleStillBlocked):
            Message = f"{message.author.mention}, du $wag est déjà bloqué à ton compte chez $tyle Generatoc Inc. ! Attends leurs déblocage pour pouvoir en bloquer de nouveau !"
        await message.channel.send(Message)
    except (swag.NotEnoughStyleInBalance):
        await message.channel.send(
            f"{message.author.mention} ! Tu ne possèdes pas assez de $tyle pour faire cette transaction, vérifie ton solde avec `!$tyle solde`"
        )
    except (swag.InvalidValue):
        await message.channel.send(
            f"{message.author.mention}, la valeur que tu as écrite est incorrecte, elle doit être supérieur à 0, car le $tyle est **toujours positif** !"
        )
    except (swag.NoAccountRegistered) as e:
        no_account_guy = "NO_NAME"
        if e.name == str(message.author):
            no_account_guy = message.author.mention
        elif e.name == str(destinataire[0]):
            no_account_guy = destinataire[0]
        await message.channel.send(
            f"{no_account_guy}, tu ne possèdes pas de compte chez $wagBank™ <:rip:817165391846703114> !\n\n"
            "Remédie à ce problème en lançant la commande `!$wag créer` et devient véritablement $wag 😎!"
        )

    await message.channel.send(
        f"{message.author.mention}, tu sembles perdu, voici les commandes que tu peux utiliser avec en relation avec ton $tyle :\n"
        "```HTTP\n"
        "!$tyle info ~~ Voir ton solde de $tyle, ton bonus de bloquage, le $wag que tu as bloqué, et la date de déblocage \n"
        "!$tyle payer [montant] [@destinataire] ~~ Envoie un *montant* de $tyle au *destinataire* spécifié\n"
        "!$tyle bloquer [montant] ~~ Bloque un *montant* de $wag pour générer du $tyle pendant quelques jours\n"
        "```"
    )


async def execute_jukebox_command(message):
    ##Channel finding
    if message.author.voice is None:
        await message.channel.send(
            "Hey ! Connecte toi sur un canal vocal avant de m'importuner !"
        )
        return
    chanToGo = message.author.voice.channel

    ##Command Processing
    commande = message.content.split(maxsplit=1)

    file_path, searchResult, search_code_success = bot_jukebox.searchWithTheCommand(
        commande[0][1:], commande[1]
    )

    # Gestion des erreurs
    if search_code_success == jukebox.code_recherche.NO_RESULT:
        await message.channel.send(
            "Aucun son n'a été trouvé <:rip:817165391846703114> Essaye avec d'autres mots/Tags !"
        )
        return

    if search_code_success == jukebox.code_recherche.SOME_RESULT:
        await message.channel.send(
            "Waa ! Voici ce que j'ai en stock <:charlieKane:771392220430860288> \n"
            "```fix\n"
            f"{well_aligned_jukebox_tab(searchResult)}\n"
            "```Sois plus précis pour lancer le bon son ! :notes:"
        )
        return

    if search_code_success == jukebox.code_recherche.TOO_MANY_RESULT:
        await message.channel.send(
            "Waa ! J'ai trop de son qui correspondent à ce que tu as demandé ! <:gniknoht:781090046366187540> \n"
            "```diff\n"
            f"{well_aligned_jukebox_tab(searchResult[:15], '-')}\n"
            f"...et encore {len(searchResult) - 15} autres !\n"
            "```\n"
            "Sois plus précis, n'hésite pas à utiliser les **tags** <:hellguy:809774898665881610> !"
        )
        return

    if search_code_success == jukebox.code_recherche.REQUEST_HELP:
        await reaction_message_building(searchResult, message, mini_help_message_string)
        return

    if search_code_success == jukebox.code_recherche.ONE_RESULT:
        await message.channel.send(
            "Lancement du son :radio: :musical_note:\n"
            "```bash\n"
            f'"{well_aligned_jukebox_tab(searchResult)}"\n'
            "```"
        )

    fileToPlay = file_path

    vc = await connect_to_chan(chanToGo)

    # Si un autre son est actuellement entrain d'être joué, on endors le tread pendant 1 secondes
    while vc.is_playing():
        time.sleep(1)

    # Lorsque aucun son n'est joué dans le canal vocal actuel, on lance le son !
    if not vc.is_playing():
        soundToPlay = discord.FFmpegPCMAudio(fileToPlay)
        vc.play(soundToPlay, after=None)


@client.event
async def on_message(message):
    """Fonction appelé à chaque fois qu'un message est envoyé sur un serveur où celui-ci est connecté
        C'est ici qu'il détecte et traite les différentes commandes

    Args:
        message (Message): Le message qui a activé le bot

    """

    # Si le message vient du bot lui même, on ne fait rien
    if message.author == client.user:
        return

    # Commandes liées au $wag
    if message.content.startswith("!$wag"):
        execute_swag_command(message)

    # Commande liées au $tyle
    elif message.content.startswith("!$tyle"):
        execute_style_command(message)

    # Commandes liées aux Jukebox (aoe, war3, kaa etc...)
    if message.content.startswith(bot_jukebox.command_tuple):
        execute_jukebox_command(message)


import json

with open("bot_token.json", "r") as json_file:
    client_config = json.load(json_file)

# Lancement du client
client.run(client_config.get("token"))
