import difflib
from typing import TYPE_CHECKING
import disnake
from disnake.ext import commands

from bobbycall.game import GameEmbed, Gamelist

from utils import GAME_CHANNEL_ID, GUILD_ID, fuzzysearch

if TYPE_CHECKING:
    from bobbycall.bobbycall import Bobbycall



class BobbyCallCommand(commands.Cog):
    def __init__(self, client : 'Bobbycall'):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self,message : disnake.Message):
        if message.channel.id == GAME_CHANNEL_ID:
            await self.client.setup()

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload : disnake.RawMessageUpdateEvent):
        if payload.channel_id == GAME_CHANNEL_ID:
            await self.client.setup()

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload : disnake.RawMessageUpdateEvent):
        if payload.channel_id == GAME_CHANNEL_ID:
            await self.client.setup()

    def autocomplete_game_name(
        self, interaction: disnake.ApplicationCommandInteraction, user_input: str
    ):
        games = fuzzysearch(user_input,self.client.gamelist.get_game_names())
        if len(games) > 25:
            games = games[:25]
        return games

    @commands.slash_command(name="call", guild_ids=[GUILD_ID])
    async def bobbycall(self, interaction: disnake.ApplicationCommandInteraction, jeu : str):
        """
        Annonce aux autres utilisateurs que tu souhaites jouer à un jeu avec eux !
        
        Parameters
        ----------
        jeu : Nom du jeu auquel tu veux jouer.
        """
        
        game = self.client.gamelist.get_game_by_name(jeu)

        users_to_notify = ", ".join([user.mention for user in await game.getPlayers()])

        await interaction.send(users_to_notify, embed= await GameEmbed.from_game(game,interaction.author))
        
        #Get the message object for create the associated thread
        message = await interaction.original_message()

        thread = await message.create_thread(
                                name=f"Partie de {game.name.capitalize()}",
                                auto_archive_duration=1440,
                                reason=f"Bobbycall {game.name} by {interaction.author.display_name}"
                            )
        
        await thread.send("Utilisez ce fil pour organiser votre partie !")
        
    bobbycall.autocomplete("jeu")(autocomplete_game_name)

    #event msg