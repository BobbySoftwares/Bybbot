from decimal import ROUND_DOWN, Decimal
from attr import attrs, attrib
from swag.errors import InvalidStyleValue, InvalidSwagValue

from utils import format_number


@attrs(frozen=True)
class Money:
    @property
    def currency(self):
        raise NotImplementedError

    def __str__(self) -> str:
        return f"{format_number(self.value)} {self.currency}"


@attrs(frozen=True)
class Swag(Money):
    value: int = attrib(converter=int)

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
