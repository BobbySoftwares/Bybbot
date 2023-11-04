import disnake
from disnake.ext.commands import Bot

import traceback

from apscheduler.schedulers.asyncio import AsyncIOScheduler

import json

from jukebox.jukebox_client import JukeboxClient
from swag import SwagClient
from maintenance.maintenance_client import MaintenanceClient
from swag.id import UserId

from utils import LOG_CHANNEL_ID

with open("config.json", "r") as json_file:
    client_config = json.load(json_file)

print("Lancement du bot...")

# Mise à jour des droit du bot, qui lui permet d'avoir la liste entière
# des membres d'un serveur
intents = disnake.Intents.default()
intents.members = True

# Création du client
client = Bot(intents=intents)

swag_module = SwagClient(client)

modules = [
    swag_module,
    JukeboxClient(client),
    MaintenanceClient(client, swag_module),
]

# Registration of commands (like slash_commands) MUST be before the bot launch
# That's why register_commands is used outside "on_ready" event
for module in modules:
    module.register_commands()


@client.event
async def on_ready():
    """Fonction lancé lorsque le bot se lance.

    Utilisé pour programmer les fonctions récurrentes, comme la mise
    à jour du $tyle
    """

    print(f"Le bot est loggué avec les id {client.user}")

    for module in modules:
        await module.setup()

    print("Lancement des commandes périodiques\n\n")

    print("Génération du style toute les heures...\n")

    scheduler = AsyncIOScheduler()
    for module in modules:
        await module.add_jobs(scheduler)
    scheduler.start()

    print("Bybbot opérationnel !")

    try:
        await client.get_channel(LOG_CHANNEL_ID).send(
            "Démarrage terminé, prêt à bybbotter des clous !"
        )
    except:
        pass


@client.event
async def on_disconnect():
    """Fonction lancé lorsque le bot se déconnecte"""
    await client.change_presence(status=disnake.Status.offline)


@client.event
async def on_voice_state_update(member, before, after):
    """Fonction appelé lorsque n'importe quel membre d'un serveur où
    le bot est présent change de statut vocal (Changer de canal vocal,
    de déconnecter d'un canal vocal, se connecter d'un canal vocal, se
    mute etc...)

    Utilisée pour déconnecter automatiquement le bot si il se retrouve
    tout seul.

    Args:
        member (Member): Le membre qui vient de changer de statut vocal
        before ([type]): L'ancien statut vocal du membre
        after ([type]) : Le nouveau statut vocal
    """
    # Si l'utilisateur reste au même endroit, pas besoin de faire quoi
    # que ce soit
    if before == after:
        return
    else:
        # si le bot est connecté à des voiceschat
        if client.voice_clients:
            # on vérifie, dans tout les channels vocaux où le bot est
            # présent, si le bot est tout seul
            for bot_chan in client.voice_clients:
                # un gars est parti et le bot est tout seul
                if (
                    before.channel == bot_chan.channel
                    and len(bot_chan.channel.members) == 1
                ):
                    await bot_chan.disconnect()


@client.event
async def on_message(message):
    """Fonction appelé à chaque fois qu'un message est envoyé sur un
    serveur où celui-ci est connecté

    C'est ici qu'il détecte et traite les différentes commandes

    Args:
        message (Message): Le message qui a activé le bot

    """
    # Si le message vient du bot lui même, on ne fait rien
    if message.author == client.user:
        return

    for module in modules:
        try:
            await module.process(message)
        except Exception as e:
            try:
                await client.get_channel(LOG_CHANNEL_ID).send(
                    "Une erreur inattendue est "
                    f"survenue suite à ce message de {message.author.mention} : "
                    f"{message.jump_url}\n"
                    "Le contenu du message est le suivant :\n"
                    f"> {message.content}\n"
                    "L'erreur est la suivante :\n"
                    "```\n"
                    f"{traceback.format_exc()}\n"
                    f"{e}\n"
                    "```"
                )
                await message.channel.send(
                    f"{message.author.mention} ! Une erreur inattendue est survenue. "
                    "Les développeurs viennent d'en être informés. Merci de bien vouloir "
                    "patienter."
                )
            except:
                raise e


# Lancement du client
client.run(client_config.get("token"))
