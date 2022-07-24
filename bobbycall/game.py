from email import message
import re
from typing import List
import disnake

import textwrap

URL_REGEX = "[ \t\n]*(?P<url>https?:\/\/[^\s]+)[ \t\n]*"

class Game:
    def __init__(self, message : disnake.Message) -> None:
        self.message = message

    def udpate_message(self, new_message : disnake.Message) -> None:
        self.message = new_message

    @property
    def name(self) -> str:

        name = self.message.content
        matcher = re.search(URL_REGEX,self.message.content)

        if matcher is not None:
            name = name.replace(matcher.group(),'')

        return textwrap.shorten(name, width=24, placeholder="…")

    @property
    def picture_url(self) -> str:

        if len(self.message.attachments) > 0:
            url = self.message.attachments[0].url
        else:
            url = re.search(URL_REGEX,self.message.content).group("url")

        return url 

    async def getPlayers(self)  -> List[disnake.Member]:
        #find the ✅
        green_mark_reaction = None
        for reaction in self.message.reactions:
            if reaction.emoji == '✅':
                green_mark_reaction = reaction
                break
        
        if green_mark_reaction is None:
            return []

        return await green_mark_reaction.users().flatten()

class Gamelist:

    def __init__(self) -> None:
        self.games : List[Game] = []

    @classmethod
    async def from_channel(cls, channel : disnake.TextChannel):
        gamelist =  cls()

        async for message in channel.history(limit=None, oldest_first=True):
            gamelist.add_game(message)

        return gamelist

    def add_game(self,message : disnake.Message) -> None:
        if message.content is not None and (len(message.attachments) == 1 or re.search(URL_REGEX,message.content) is not None):
            self.games.append(Game(message))

    def get_game_names(self) -> List[str]:
        return [game.name for game in self.games]

    def get_game_by_name(self, search_name : str) -> Game:
        return next((game for game in self.games if game.name == search_name),None)


            
class GameEmbed(disnake.Embed):
    @classmethod
    async def from_game(cls,game : Game, caller : disnake.User):

        embed_dict = {
            "title": f" 📣🎮 {caller.name} veut jouer à {game.name} !",
            "thumbnail" : {"url": caller.avatar.url},
            "description" : f"{caller.name} veut faire une partie de {game.name}, vous êtes partant ? \n\nPour être prévenu des prochaines parties, cocher ✅ dans [#{game.message.channel}]({game.message.jump_url}).",
            "image" : {
                "url" : f"{game.picture_url}",
            },
        }

        return cls.from_dict(embed_dict)