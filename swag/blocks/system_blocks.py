from __future__ import annotations

from typing import TYPE_CHECKING, Union

from swag.id import UserId
from swag.utils import assert_timezone

if TYPE_CHECKING:
    from ..blockchain import SwagChain

from attr import attrs, attrib
import arrow


from ..block import Block

from ..errors import (
    InvalidTimeZone,
    TimeZoneFieldLocked,
)

from ..currencies import Swag, Style


@attrs(frozen=True, kw_only=True)
class UserTimezoneUpdate(Block):
    user_id = attrib(type=UserId, converter=UserId)
    timezone = attrib(validator=assert_timezone)

    def execute(self, db: SwagChain):
        user_account = db._accounts[self.user_id]

        if (
            user_account.timezone_lock_date is not None
            and self.timestamp <= user_account.timezone_lock_date
        ):
            raise TimeZoneFieldLocked(user_account.timezone_lock_date)

        user_account.timezone_lock_date = self.lock_date.datetime
        user_account.timezone = self.timezone

    @property
    def lock_date(self):
        return self.timestamp.shift(days=1)


@attrs(frozen=True, kw_only=True)
class GuildTimezoneUpdate(Block):
    guild_id = attrib(type=int)
    timezone = attrib(validator=assert_timezone)

    def execute(self, db: SwagChain):
        db._guilds[self.guild_id].timezone = self.timezone


@attrs(frozen=True, kw_only=True)
class GuildSystemChannelUpdate(Block):
    guild_id = attrib(type=int)
    channel_id = attrib(type=int)

    def execute(self, db: SwagChain):
        db._guilds[self.guild_id].system_channel_id = self.channel_id


@attrs(frozen=True, kw_only=True)
class GuildForbesChannelUpdate(Block):
    guild_id = attrib(type=int)
    channel_id = attrib(type=int)

    def execute(self, db: SwagChain):
        db._guilds[self.guild_id].forbes_channel_id = self.channel_id


@attrs(frozen=True, kw_only=True)
class EventGiveaway(Block):
    user_id = attrib(type=UserId, converter=UserId)
    amount = attrib(type=Union[Swag, Style])

    def execute(self, db: SwagChain):
        user_account = db._accounts[self.user_id]

        user_account += self.amount
