from abc import ABCMeta, abstractmethod
from decimal import ROUND_DOWN, Decimal
from enum import Enum
from attr import attrs, attrib
from swag.errors import InvalidStyleValue, InvalidSwagValue

from utils import format_number


@attrs(frozen=True)
class Money(metaclass=ABCMeta):
    @property
    @abstractmethod
    def _CURRENCY(self) -> str:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def from_human_readable(cls, text: str):
        raise NotImplementedError

    def __str__(self) -> str:
        return f"{format_number(self.value)} {self._CURRENCY}"


@attrs(frozen=True)
class Swag(Money):
    value: int = attrib(converter=int)
    _CURRENCY: str = "$wag"

    @classmethod
    def from_human_readable(cls, text: str):
        try:
            return cls(text.replace(" ", ""))
        except ValueError:
            raise InvalidSwagValue

    @value.validator
    def _check_amount(self, attribute, value):
        if value < 0:
            raise InvalidSwagValue

    def __add__(self, other):
        if isinstance(other, Swag):
            return Swag(self.value + other.value)
        else:
            return Swag(self.value + other)

    def __radd__(self, other):
        if isinstance(other, Swag):
            return Swag(self.value + other.value)
        else:
            return Swag(self.value + other)

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
    _CURRENCY: str = "$tyle"

    @classmethod
    def from_human_readable(cls, text: str):
        try:
            return cls(value=text.replace(" ", "").replace(",", "."))
        except ValueError:
            raise InvalidStyleValue

    @value.validator
    def _check_amount(self, attribute, value):
        if value < 0:
            raise InvalidStyleValue

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

    SWAG = Swag._CURRENCY
    STYLE = Style._CURRENCY


def get_money_class(currency_str):
    if currency_str == Swag._CURRENCY:
        return Swag
    elif currency_str == Style._CURRENCY:
        return Style
    else:
        return ValueError
