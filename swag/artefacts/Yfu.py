import json
from arrow.arrow import Arrow
import discord

from attr import attrib, attrs
from enum import Enum

# Temporary class, waiting for gggto
@attrs(auto_attribs=True)
class Yfu_Power:
    name: str
    effect: str

    def activate(self, kw_arg):
        pass


@attrs(auto_attribs=True)
class Yfu:
    first_name: str
    last_name: str
    clan: str
    generation_date: Arrow
    power_point: int
    activation_cost: float
    greed: float  # multiplier of the activation_cost after one activation, should be >= 1
    zenitude: float  # multiplier of the activation_cost after one activation, should be <= 1
    avatar_local_path: str
    avatar_url: str = attrib(init=False)

    power: Yfu_Power

    class YfuRarity(Enum):
        COMMON = int("0xffffff", base=16)
        UNCOMMON = int("0x1eff00", base=16)
        RARE = int("0x0070dd", base=16)
        EPIC = int("0xa335ee", base=16)
        LEGENDARY = int("0xff8000", base=16)

        @classmethod
        def from_power_point(cls, power_point):
            if power_point < 20:
                return cls.COMMON
            if power_point < 40:
                return cls.UNCOMMON
            if power_point < 60:
                return cls.RARE
            if power_point < 80:
                return cls.EPIC
            return cls.LEGENDARY

        def get_color(self):
            return self.value

    def activate(self, kw_arg):
        self.power.activate(kw_arg)
        self.increase_activation_cost()

    def increase_activation_cost(self):
        self.activation_cost *= self.greed

    def reduce_activation_cost(self):
        self.activation_cost *= self.zenitude

    def on_receive(self):
        # Function called when this Yfu is received by a player, can be usefull for passive power
        pass

    def on_loss(self):
        # Function called when this Yfu is no longer on a player account, can be usefull for passive power
        pass


# TODO move this class
class Embed_Yfu(discord.Embed):
    @classmethod
    def from_yfu(cls, yfu: Yfu):
        yfu_dict = {
            "title": f"{yfu.clan} {yfu.first_name} {yfu.last_name}",
            "image": {"url": yfu.avatar_local_path},
            "color": yfu.YfuRarity.from_power_point(yfu.power_point).get_color(),
            "fields": [
                {"name": yfu.power.name, "value": yfu.power.effect, "inline": False},
                {
                    "name": "Coût",
                    "value": f"{yfu.activation_cost} $tyle",
                    "inline": True,
                },
                {"name": "Avidité", "value": f"{yfu.greed}", "inline": True},
                {"name": "Zenitude", "value": f"{yfu.zenitude}", "inline": True},
            ],
            "footer": {"text": f"{yfu.generation_date}"},
        }
        return discord.Embed.from_dict(yfu_dict)


### Temporary : Just for testing ###

YFU_CHANNEL = 929447745822007388

power = Yfu_Power(
    "Erreur de l'administration bancaire", "Permet d'échanger le swag de deux joueurs"
)

yfu_test = Yfu(
    "Sakura",
    "Hitori",
    "✊",
    "09-01-2022",
    64,
    10,
    2.0,
    0.5,
    "https://cdn.discordapp.com/attachments/929447745822007388/929777841980186714/seed0098.png",
    power,
)

intents = discord.Intents.default()
intents.members = True

# Création du client
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    await client.get_channel(YFU_CHANNEL).send(
        client.get_user(178947222103130123).mention + " utilise une Yfu !",
        embed=Embed_Yfu.from_yfu(yfu_test),
    )
    print("Yfu opérationnelle !")


with open("config.json", "r") as json_file:
    client_config = json.load(json_file)

client.run(client_config.get("token"))
