from typing import Dict, List, Set, Union
from attr import Factory, attrs

from swag.id import UserId

from ..errors import (
    InvalidStyleValue,
    InvalidSwagValue,
    NoCagnotteRegistered,
    NotEnoughStyleInBalance,
    NotEnoughSwagInBalance,
)
from ..currencies import Money, Style, Swag


@attrs(auto_attribs=True)
class Cagnotte:
    name: str
    managers: List[UserId]
    participants: Set[UserId] = Factory(set)
    swag_balance: Swag = Swag(0)
    style_balance: Style = Style(0)

    def __iadd__(self, value: Union[Swag, Style]):
        if type(value) is Swag:
            self.swag_balance += value
        elif type(value) is Style:
            self.style_balance += value
        else:
            raise TypeError(
                "Amounts added to SwagAccount should be either Swag or Style."
            )
        return self

    def __isub__(self, value: Union[Swag, Style]):
        try:
            if type(value) is Swag:
                self.swag_balance -= value
            elif type(value) is Style:
                self.style_balance -= value
            else:
                raise TypeError(
                    "Amounts subtracted to SwagAccount should be either Swag or Style."
                )
        except InvalidSwagValue:
            raise NotEnoughSwagInBalance(self.swag_balance)
        except InvalidStyleValue:
            raise NotEnoughStyleInBalance(self.style_balance)
        return self

    @property
    def is_empty(self):
        return self.swag_balance == Swag(0) and self.style_balance == Style(0)

    def register(self, participant: UserId):
        self.participants.add(participant)


@attrs(frozen=True)
class CagnotteInfo(Cagnotte):
    @classmethod
    def from_cagnotte(cls, account):
        return cls(**vars(account))


class CagnotteDict(dict):
    def __missing__(self, key):
        raise NoCagnotteRegistered(key)
