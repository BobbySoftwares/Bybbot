from decimal import Decimal
from typing import Any, Dict, Optional, Union, List, Set
from attr import Factory, attrs, attrib
import arrow
from arrow import Arrow
from itertools import chain
from swag.artefacts.bonuses import Bonuses
from swag.cauchy import roll

from swag.id import CagnotteId, UserId, YfuId
from swag.powers.power import Passive
from swag.utils import assert_timezone
from swag.yfu import Yfu

from ..errors import (
    AlreadyMineToday,
    InvalidStyleValue,
    InvalidSwagValue,
    InvalidTimeZone,
    NoSwagAccountRegistered,
    NoCagnotteAccountRegistered,
    NotEnoughStyleInBalance,
    NotEnoughSwagInBalance,
)
from ..currencies import Money, Swag, Style


class Info:
    def __init__(self, orig) -> None:
        self.__dict__ = orig.__dict__

        def setattr(self, __name: str, __value: Any) -> None:
            raise AttributeError

        def delattr(self, __name: str) -> None:
            raise AttributeError

        self.__setattr__ = setattr
        self.__delattr__ = delattr


@attrs(auto_attribs=True)
class Account:
    swag_balance: Swag = attrib(init=False, default=Swag(0))
    style_balance: Style = attrib(init=False, default=Style(0))
    yfu_wallet: Set[YfuId] = attrib(init=False, factory=set)

    def __iadd__(self, value: Union[Swag, Style]):
        if type(value) is Swag:
            self.swag_balance += value
        elif type(value) is Style:
            self.style_balance += value
        else:
            raise TypeError(
                "Amounts added to SwagAccount should be either Swag, Style."
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
                    "Amounts subtracted to SwagAccount should be either Swag, Style."
                )
        except InvalidSwagValue:
            raise NotEnoughSwagInBalance(self.swag_balance)
        except InvalidStyleValue:
            raise NotEnoughStyleInBalance(self.style_balance)
        return self

    def register(self, _):
        pass

    @property
    def is_empty(self):
        return self.swag_balance == Swag(0) and self.style_balance == Style(0)

    def check_immunity(self, power):
        # cost = Style("inf")
        # for yfu_id in self.yfu_wallet:
        #     cost = min(cost, chain._yfus[yfu_id].power.protection_cost(power))
        # try:
        #     self -= cost
        #     raise NotImplementedError
        # except NotEnoughStyleInBalance:
        #     pass
        
        # TODO
        pass

    def mine(self, chain):
        return self.bonuses(chain).roll()

    def bonuses(self, chain, **kwargs):
        bonuses = Bonuses(**kwargs)
        for yfu_id in self.yfu_wallet:
            if issubclass(type(chain._yfus[yfu_id].power), Passive):
                chain._yfus[yfu_id].power.add_bonus(bonuses)
        
        return bonuses


# ------------------------------------#
# Classes pour les comptes Cagnottes #
# ------------------------------------#


@attrs(auto_attribs=True)
class SwagAccount(Account):
    creation_date: Arrow
    timezone: str = attrib(validator=assert_timezone)
    last_mining_date: Optional[Arrow] = None
    style_rate: Decimal = Decimal(100)
    blocked_swag: Swag = Swag(0)
    blocking_date : Optional[Arrow] = None
    unblocking_date: Optional[Arrow] = None
    pending_style: Style = Style(0)
    timezone_lock_date: Optional[Arrow] = None


class SwagAccountDict(dict):
    def __missing__(self, key):
        raise NoSwagAccountRegistered(key)


# ------------------------------------#
# Classes pour les comptes Cagnottes #
# ------------------------------------#


@attrs(auto_attribs=True)
class CagnotteAccount(Account):
    name: str
    managers: List[UserId]
    participants: Set[UserId] = Factory(set)

    def register(self, participant: UserId):
        self.participants.add(participant)


class CagnotteAccountDict(dict):
    def __missing__(self, key):
        raise NoCagnotteAccountRegistered(key)


# ------------------------------------#
# Classe de l'ensemble des comptes   #
# ------------------------------------#


@attrs(auto_attribs=True)
class Accounts:
    users: Dict[UserId, SwagAccount] = attrib(init=False, factory=SwagAccountDict)
    cagnottes: Dict[CagnotteId, CagnotteAccount] = attrib(
        init=False, factory=CagnotteAccountDict
    )

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
