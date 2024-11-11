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
        avantage_rolls = [self.unit_roll() for _ in range(self.avantage)]

        return {
            "result": self.multiplier * max(avantage_rolls),
            "details": {"multiplier": self.multiplier, "avantages": avantage_rolls},
        }

    def unit_roll(self):
        return roll(self.base, self.luck)

    def __str__(self) -> str:
        result = ""
        if self.base != 0:
            result += f"- $wagBase : {self.base}\n"
        if self.luck != 0:
            result += f"- $wagLuck : {self.luck}\n"
        if self.minings != 0:
            result += f"- Nombre de minage : {self.minings}\n"
        if self.avantage != 0:
            result += f"- Avantage au minage : {self.avantage}\n"
        if self.multiplier != 0:
            result += f"- Multiplicateur de minage : x{self.multiplier}\n"
        if self.blocking_bonus != 0:
            result += f"- Bonus de blocage : {self.blocking_bonus}%\n"
        if self.lottery_luck != 0:
            result += f"- Lottery Luck : {self.lottery_luck}"
        return result
