from decimal import Decimal
from typing import Union
from arrow.arrow import Arrow
import disnake

from attr import attrib, attrs
from enum import Enum
from swag.currencies import Style
from swag.id import CagnotteId, UserId, YfuId
from .powers.power import Active, Passive, Power

from swag.utils import assert_timezone
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
    initial_activation_cost: Style
    activation_cost: Style
    greed: Decimal  # multiplier of the activation_cost after one activation, should be >= 1
    zenitude: Decimal  # divided of the activation_cost after one activation, should be >= 1
    power: Power

    is_baptized: bool = attrib(default=False)

    def activate(self, kw_arg):
        self.power.activate(kw_arg)
        self.increase_activation_cost()

    def increase_activation_cost(self):
        """
        Increase the cost of the activation of the Yfu power by her greed.
        """
        self.activation_cost *= self.greed

    def reduce_activation_cost(self):
        """
        Reduice the cost of the activation of the Yfu power by her zenitude.

        The activation cost can't be less than the initial_activation_cost.
        """
        if (self.activation_cost / self.zenitude >= self.initial_activation_cost):
            self.activation_cost /= self.zenitude
            
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
