from typing import Union
from arrow.arrow import Arrow
import discord

from attr import attrib, attrs
from enum import Enum
from swag.currencies import Style
from swag.id import CagnotteId, UserId

from swag.utils import assert_timezone

# Temporary class, waiting for gggto
@attrs(auto_attribs=True)
class Yfu_Power:
    name: str
    effect: str

    def activate(self, kw_arg):
        pass


@attrs(auto_attribs=True)
class Yfu:
    owner: Union[UserId, CagnotteId]
    first_name: str
    last_name: str
    clan: str
    generation_date: Arrow
    timezone: str = attrib(validator=assert_timezone)
    power_point: int
    activation_cost: Style
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
            "image": {"url": yfu.avatar_url},
            "color": yfu.YfuRarity.from_power_point(yfu.power_point).get_color(),
            "fields": [
                {"name": yfu.power.name, "value": yfu.power.effect, "inline": False},
                {
                    "name": "Coût",
                    "value": f"{yfu.activation_cost}",
                    "inline": True,
                },
                {"name": "Avidité", "value": f"{yfu.greed}", "inline": True},
                {"name": "Zenitude", "value": f"{yfu.zenitude}", "inline": True},
            ],
            "footer": {"text": f"{yfu.generation_date.format('YYYY-MM-DD')}"},
        }
        return discord.Embed.from_dict(yfu_dict)
