from decimal import Decimal
from attr import attrs
from swag.cauchy import roll


SWAG_BASE = 1000
SWAG_LUCK = 100000


@attrs(auto_attribs=True)
class Bonuses:
    avantage: int = 1
    minings: int = 1
    base: int = SWAG_BASE
    luck: int = SWAG_LUCK
    multiplier: Decimal = Decimal(1)
    lottery_luck: int = 1
    blocking_bonus: Decimal = Decimal(0)

    def roll(self):
        return self.multiplier * max(
            roll(self.base, self.luck) for _ in range(self.avantage)
        )
