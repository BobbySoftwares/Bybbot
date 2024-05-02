from decimal import Decimal
from math import sqrt
from typing import Union
from arrow.arrow import Arrow
import disnake
from numpy import log2

from attr import attrib, attrs
from enum import Enum
from swag.currencies import Style
from swag.id import CagnotteId, UserId, YfuId
from swag.stylog import stylog
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

    power_points: int  # Power point initiaux
    initial_activation_cost: Style  # ne sert plus, mais on doit le laisser pour une raison de compatibilite :)
    power: Power
    last_activation_date: Arrow = attrib(default=Arrow.min)

    is_baptized: bool = attrib(default=False)
    experience: int = attrib(default=0)

    @property
    def cost(self):
        return max(
            Style("0.002"),
            Style(4 * self.dampening * sqrt(self.power_point_effective / 100)),
        ) * Style(self.power.cost_factor)

    @property
    def power_point_effective(self):
        return int(
            self.power_points
            * (1 + stylog(self.experience / self.power_points * 1_000_000))
        )

    @property
    def dampening(self):

        # le dampening est initialement calculé à la generation de Yfu
        # cependant, celui ci n'est pas enregistré lors de la création de la Yfu (c'est dommage!)
        # on peut le recalculer en regardant la proportion des pp de la yfu et du pouvoir

        return (
            self.power.power_points / self.power_point_effective
        ) * self.power._correct_dampening()

    def activate(self, db, targets, activation_date):
        self.power._activation(db, self.owner_id, targets)
        self.last_activation_date = activation_date

    def upgrade(self, experience_received):
        # enregistrement du dampening avant l'ajout de l'experience
        actual_dampening = self.dampening
        self.experience += experience_received  # Ajout de l'experience

        # update des pp du pouvoir, avec le même dampening que precedement
        self.power.power_points = self.power_point_effective * actual_dampening


class YfuColor(Enum):
    DISAPPOINTING = (0, int("0xad97c0", base=16))
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
        if power_points < 50:
            return cls(0, YfuColor.DISAPPOINTING)
        if power_points < 250:
            return cls(1, YfuColor.COMMON)
        if power_points < 1_000:
            return cls(2, YfuColor.UNCOMMON)
        if power_points < 4_000:
            return cls(3, YfuColor.RARE)
        if power_points < 16_000:
            return cls(4, YfuColor.EPIC)
        if power_points < 64_000:
            return cls(5, YfuColor.MYTHIC)
        if power_points < 256_000:
            return cls(6, YfuColor.LEGENDARY)
        stars = int(log2(power_points / 1_000)) + 3
        return cls(stars, YfuColor.UNREAL)

    @classmethod
    def from_yfu(cls, yfu: Yfu):
        return cls.from_power_point(yfu.power_point_effective)

    def get_number_of_star(self):
        return self.stars

    def get_color(self):
        return self.color.value[1]


class YfuNotFound(Exception):
    pass


class YfuDict(dict):
    def __missing__(self, key):
        raise YfuNotFound(key)
