from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Union

from swag.id import CagnotteId, UserId, YfuId
from swag.assert_timezone import assert_timezone
from swag.yfu import Yfu

if TYPE_CHECKING:
    from ..blockchain import SwagChain

from ..artefacts import SwagAccount

from typing import Dict
from attr import attrs, attrib
import arrow

from swag.cauchy import roll

from ..block import Block

from ..errors import (
    AccountAlreadyExist,
    AlreadyMineToday,
    NotCagnotteManager,
    StyleStillBlocked,
)

from ..currencies import Swag, Style


@attrs(frozen=True, kw_only=True)
class AccountCreation(Block):
    user_id = attrib(type=UserId, converter=UserId)
    timezone = attrib(validator=assert_timezone)

    def validate(self, db: SwagChain):
        if self.user_id in db._accounts:
            raise AccountAlreadyExist

    def execute(self, db: SwagChain):
        db._accounts[self.user_id] = SwagAccount(self.timestamp, self.timezone)


@attrs(frozen=True, kw_only=True)
class AccountDeletion(Block):
    user_id = attrib(type=UserId, converter=UserId)

    def validate(self, db: SwagChain):
        if self.user_id not in db._accounts:
            raise AccountAlreadyExist

    def execute(self, db: SwagChain):
        account = db._accounts.users.pop(self.user_id)
        dev_cagnotte = db._accounts[CagnotteId("€")]

        dev_cagnotte += account.swag_balance
        dev_cagnotte += account.style_balance
        dev_cagnotte += account.blocked_swag
        dev_cagnotte += account.pending_style
        dev_cagnotte.yfu_wallet.update(account.yfu_wallet)


class Uncomputed:
    @classmethod
    def converter(cls, type_converter):
        def cv(input):
            if input is cls:
                return input
            else:
                return type_converter(input)

        return cv


@attrs(frozen=True, kw_only=True)
class Mining(Block):
    user_id = attrib(type=UserId, converter=UserId)
    amount = attrib(type=Swag, default=Uncomputed)
    harvest = attrib(type=Union[dict, None], default=None)

    def execute(self, db: SwagChain):
        user_account = db._accounts[self.user_id]
        bonuses = user_account.bonuses(db)

        if (
            user_account.last_mining_date is not None
            and user_account.last_mining_date.date()
            >= self.timestamp.to(user_account.timezone).date()
        ):
            raise AlreadyMineToday

        if self.amount is Uncomputed:
            rolls = [bonuses.roll() for _ in range(bonuses.minings)]
            self.__dict__["amount"] = Swag(sum([roll["result"] for roll in rolls]))
            self.__dict__["harvest"] = rolls

        user_account.last_mining_date = self.timestamp.to(user_account.timezone)
        user_account += self.__dict__["amount"]


@attrs(frozen=True, kw_only=True)
class Transaction(Block):
    giver_id = attrib(type=Union[UserId, CagnotteId])
    recipient_id = attrib(type=Union[UserId, CagnotteId])
    amount = attrib(type=Union[Swag, Style])

    def execute(self, db: SwagChain):
        if type(self.giver_id) is CagnotteId:
            if self.issuer_id not in db._accounts[self.giver_id].managers:
                raise NotCagnotteManager

        db._accounts[self.giver_id] -= self.amount
        db._accounts[self.recipient_id] += self.amount
        db._accounts[self.recipient_id].register(self.giver_id)


# In days
BLOCKING_TIME = 3


@attrs(frozen=True, kw_only=True)
class SwagBlocking(Block):
    user_id = attrib(type=UserId, converter=UserId)
    amount = attrib(type=Swag)

    def validate(self, db: SwagChain):
        user_account = db._accounts[self.user_id]

        unblocking_date = (
            self.timestamp.to(user_account.timezone)
            .shift(days=BLOCKING_TIME)
            .replace(microsecond=0, second=0, minute=0)
            .to("UTC")
            .datetime
        )

        # If no $tyle was generated yet, reset blockage
        if (
            user_account.unblocking_date != unblocking_date
            and user_account.blocked_swag > Swag(0)
        ):
            raise StyleStillBlocked

    def execute(self, db: SwagChain):
        user_account = db._accounts[self.user_id]

        blocking_date = (
            self.timestamp.to(user_account.timezone)
            .replace(microsecond=0, second=0, minute=0)
            .to("UTC")
        )

        unblocking_date = blocking_date.shift(days=BLOCKING_TIME).to("UTC").datetime
        blocking_date = blocking_date.datetime

        # If no $tyle was generated yet, reset blockage
        if user_account.unblocking_date == unblocking_date:
            user_account += user_account.blocked_swag
            user_account.blocked_swag = Swag(0)
            user_account.unblocking_date = None
            user_account.blocking_date = None

        user_account -= self.amount
        user_account.blocked_swag = self.amount
        user_account.unblocking_date = unblocking_date
        user_account.blocking_date = blocking_date


@attrs(frozen=True, kw_only=True)
class ReturnOnInvestment(Block):
    user_id = attrib(type=UserId, converter=UserId)
    amount = attrib(type=Style)

    def validate(self, db: SwagChain):
        user_account = db._accounts[self.user_id]
        if (
            user_account.unblocking_date is None
            or self.timestamp < user_account.unblocking_date
            or user_account.blocked_swag <= Swag(0)
        ):
            raise StyleStillBlocked

    def execute(self, db: SwagChain):
        user_account = db._accounts[self.user_id]

        user_account += user_account.blocked_swag
        user_account.blocked_swag = Swag(0)

        user_account += self.amount
        user_account.pending_style = Style(0)

        user_account.unblocking_date = None
        user_account.blocking_date = None


@attrs(frozen=True, kw_only=True, eq=False)
class StyleGeneration(Block):
    amounts = attrib(type=Dict[UserId, Style])

    def execute(self, db: SwagChain):
        for user_id, amount in self.amounts.items():
            user_account = db._accounts[user_id]

            user_account.pending_style += amount
