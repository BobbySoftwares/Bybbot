from typing import Union
from arrow.arrow import Arrow
import disnake

from attr import attrib, attrs
from enum import Enum
from swag.currencies import Style
from swag.id import CagnotteId, UserId, YfuId

from swag.utils import assert_timezone

# Temporary class, waiting for gggto
@attrs(auto_attribs=True)
class YfuPower:
    name: str
    effect: str

    def activate(self, kw_arg):
        pass


@attrs(auto_attribs=True)
class Yfu:
    owner_id: Union[UserId, CagnotteId]
    id: YfuId
    first_name: str
    last_name: str
    clan: str
    avatar_url: str
    generation_date: Arrow
    timezone: str = attrib(validator=assert_timezone)

    power_point: int
    activation_cost: Style
    greed: float  # multiplier of the activation_cost after one activation, should be >= 1
    zenitude: float  # multiplier of the activation_cost after one activation, should be <= 1
    power: YfuPower

    is_baptized: bool = attrib(default=False)

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


class YfuRarity(Enum):
    COMMON = int("0xffffff", base=16)
    UNCOMMON = int("0x1eff00", base=16)
    RARE = int("0x0070dd", base=16)
    EPIC = int("0xa335ee", base=16)
    LEGENDARY = int("0xff8000", base=16)

    @classmethod
    def from_power_point(cls, power_point):
        if power_point < 200:
            return cls.COMMON
        if power_point < 500:
            return cls.UNCOMMON
        if power_point < 1000:
            return cls.RARE
        if power_point < 5000:
            return cls.EPIC
        return cls.LEGENDARY

    def get_color(self):
        return self.value


class YfuNotFound(Exception):
    pass


class YfuDict(dict):
    def __missing__(self, key):
        raise YfuNotFound(key)
