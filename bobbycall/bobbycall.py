
import disnake
from disnake.ext.commands import Bot
from bobbycall.client import BobbyCallCommand
from bobbycall.game import Gamelist
from module import Module
from utils import GAME_CHANNEL_ID


class Bobbycall(Module):
    
    def __init__(self, discord_client : Bot):
        self.discord_client = discord_client

    def register_commands(self):
        self.discord_client.add_cog(BobbyCallCommand(self))

    async def setup(self):
        print("Initialisation de la liste des jeux")
        self.gamelist = await Gamelist.from_channel(self.discord_client.get_channel(GAME_CHANNEL_ID))