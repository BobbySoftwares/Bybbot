from decimal import ROUND_DOWN, Decimal
from enum import Enum
from attr import attrs, attrib
from swag.errors import InvalidStyleValue, InvalidSwagValue

from utils import format_number


@attrs(frozen=True)
class Money:
    @property
    def currency(self):
        raise NotImplementedError

    @classmethod
    def from_str(cls, text : str):
        raise NotImplementedError

    def __str__(self) -> str:
        return f"{format_number(self.value)} {self.currency}"


@attrs(frozen=True)
class Swag(Money):
    value: int = attrib(converter=int)

    @classmethod
    def from_command(cls, text : str):
        try:
            return cls(text.replace(" ",""))
        except ValueError:
            raise InvalidSwagValue

    @value.validator
    def _check_amount(self, attribute, value):
        if value < 0:
            raise InvalidSwagValue

    @property
    def currency(self):
        return "$wag"

    def __add__(self, other: "Swag"):
        return Swag(self.value + other.value)

    def __sub__(self, other: "Swag"):
        return Swag(self.value - other.value)

    def __pos__(self):
        return self

    def __neg__(self):
        if self.value == 0:
            return self
        else:
            raise InvalidSwagValue

    def __int__(self):
        return self.value


def style_decimal(amount):
    if type(amount) is Style:
        return amount.value
    else:
        return Decimal(amount).quantize(Decimal(".0001"), rounding=ROUND_DOWN)


@attrs(frozen=True)
class Style(Money):
    value: Decimal = attrib(converter=style_decimal)

    @classmethod
    def from_command(cls, text : str):
        try:
            return cls(value=text.replace(" ","").replace(",","."))
        except ValueError:
            raise InvalidStyleValue

    @value.validator
    def _check_amount(self, attribute, value):
        if value < 0:
            raise InvalidStyleValue

    @property
    def currency(self):
        return "$tyle"

    def __add__(self, other: "Style"):
        return Style(self.value + other.value)

    def __sub__(self, other: "Style"):
        return Style(self.value - other.value)

    def __mul__(self, other: Decimal):
        return Style(self.value * other)

    __rmul__ = __mul__

    def __pos__(self):
        return self

    def __neg__(self):
        if self.value == 0:
            return self
        else:
            raise InvalidStyleValue


class Currency(str, Enum): 
    """
    Only used by slash command, 
    Could be automaticly built thanks to Money children I guess ?
    """

    Swag = Swag(0).currency
    Style = Style(0).currency

    @classmethod
    def get_class(cls,currency_str):
        if currency_str == cls.Swag:
            return Swag
        elif currency_str == cls.Style:
            return Style
        else:
            return ValueError
