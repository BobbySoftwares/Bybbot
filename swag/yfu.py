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
    power: Power
    last_activation_date: Arrow = attrib(default=Arrow.min)

    is_baptized: bool = attrib(default=False)

    def activate(self, db, targets, activation_date):
        self.power._activation(db, self.owner_id, targets)
        self.last_activation_date = activation_date


class YfuRarity(Enum):
    COMMON = (1, int("0xffffff", base=16))
    UNCOMMON = (2, int("0x1eff00", base=16))
    RARE = (3, int("0x0070dd", base=16))
    EPIC = (4, int("0xa335ee", base=16))
    MYTHIC = (5, int("0xff8000", base=16))
    LEGENDARY = (6, int("0xffea00", base=16))
    UNREAL = (7, int("0xff033e", base=16))

    @classmethod
    def from_power_point(cls, power_point):
        if power_point < 500:  # stylog(1) / 2
            return cls.COMMON
        if power_point < 1000:  # stylog(1)
            return cls.UNCOMMON
        if power_point < 4000:  # stylog(2)
            return cls.RARE
        if power_point < 16000:  # stylog(3)
            return cls.EPIC
        if power_point < 64000:  # stylog(4)
            return cls.MYTHIC
        if power_point < 256000:  # stylog(5)
            return cls.LEGENDARY
        return cls.UNREAL

    def get_number_of_star(self):
        return self.value[0]

    def get_color(self):
        return self.value[1]


class YfuNotFound(Exception):
    pass


class YfuDict(dict):
    def __missing__(self, key):
        raise YfuNotFound(key)
