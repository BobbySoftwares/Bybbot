import difflib
from typing import TYPE_CHECKING
import disnake
from disnake.ext import commands

from bobbycall.game import GameEmbed, Gamelist

from utils import GUILD_ID, fuzzysearch

if TYPE_CHECKING:
    from bobbycall.bobbycall import Bobbycall



class BobbyCallCommand(commands.Cog):
    def __init__(self, client : 'Bobbycall'):
        self.client = client

    def autocomplete_game_name(
        self, interaction: disnake.ApplicationCommandInteraction, user_input: str
    ):
        return fuzzysearch(user_input,self.client.gamelist.get_game_names())

    @commands.slash_command(name="call", guild_ids=[GUILD_ID])
    async def bobbycall(self, interaction: disnake.ApplicationCommandInteraction, jeu : str):
        
        game = self.client.gamelist.get_game_by_name(jeu)

        users_to_notify = ", ".join([user.mention for user in await game.getPlayers()])

        await interaction.send(users_to_notify, embed= await GameEmbed.from_game(game,interaction.author))

    bobbycall.autocomplete("jeu")(autocomplete_game_name)

    #event msg