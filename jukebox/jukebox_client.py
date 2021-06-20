import discord

from .jukebox import code_recherche, jukebox
from .utils import well_aligned_jukebox_tab, mini_help_message_string

from utils import reaction_message_building, connect_to_chan
from module import Module

from time import sleep


class JukeboxClient(Module):
    def __init__(self, client) -> None:
        self.client = client
        print("Lancement du jukebox...\n")
        self.jukebox = jukebox("sounds")
        # Affichage du nombre de son enregistré par famille (aoe, kaa, duke...)
        print(self.jukebox.jukebox_stat())

    async def process(self, message):
        # Commandes liées aux Jukebox (aoe, war3, kaa etc...)
        if message.content.startswith(self.jukebox.command_tuple):
            await self.execute_jukebox_command(message)

    async def execute_jukebox_command(self, message):
        ##Channel finding
        if message.author.voice is None:
            await message.channel.send(
                "Hey ! Connecte toi sur un canal vocal avant de m'importuner !"
            )
            return
        chanToGo = message.author.voice.channel

        ##Command Processing
        commande = message.content.split(maxsplit=1)

        (
            file_path,
            searchResult,
            search_code_success,
        ) = self.jukebox.searchWithTheCommand(commande[0][1:], commande[1])

        # Gestion des erreurs
        if search_code_success == code_recherche.NO_RESULT:
            await message.channel.send(
                "Aucun son n'a été trouvé <:rip:817165391846703114> Essaye avec d'autres mots/Tags !"
            )
            return

        if search_code_success == code_recherche.SOME_RESULT:
            await message.channel.send(
                "Waa ! Voici ce que j'ai en stock <:charlieKane:771392220430860288> \n"
                "```fix\n"
                f"{well_aligned_jukebox_tab(searchResult)}\n"
                "```Sois plus précis pour lancer le bon son ! :notes:"
            )
            return

        if search_code_success == code_recherche.TOO_MANY_RESULT:
            await message.channel.send(
                "Waa ! J'ai trop de son qui correspondent à ce que tu as demandé ! <:gniknoht:781090046366187540> \n"
                "```diff\n"
                f"{well_aligned_jukebox_tab(searchResult[:15], '-')}\n"
                f"...et encore {len(searchResult) - 15} autres !\n"
                "```\n"
                "Sois plus précis, n'hésite pas à utiliser les **tags** <:hellguy:809774898665881610> !"
            )
            return

        if search_code_success == code_recherche.REQUEST_HELP:
            await reaction_message_building(
                self.client, searchResult, message, mini_help_message_string
            )
            return

        if search_code_success == code_recherche.ONE_RESULT:
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
            sleep(1)

        # Lorsque aucun son n'est joué dans le canal vocal actuel, on lance le son !
        if not vc.is_playing():
            soundToPlay = discord.FFmpegPCMAudio(fileToPlay)
            vc.play(soundToPlay, after=None)
