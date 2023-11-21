from decimal import Decimal
from typing import Union
from arrow.arrow import Arrow
import disnake
from numpy import log2

from attr import attrib, attrs
from enum import Enum
from swag.currencies import Style
from swag.id import CagnotteId, UserId, YfuId
from .powers.power import Active, Passive, Power

from swag.assert_timezone import assert_timezone


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

    power_points: int
    initial_activation_cost: Style
    power: Power
    last_activation_date: Arrow = attrib(default=Arrow.min)

    is_baptized: bool = attrib(default=False)

    @property
    def cost(self):
        return self.initial_activation_cost * Style(self.power.cost_factor)

    def activate(self, db, targets, activation_date):
        self.power._activation(db, self.owner_id, targets)
        self.last_activation_date = activation_date


class YfuColor(Enum):
    COMMON = (1, int("0xffffff", base=16))
    UNCOMMON = (2, int("0x1eff00", base=16))
    RARE = (3, int("0x0070dd", base=16))
    EPIC = (4, int("0xa335ee", base=16))
    MYTHIC = (5, int("0xff8000", base=16))
    LEGENDARY = (6, int("0xffea00", base=16))
    UNREAL = (7, int("0xff033e", base=16))


@attrs(auto_attribs=True)
class YfuRarity:
    stars: int
    color: YfuColor

    @classmethod
    def from_power_point(cls, power_points):
        if power_points < 500:  # stylog(1) / 2
            return cls(1, YfuColor.COMMON)
        if power_points < 1_000:  # stylog(1)
            return cls(2, YfuColor.UNCOMMON)
        if power_points < 4_000:  # stylog(2)
            return cls(3, YfuColor.RARE)
        if power_points < 16_000:  # stylog(3)
            return cls(4, YfuColor.EPIC)
        if power_points < 64_000:  # stylog(4)
            return cls(5, YfuColor.MYTHIC)
        if power_points < 256_000:  # stylog(5)
            return cls(6, YfuColor.LEGENDARY)
        stars = int(log2(power_points / 1_000)) + 3
        return cls(stars, YfuColor.UNREAL)

    def get_number_of_star(self):
        return self.stars

    def get_color(self):
        return self.color.value[1]


class YfuNotFound(Exception):
    pass


class YfuDict(dict):
    def __missing__(self, key):
        raise YfuNotFound(key)
