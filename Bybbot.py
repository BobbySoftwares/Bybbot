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
bot_jukebox = jukebox.jukebox("sounds") # On indique le fichier qui contient tout les sons, ici "sounds"
print(bot_jukebox.jukebox_stat())       # Affichage du nombre de son enregistré par famille (aoe, kaa, duke...)

print("Initialisation de la Banque Centrale du $wag...\n")
bot_SwagBank = swag.SwagBank()

print("Lancement du bot...")

ROLE_ID_BOBBY_SWAG = 846736189310238751     #Identifiant unique du rôle "Le bobby swag" 
GUILD_ID_BOBBYCRATIE = 487244765558210580   #ID unique du serveur Bobbycratie

FORBES_CHANNEL_ID_BOBBYCRATIE = 848313360306536448  #ID unique du canal du swag forbes
COMMAND_CHANNEL_ID_BOBBYCRATIE = 848302082150760508 #ID unique du canal swag-command
 
#Liste des émoji utilisé pour le swag-forbes
EMOJI_NUL = ['🤨','😐','😑','🙄','😣','😥','😫','😒','🙃','😲','🙁','😖','😞','😟','😤','😩','😭','😢','😰','😱','🤪','😵','🥴','😠','🤮','🤧','🥺','🙈','🙊','🍞','🤏']

#Mise à jour des droit du bot, qui lui permet d'avoir la liste entière des membres d'un serveur
intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents) #Lancement du client

############################## Fonctions utilitaire ##########################################

def formatNumber(n):
    """ Fonction qui permet de rajouter des espaces fin entre chaque millier d'un nombre
        100000 -> 100 000

    Args:
        n (int/float): le nombre à formater

    Returns:
        String: le nombre, formaté
    """
    return format(n,',').replace(","," ")

def chucks(lst, n):
    """Permet de subdiviser des listes en plusieurs sous-liste de même taille.

    Args:
        lst (liste): La liste à subdiviser
        n (int): taille de chaque sous-liste
    Yields:
        list: liste des sous-listes
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

async def connect_to_chan(chanToGo):
    """ Fonction utilisé par le bot pour se connecter sur un canal vocal,
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
                #close the old voiceClient in wrong channel, and move to the new channel
                await actualVoiceClient.move_to(chanToGo)
                return actualVoiceClient
    
    #If no VoiceClient is already set, create a new one
    return await chanToGo.connect()

def getGuildMemberName(general_username,guild,return_display_name=True):
    """ Permet de récupérer l'objet User en donnant le nom d'utilisateur général discord de quelqu'un

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
    user = discord.utils.get(guild.members, name=split_username[0], discriminator = split_username[1])
    if user == None:
        return general_username

    if return_display_name:
        return user.display_name
    else:
        return user

############################## Fonction ajouté pour le Jukebox  ##############################

def well_agligned_jukebox_tab(lst_sound, begginner_carac,end_carac):
    """ Fonction utilisé pour la fonctionnalité jukebox.
        Affiche plusieurs ligne de son (numéro, [tag], transcription) correctement allignées

    Args:
        lst_sound (Liste de sons (de type jukebox.son)): Liste comportant les sons à afficher
        begginner_carac (String): Caractère à rajouter à chaque début de ligne (utile si on veut utiliser les couleurs)
        end_carac (String): Caractère à rajouter à chaque fin de ligne

    Returns:
        String : Une chaîne de caractère à afficher
    """
    #Détermination de la chaîne de caractère la plus longue pour les tags
    maxsize = 0
    for sound in lst_sound:
        tagsize = len(str(sound.tags).replace("'",""))
        if tagsize > maxsize:
            maxsize = tagsize
    
    codeblock = "" # initialisation de la chaîne de caractère à renvoyer
    for sound in lst_sound:
        if maxsize > 2:
            codeblock += begginner_carac + str(sound.tags).replace("'","").ljust(maxsize) + " || " + str(sound.transcription) + end_carac + "\n"
        else: ## Si il n'y a que des sons sans aucun tag dans le tableau
            codeblock += begginner_carac + str(sound.transcription) + end_carac + "\n"

    return codeblock

############################## Fonctions ajouté pour le $wag #################################

async def updateForbesClassement(guild):
    """Met à jour le classement Forbes dans le #swag-forbes

    Args:
        guild (Guild): Guilde où écrire le classement (Ne sert à rien en soit, car on le fait toujours que en bobbycratie pour le moment)
    """

    Personne_par_message = 15 #Chaque message du $wag forbes ne contient que 15 places

    #Récupération du canal #$wag-forbes
    channelForbes = guild.get_channel(FORBES_CHANNEL_ID_BOBBYCRATIE)

    #Récupération du classement complet
    dico_classement = list(bot_SwagBank.getClassement().items())

    #Subdivision du dictionnaire en sous-liste de taille équitable
    chucks_classement = list(chucks(dico_classement,Personne_par_message))

    #Récupération du nombre de message nécessaire pour écrire tout le classement (c'est le nombre de sous-listes)
    nbr_pages = math.ceil(len(dico_classement) / Personne_par_message)

    #On compte le nombre de message posté dans le $wag forbes
    nbr_message_in_channel = 0
    async for message in channelForbes.history(oldest_first=True):
        nbr_message_in_channel+=1

    #Si le nombre de message du canal est plus petît que le nombre message nécessaire pour écrire le classement
    if nbr_message_in_channel < nbr_pages: # Il faut écrire un nouveau message
        Message = "Nouvelle page de classement en cours d'écriture"
        nouveau_message = await channelForbes.send(Message) #écriture du nouveau message temporaire

    #édition des messages pour mettre à jour le classement
    cpt_message=0
    async for message in channelForbes.history(oldest_first=True):
        await message.edit(content=mini_forbes_swag(chucks_classement[cpt_message],cpt_message+1,guild))
        cpt_message+=1
    
    #update des bonus de st$le
    bot_SwagBank.updateBonusGrowthRate()
    #update du rôle du "Bobby $wag"
    await updateTheSwaggest(guild)

async def updateTheSwaggest(guild):
    """Met à jour l'attribution du rôle "Le Bobby $wag"

    Args:
        guild (Guild): Serveur discord (inutile car c'est uniquement pour la Bobbycratie pour le moment)

    Returns:
        void
    """

    username_swaggest = bot_SwagBank.getTheNewSwaggest() #Récupération du nouveau premier au classement
    if username_swaggest == bot_SwagBank.theSwaggest or guild.id != GUILD_ID_BOBBYCRATIE: #La gestion de rôle n'est qu'en bobbycratie
        return #rien ne se passe si le plus riche est toujours le même
    
    bot_SwagBank.theSwaggest = username_swaggest #Mise à jour du plus riche dans $wagBank

    #Récupération de l'objet User du plus $wag
    member = discord.utils.get(guild.members, name=username_swaggest.split("#")[0], discriminator = username_swaggest.split("#")[1])

    if member == None: # Si l'utilisateur n'existe pas, alors ne rien faire
        return
    #get the role
    role_swag = guild.get_role(ROLE_ID_BOBBY_SWAG)
    #get the older swaggest
    older_swaggers = role_swag.members

    #Retirez le rôle aux anciens "Bobby $wag"
    for old_swagger in older_swaggers:
        await old_swagger.remove_roles(role_swag,reason="N'est plus le plus $wag")

    #Give the role to the new swagger
    await member.add_roles(role_swag,reason="Est maintenant devenu le plus $wag !")

############################## Fonctions ajouté pour le $tyle ################################

async def update_the_style(): #appelé toute les heures
    """ Appelée de manière périodique en fonction des paramètres choisi dans la fonction "on_ready"
        Permet de faire gagner du $tyle à tout les utilisateurs qui ont bloqué leurs $wag, et débloque les comptes déblocables
    """

    bobbycratie_guild = client.get_guild(id=GUILD_ID_BOBBYCRATIE)
    command_channel = client.get_channel(id=COMMAND_CHANNEL_ID_BOBBYCRATIE)

    ## Faire gagner du style à ceux qui ont du swag bloqué :
    bot_SwagBank.everyoneEarnStyle()

    for account_name in bot_SwagBank.getListOfAccount():
        if bot_SwagBank.isBlockingSwag(account_name):
            #On essaye de débloquer le comptes. Cela sera refusé systématiquement si le blocage n'est pas terminé
            try:
                blockedSwag = bot_SwagBank.getBlokedSwag(account_name)
                bot_SwagBank.deblockSwag(account_name)
                member = getGuildMemberName(account_name,bobbycratie_guild,False)
                Message = member.mention +", les `" + str(blockedSwag) + "$wag` que vous aviez bloqué sont à nouveau disponible. Continuer d'en bloquer pour gagner plus de $tyle !" 
                await command_channel.send(Message)
            except(swag.StyleStillBlocked):
                #Si le blocage n'est pas terminé, on fait R frèr
                pass
            
    await updateForbesClassement(bobbycratie_guild) #Mise à jour du classement après les gains de $tyle

############################## Fonctions pour messages interactifs ###########################

async def reaction_message_building(lst_to_show, message_user,fonction_message_builder):
    """ Utilisé par toutes les fonctionnalités du bot (Jukebox et $wag)
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
    chucks_sounds = list(chucks(lst_to_show,sound_per_page))
    nbr_pages = math.ceil(len(lst_to_show) / sound_per_page)
    current_page = 1

    Message = fonction_message_builder(chucks_sounds[current_page-1],current_page,nbr_pages,message_user)

    #Envoie du message crée par la fonction_message_builder, défini en entrée.
    message_bot = await message_user.channel.send(Message)

    #Ajout des réactions initiale
    await message_bot.add_reaction("◀️") 
    await message_bot.add_reaction("▶️")
    active = True

    def check(reaction, user):
        return user == message_user.author and reaction.message == message_bot and str(reaction.emoji) in ["◀️", "▶️"]

    while active:
        try:
            reaction, user = await client.wait_for("reaction_add", timeout=60, check=check)
        
            #Si l'émoji suivant est tapé, on avance d'une page
            if str(reaction.emoji) == "▶️" and current_page != nbr_pages:
                current_page += 1
                await message_bot.edit(content=fonction_message_builder(chucks_sounds[current_page-1],current_page,nbr_pages,message_user))

            #Si l'émoji précédent est tapé, on recule d'une page
            elif str(reaction.emoji) == "◀️" and current_page > 1:
                current_page -= 1
                await message_bot.edit(content=fonction_message_builder(chucks_sounds[current_page-1],current_page,nbr_pages,message_user))
                
            #On retire la réaction faites par l'utilisateur
            await message_bot.remove_reaction(reaction, user)
        #Passé le time out défini dans le client.wait_for, on empêche les gens de continuer de naviguer.
        except asyncio.TimeoutError:
            await message_bot.clear_reactions()
            active = False

def mini_help_message_string(sub_soundlst,current_page,nbr_pages, message_user = None):
    """ Fonction utilisé par la fonctionnalité du Jukebox
        Appelée lorsqu'on veut afficher un message d'aide pour l'affichage du catalogue est son disponible en fonction de la commande

    Args:
        sub_soundlst (lst): sous-liste de son
        current_page (int): La page courante, utilisé pour l'afficher en bas du message
        nbr_pages (int): Le nombre de page total, utilisé pour l'afficher en bas du message
        message_user ([type], optional): Ce paramètre n'a aucune incidence ici. Defaults to None.

    Returns:
        String: Une chaîne de caractère correspondant à un message d'aide pour le jukebox
    """
    Message =  "Voici tout ce que j'ai par rapport à la commande que tu as tappé <:cozmo:774656738469216287>\n"
    Message += "À toi de choisir le son de ton choix <:ris:800855908859117648>```fix\n"
    Message += well_agligned_jukebox_tab(sub_soundlst,"","")
    Message += "Page " + str(current_page) + "/" + str(nbr_pages) + "\n```"

    return Message

def mini_history_swag_message(chuck_transaction,current_page,nbr_pages,message_user):
    """ Fonction utilisé pour la fonctionnalité du $wag
        Appelée lorsqu'on veut afficher une partie de l'historique des transactions du $wag ou de $tyle

    Args:
        chuck_transaction (lst): sous-liste de transaction
        current_page (int): La page courante, utilisé pour l'afficher en bas du message
        nbr_pages (int): Le nombre de page total, utilisé pour l'afficher en bas du message
        message_user (Message): Message de l'utilisateur qui a demandé l'affichage de l'historique

    Returns:
        String : message à envoyer pour visualiser une sous-partie de l'historique
    """

    #Besoin de connaître la valeur de swag la plus grande et le nom d'utilisateur le plus grand parmis
    #l'ensemble de la sous liste pour un affichage au top
    maxTailleValeur = 0
    maxTailleNom = 0
    for transaction in chuck_transaction:
        tailleValeur = len(formatNumber(transaction[2]))
        tailleNom = len(getGuildMemberName(transaction[1],message_user.guild))

        if tailleValeur > maxTailleValeur:
            maxTailleValeur = tailleValeur
        
        if tailleNom > maxTailleNom:
            maxTailleNom = tailleNom

    #On regarde si la transaction contient la partie "currency"
    if len(transaction) == 4:
        currency = transaction[3]
    else:
        currency = "$wag"

    #Écriture du message
    Message = "```ini\n" #on met ini pour la couleur
    for transaction in chuck_transaction:
        if transaction[0] == swag.SwagBank.account.history_movement.GIVE_TO:
            Message += "[ -->"
        else:
            Message += "[ <--"
        Message += "\t" + formatNumber(transaction[2]).ljust(maxTailleValeur) + " "+currency+"\t" + getGuildMemberName(transaction[1],message_user.guild).rjust(maxTailleNom) + "]\n"
    Message += "[Page " + str(current_page) + "/" + str(nbr_pages) + "]\n```"
    return Message

def mini_forbes_swag(chuck_classement,nbr_pages,guild):
    """ Fonction utilisé pour la fonctionnalité du $wag 
        Appelé pour construire des parties du classement forbes sous forme de String

    Args:
        chuck_classement (lst): sous-liste d'une partie du classement
        nbr_pages (int): Nombre de page totale du classement
        guild (Guild): Guilde où est affiché le classement

    Returns:
        String: message à envoyer pour visualiser une partie du classement
    """

    #Besoin de connaître le nom, la valeur de $wag, et la valeur de $tyle le plus long pour l'aligement de chaque colonne
    max_carac = 0
    max_number = 0
    max_style = 0
    for rang in chuck_classement:
        nomDuCompte = rang[0]
        swagEnCompte = rang[1]
        styleEnCompte = round(bot_SwagBank.getStyleBalanceOf(nomDuCompte),3)
        tailleNom = len(getGuildMemberName(nomDuCompte,guild))
        tailleNombre = len(formatNumber(swagEnCompte))
        tailleStyle = len(formatNumber(styleEnCompte))
        if tailleNom > max_carac:
            max_carac = tailleNom
        if tailleNombre > max_number:
            max_number = tailleNombre
        if tailleStyle > max_style:
            max_style = tailleStyle

    Message = "```ini\n"
    cpt = 1 + ((nbr_pages-1)*15)
    dico_medal = {1:" 🥇]",2:" 🥈]",3:" 🥉]"}
    for rang in chuck_classement:
        nomDuCompte = rang[0]
        swagEnCompte = rang[1]
        styleEnCompte = round(bot_SwagBank.getStyleBalanceOf(nomDuCompte),3) #Arrondissement du $tyle à 3 décimales
        Message += "[#"+ str(cpt).zfill(2)
        Message += dico_medal.get(cpt," "+random.choice(EMOJI_NUL)+"]") #Ajoute une médaille si jamais le compteur est à 1, 2 ou 3
        Message += "\t" + getGuildMemberName(nomDuCompte,guild).ljust(max_carac) + "\t" +formatNumber(swagEnCompte).rjust(max_number) + " $wag\t" +"#"+formatNumber(styleEnCompte).rjust(max_style)+" $tyle"
        if bot_SwagBank.isBlockingSwag(nomDuCompte):
            Message += " 🔒"
        Message += "\n"
        cpt+=1
    Message += "\n```"
    return Message

############################## Évènements Bot ################################################

@client.event
async def on_ready():
    """ Fonction lancé lorsque le bot se lance.
        Utilisé pour programmer les fonctions récurrentes, comme la mise à jour du $tyle
    """
    await client.change_presence(status=discord.Status.online)
    print('Le bot est loggué avec les id {0.user}'.format(client))

    print("Mise à jour du classement et des bonus de blocage\n\n")
    await updateForbesClassement(client.get_guild(GUILD_ID_BOBBYCRATIE))

    print("Lancement des commandes périodiques\n\n")

    print("Génération du style toute les heures...\n")

    scheduler = AsyncIOScheduler()
    scheduler.add_job(update_the_style,CronTrigger(hour='*')) #La fonction update_the_style, est programmé pour toute les heures
    #scheduler.add_job(update_the_style,CronTrigger(hour=*)) #Toute les 10 secondes (test uniquement)
    scheduler.start()

    print("Bybbot opérationnel !")

@client.event
async def on_disconnect():
    """Fonction lancé lorsque le bot se déconnecte
    """
    await client.change_presence(status=discord.Status.offline)

@client.event
async def on_voice_state_update(member, before, after):
    """ Fonction appelé lorsque n'importe quel membre d'un serveur où le bot est présent change de statut vocal
        (Changer de canal vocal, de déconnecter d'un canal vocal, se connecter d'un canal vocal, se mute etc...)
        
        Utilisée pour deconnecter automatiquement le bot si il se retrouve tout seul

    Args:
        member (Member): Le membre qui vient de changer de statut vocal
        before ([type]): L'ancien statut vocal du membre
        after ([type]) : Le nouveau statut vocal
    """
    if before == after: ## Si l'utilisateur reste au même endroit, pas besoin de faire quoi que ce soit
        return
    else:
        if client.voice_clients: # si le bot est connecté à des voices chat
            for botChan in client.voice_clients: # on vérifie, dans tout les channels vocaux où le bot est présent, si le bot est tout seul
                if before.channel == botChan.channel and len(botChan.channel.members) == 1: #un gars est parti et le bot est tout seul
                    await botChan.disconnect()

@client.event
async def on_message(message):
    """ Fonction appelé à chaque fois qu'un message est envoyé sur un serveur où celui-ci est connecté
        C'est ici qu'il détecte et traite les différentes commandes

    Args:
        message (Message): Le message qui a activé le bot

    """

    #Si le message vient du bot lui même, on ne fait rien
    if message.author == client.user:
        return

    #Commandes liées au $wag
    if message.content.startswith("!$wag"):
        command_swag = message.content.split()

        if len(command_swag) > 1:
            
            if 'créer' in command_swag:
                try:
                    bot_SwagBank.addAccount(str(message.author))
                    Message = "Bienvenue chez $wagBank™ " + message.author.mention +" !\n\n"
                    Message += "Tu peux maintenant miner du $wag avec la commande `!$wag miner` 💰"
                    await message.channel.send(Message)
                except(swag.AccountAlreadyExist):
                    Message = message.author.mention +", tu possèdes déjà un compte chez $wagBank™ !"
                    await message.channel.send(Message)
                return

            try:
                if 'miner' in command_swag:
                    try:
                        mining_booty = bot_SwagBank.mine(str(message.author))
                        Message = "⛏ " + message.author.mention + " a miné : " + "`"+formatNumber(mining_booty)+"$wag` !"
                        await message.channel.send(Message)
                        await updateForbesClassement(message.guild)
                    except(swag.AlreadyMineToday):
                        Message = "Désolé " + message.author.mention + " mais tu as déjà miné du $wag aujourd'hui 😮 ! Reviens donc demain !"
                        await message.channel.send(Message)
                    return

                if 'solde' in command_swag:
                    montant_swag = bot_SwagBank.getBalanceOf(str(message.author))
                    Message =  "```diff\n+$wag de " + message.author.display_name + " : " + formatNumber(montant_swag) + "\n```"
                    await message.channel.send(Message)
                    return

                if 'historique' in command_swag:
                    history = bot_SwagBank.getHistory(str(message.author))
                    Message = message.author.mention + ", voici l'historique de tes transactions de $wag :\n"
                    await message.channel.send(Message)
                    await reaction_message_building(history,message,mini_history_swag_message)
                    return
                
                if 'payer' in command_swag:

                    try:

                        #Récupération du destinataire
                        destinataire = message.mentions
                        if len(destinataire) != 1:
                            Message = "Merci de mentionner un destinataire (@Bobby Machin) pour lui donner de ton $wag !"
                            await message.channel.send(Message)
                            return

                        #Récupération de la valeur envoyé
                        valeur = [argent for argent in command_swag if argent.isnumeric()]
                        if len(valeur) != 1:
                            raise swag.InvalidValue

                        #envoie du swag
                        try:
                            bot_SwagBank.giveSwag(str(message.author),str(destinataire[0]),int(valeur[0]))
                            Message = "Transaction effectué avec succès ! \n```ini\n["+ message.author.display_name + "\t" + formatNumber(int(valeur[0])) + " $wag\t-->\t" + destinataire[0].display_name + "]\n```"
                            await message.channel.send(Message)
                            await updateForbesClassement(message.guild)
                            return
                        except(swag.NotEnoughSwagInBalance):
                            Message = message.author.mention + " ! Tu ne possèdes pas assez de $wag pour faire cette transaction, vérifie ton solde avec `!$wag solde`"
                            await message.channel.send(Message)
                            return
                    except(swag.InvalidValue):
                        Message = message.author.mention +", la valeur que tu as écrite est incorrecte, elle doit être supérieur à 0 et entière, car le $wag est **indivisible** !"
                        await message.channel.send(Message)
                        return
            except(swag.NoAccountRegistered) as e:
                no_account_guy = "NO_NAME"
                if e.name == str(message.author):
                    no_account_guy = message.author.mention
                elif e.name == str(destinataire[0]):
                    no_account_guy = destinataire[0]
                Message = no_account_guy + ", tu ne possèdes pas de compte chez $wagBank™ <:rip:817165391846703114> !"
                Message +="\n\nRemédie à ce problème en lançant la commande `!$wag créer` et devient véritablement $wag 😎!"
                await message.channel.send(Message)
                return

        
        #Si l'utilisateur se trompe de commande, ce message s'envoie par défaut
        Message = message.author.mention + ", tu sembles perdu, voici les commandes que tu peux utiliser avec ton $wag :\n"
        Message += "```HTTP\n"
        Message += "!$wag créer ~~ Crée un compte chez $wagBank™\n"
        Message += "!$wag solde ~~ Voir ton solde de $wag sur ton compte\n"
        Message += "!$wag miner ~~ Gagner du $wag gratuitement tout les jours\n"
        Message += "!$wag payer [montant] [@destinataire] ~~ Envoie un *montant* de $wag au *destinataire* spécifié\n"
        Message += "!$wag historique ~~ Visualiser l'ensemble des transactions effectuées sur ton compte\n"
        Message +="```"
        await message.channel.send(Message)
        await updateForbesClassement(message.guild)

    #Commande liées au $tyle
    if message.content.startswith("!$tyle"):
        command_style = message.content.split()

        if len(command_style) > 1:
            try:
                if 'info' in command_style:
                    montant_style = bot_SwagBank.getStyleBalanceOf(str(message.author))
                    Message =  "```diff\n+$tyle de " + message.author.display_name + " : " + formatNumber(montant_style) + "\n"
                    Message += "-Taux de bloquage : " + formatNumber(bot_SwagBank.getStyleTotalGrowthRate(str(message.author))) +"%\n"
                    Message += "-$wag actuellement bloqué : " + formatNumber(bot_SwagBank.getBlokedSwag(str(message.author))) +"\n"
                    if bot_SwagBank.isBlockingSwag(str(message.author)):
                        Message += "-Date du déblocage sur $wag : " + str(bot_SwagBank.getDateOfUnblockingSwag(str(message.author))) + "\n" #TODO : Changer l'affichage pour avoir une affichage à la bonne heure, et en français
                    Message += "```"
                    await message.channel.send(Message)
                    return

                if 'bloquer' in command_style:
                    try:
                        #Récupération de la valeur envoyé
                        valeur = [argent for argent in command_style if argent.isnumeric()]
                        if len(valeur) != 1:
                            raise swag.InvalidValue

                        bot_SwagBank.blockSwagToGetStyle(str(message.author),int(valeur[0]))
                        Message = message.author.mention + ", vous venez de bloquer `" + formatNumber(int(valeur[0])) + "$wag` vous les récupérerez dans **" + str(swag.TIME_OF_BLOCK) + " jours** à la même heure\n"
                        await message.channel.send(Message)
                        await updateForbesClassement(message.guild)
                        return
                    except(swag.InvalidValue, swag.NotEnoughSwagInBalance,swag.StyleStillBlocked) as e:
                        if isinstance(e,swag.InvalidValue):
                            Message = message.author.mention +", la valeur que tu as écrite est incorrecte, elle doit être supérieur à 0 et entière, car le $wag est **indivisible** !"
                        elif isinstance(e,swag.NotEnoughSwagInBalance):
                            Message = message.author.mention + " ! Tu ne possèdes pas assez de $wag pour faire cette transaction, vérifie ton solde avec `!$wag solde`"
                        elif isinstance(e,swag.StyleStillBlocked):
                            Message = message.author.mention +", du $wag est déjà bloqué à ton compte chez $tyle Generatoc Inc. ! Attends leurs déblocage pour pouvoir en bloquer de nouveau !"
                        await message.channel.send(Message)
                        return

                if 'payer' in command_style:
                    try:
                        #Récupération du destinataire
                        destinataire = message.mentions
                        if len(destinataire) != 1:
                            Message = "Merci de mentionner un destinataire (@Bobby Machin) pour lui donner de ton $tyle !"
                            await message.channel.send(Message)
                            return

                        #Récupération de la valeur envoyé
                        valeur = [argent for argent in command_style if argent.replace(".","").replace(",","").isnumeric()]
                        if len(valeur) != 1:
                            raise swag.InvalidValue

                        #envoie du style
                        try:
                            bot_SwagBank.giveStyle(str(message.author),str(destinataire[0]),float(valeur[0]))
                            Message = "Transaction effectué avec succès ! \n```ini\n["+ message.author.display_name + "\t" + formatNumber(float(valeur[0])) + " $tyle\t-->\t" + destinataire[0].display_name + "]\n```"
                            await message.channel.send(Message)
                            await updateForbesClassement(message.guild)
                            return
                        except(swag.NotEnoughStyleInBalance):
                            Message = message.author.mention + " ! Tu ne possèdes pas assez de $tyle pour faire cette transaction, vérifie ton solde avec `!$tyle solde`"
                            await message.channel.send(Message)
                            return
                    except(swag.InvalidValue):
                        Message = message.author.mention +", la valeur que tu as écrite est incorrecte, elle doit être supérieur à 0, car le $tyle est **toujours positif** !"
                        await message.channel.send(Message)
                        return
            except (swag.NoAccountRegistered) as e:
                no_account_guy = "NO_NAME"
                if e.name == str(message.author):
                    no_account_guy = message.author.mention
                elif e.name == str(destinataire[0]):
                    no_account_guy = destinataire[0]
                Message = no_account_guy + ", tu ne possèdes pas de compte chez $wagBank™ <:rip:817165391846703114> !"
                Message +="\n\nRemédie à ce problème en lançant la commande `!$wag créer` et devient véritablement $wag 😎!"
                await message.channel.send(Message)
                return

        Message = message.author.mention + ", tu sembles perdu, voici les commandes que tu peux utiliser avec en relation avec ton $tyle :\n"
        Message += "```HTTP\n"
        Message += "!$tyle info ~~ Voir ton solde de $tyle, ton bonus de bloquage, le $wag que tu as bloqué, et la date de déblocage \n"
        Message += "!$tyle payer [montant] [@destinataire] ~~ Envoie un *montant* de $tyle au *destinataire* spécifié\n"
        Message += "!$tyle bloquer [montant] ~~ Bloque un *montant* de $wag pour générer du $tyle pendant quelques jours\n"
        Message +="```"
        await message.channel.send(Message)


    #Commandes liées aux Jukebox (aoe, war3, kaa etc...)
    if message.content.startswith(bot_jukebox.command_tuple):

        ##Channel finding
        if message.author.voice == None:
            await message.channel.send("Hey ! Connecte toi sur un canal vocal avant de m'importuner !")
            return
        chanToGo = message.author.voice.channel

        ##Command Processing
        commande = message.content.split(maxsplit=1)

        file_path, searchResult, search_code_success = bot_jukebox.searchWithTheCommand(commande[0][1:],commande[1])

        # Gestion des erreurs
        if search_code_success == jukebox.code_recherche.NO_RESULT:
            await message.channel.send("Aucun son n'a été trouvé <:rip:817165391846703114> Essaye avec d'autres mots/Tags !")
            return

        if search_code_success == jukebox.code_recherche.SOME_RESULT:
            Message = "Waa ! Voici ce que j'ai en stock <:charlieKane:771392220430860288> \n```fix\n"
            Message += well_agligned_jukebox_tab(searchResult,"","")
            Message += "```\nSois plus précis pour lancer le bon son ! :notes:"
            await message.channel.send(Message)
            return

        if search_code_success == jukebox.code_recherche.TOO_MANY_RESULT:
            Message = "Waa ! J'ai trop de son qui correspondent à ce que tu as demandé ! <:gniknoht:781090046366187540> \n```diff\n"
            Message += well_agligned_jukebox_tab(searchResult[:15],"-","")
            Message += "...et encore " + str(len(searchResult) - 15) + " autres !```\nSois plus précis, n'hésite pas à utiliser les **tags** <:hellguy:809774898665881610> !"
            await message.channel.send(Message)
            return

        if search_code_success == jukebox.code_recherche.REQUEST_HELP:
            await reaction_message_building(searchResult,message,mini_help_message_string)
            return

        if search_code_success == jukebox.code_recherche.ONE_RESULT:
            Message = "Lancement du son :radio: :musical_note:\n```bash\n" + well_agligned_jukebox_tab(searchResult,'"','"') + "```"
            await message.channel.send(Message)

        fileToPlay = file_path

        vc = await connect_to_chan(chanToGo)

        #Si un autre son est actuellement entrain d'être joué, on endors le tread pendant 1 secondes
        while vc.is_playing():
            time.sleep(1)

        #Lorsque aucun son n'est joué dans le canal vocal actuel, on lance le son !
        if not vc.is_playing():
            soundToPlay = discord.FFmpegPCMAudio(fileToPlay)
            vc.play(soundToPlay, after = None)


import json

with open("bot_token.json","r") as json_file:
    client_config = json.load(json_file)

#Lancement du client
client.run(client_config.get("token"))