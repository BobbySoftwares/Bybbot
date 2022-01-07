from decimal import Decimal
from typing import Dict, Optional, Union, List, Set
from attr import Factory, attrs, attrib
import arrow
from arrow import Arrow
from itertools import chain

from swag.id import CagnotteId, UserId

from ..errors import (
    InvalidStyleValue,
    InvalidSwagValue,
    InvalidTimeZone,
    NoSwagAccountRegistered,
    NoCagnotteAccountRegistered,
    NotEnoughStyleInBalance,
    NotEnoughSwagInBalance,
)
from ..currencies import Money, Swag, Style


def assert_timezone(self, attribute, timezone):
    try:
        arrow.now(timezone)
    except arrow.parser.ParserError:
        raise InvalidTimeZone(timezone)


@attrs(auto_attribs=True)
class Account:
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

    def register(self, _):
        pass

@attrs(frozen=True)
class AccountInfo(Account):
    @classmethod
    def get_info(cls, account):
        return cls(**vars(account))


#------------------------------------#
# Classes pour les comptes Cagnottes #
#------------------------------------#

@attrs(auto_attribs=True)
class SwagAccount(Account):
    creation_date: Arrow
    timezone: str = attrib(validator=assert_timezone)
    last_mining_date: Optional[Arrow] = None
    style_rate: Decimal = Decimal(100)
    blocked_swag: Swag = Swag(0)
    unblocking_date: Optional[Arrow] = None
    pending_style: Style = Style(0)
    timezone_lock_date: Optional[Arrow] = None

@attrs(frozen=True)
class SwagAccountInfo(AccountInfo,SwagAccount):
    pass

class SwagAccountDict(dict):
    def __missing__(self, key):
        raise NoSwagAccountRegistered(key)


#------------------------------------#
# Classes pour les comptes Cagnottes #
#------------------------------------#

@attrs(auto_attribs=True)
class CagnotteAccount:
    name: str
    managers: List[UserId]
    participants: Set[UserId] = Factory(set)

    def register(self, participant: UserId):
        self.participants.add(participant)

@attrs(frozen=True)
class CagnotteAccountInfo(AccountInfo,CagnotteAccount):
    pass

class CagnotteAccountDict(dict):
    def __missing__(self, key):
        raise NoCagnotteAccountRegistered(key)

#------------------------------------#
# Classe de l'ensemble des comptes   #
#------------------------------------#

@attrs(auto_attribs=True)
class Accounts:
    users: Dict[UserId, SwagAccount] = attrib(init=False, factory=SwagAccountDict)
    cagnottes: Dict[CagnotteId, CagnotteAccount] = attrib(init=False, factory=CagnotteAccountDict)

    def __setitem__(self, key, item):
        if type(key) is UserId:
            self.users[key] = item
        elif type(key) is CagnotteId:
            self.cagnottes[key] = item
        else:
            raise KeyError("Account ID should be of type UserId or CagnotteId")

    def __getitem__(self, key):
        if type(key) is UserId:
            return self.users[key]
        elif type(key) is CagnotteId:
            return self.cagnottes[key]
        else:
            raise KeyError("Account ID should be of type UserId or CagnotteId")

    def __delitem__(self, key):
        if type(key) is UserId:
            del self.users[key]
        elif type(key) is CagnotteId:
            del self.cagnottes[key]
        else:
            raise KeyError("Account ID should be of type UserId or CagnotteId")

    def __contains__(self, key):
        return (type(key) is UserId and key in self.users) or (
            type(key) is CagnotteId and key in self.cagnottes
        )

    def __iter__(self):
        return chain(self.users.__iter__(), self.cagnottes.__iter__())

    def items(self):
        return chain(self.users.items(), self.cagnottes.items())

    def values(self):
        return chain(self.users.values(), self.cagnottes.values())
