import cbor2
from decimal import Decimal
from arrow import utcnow
from os import remove

from .errors import *


class SwagDB:
    def __init__(
        self,
        next_id=0,
        id={},
        discord_id=[],
        swag_balance=[],
        last_mining_date=[],
        style_balance=[],
        style_rate=[],
        blocked_swag=[],
        unblocking_date=[],
        pending_style=[],
        timezone=[],
        timezone_lock_date=[],
        creation_date=[],
        blockchain=[],
        guild_timezone={},
    ) -> None:
        self.next_id = next_id

        self.id = id

        self.discord_id = discord_id
        self.swag_balance = swag_balance
        self.last_mining_date = last_mining_date
        self.style_balance = style_balance
        self.style_rate = style_rate
        self.blocked_swag = blocked_swag
        self.unblocking_date = unblocking_date
        self.pending_style = pending_style
        self.timezone = timezone
        self.timezone_lock_date = timezone_lock_date
        self.creation_date = creation_date

        self.blockchain = blockchain
        self.guild_timezone = guild_timezone

    @staticmethod
    def load_database(file):
        with open(file, "rb") as file:
            return SwagDB(**cbor2.load(file))

    def save_database(self, file):
        try:
            with open(file, "wb") as file:
                cbor2.dump(vars(self), file)
        except:
            try:
                remove(file)
            except FileNotFoundError:
                pass
            raise

    def add_user(self, user, guild):
        if user not in self.id:
            self.id[user] = self.next_id
            self.next_id += 1

            self.discord_id.append(user)
            self.swag_balance.append(0)
            self.last_mining_date.append(None)
            self.style_balance.append(Decimal(0))
            self.style_rate.append(Decimal(100))
            self.blocked_swag.append(0)
            self.unblocking_date.append(None)
            self.pending_style.append(Decimal(0))
            if guild in self.guild_timezone:
                self.timezone.append(self.guild_timezone[guild])
            else:
                self.timezone.append("UTC")
            t = utcnow().datetime
            self.creation_date.append(t)
            self.timezone_lock_date.append(t)

            return self.next_id - 1, t
        else:
            raise AccountAlreadyExist

    def get_account(self, user):
        try:
            return SwagAccount(self, self.id[user])
        except KeyError:
            raise NoAccountRegistered(user)

    def get_account_from_index(self, idx):
        return SwagAccount(self, idx)

    def get_accounts(self):
        return (SwagAccount(self, idx) for idx in range(self.user_number()))

    def get_account_infos(self):
        return (AccountInfo(account) for account in self.get_accounts())

    def user_number(self):
        return self.next_id


class SwagAccount:
    def __init__(self, swagdb, id) -> None:
        self.swagdb = swagdb
        self.id = id

    def get_info(self):
        return AccountInfo(self)

    @property
    def discord_id(self):
        return self.swagdb.discord_id[self.id]

    @property
    def swag_balance(self):
        return self.swagdb.swag_balance[self.id]

    @swag_balance.setter
    def swag_balance(self, value):
        self.swagdb.swag_balance[self.id] = value

    @property
    def last_mining_date(self):
        return self.swagdb.last_mining_date[self.id]

    @last_mining_date.setter
    def last_mining_date(self, value):
        self.swagdb.last_mining_date[self.id] = value

    @property
    def style_balance(self):
        return self.swagdb.style_balance[self.id]

    @style_balance.setter
    def style_balance(self, value):
        self.swagdb.style_balance[self.id] = value

    @property
    def style_rate(self):
        return self.swagdb.style_rate[self.id]

    @style_rate.setter
    def style_rate(self, value):
        self.swagdb.style_rate[self.id] = value

    @property
    def blocked_swag(self):
        return self.swagdb.blocked_swag[self.id]

    @blocked_swag.setter
    def blocked_swag(self, value):
        self.swagdb.blocked_swag[self.id] = value

    @property
    def unblocking_date(self):
        return self.swagdb.unblocking_date[self.id]

    @unblocking_date.setter
    def unblocking_date(self, value):
        self.swagdb.unblocking_date[self.id] = value

    @property
    def pending_style(self):
        return self.swagdb.pending_style[self.id]

    @pending_style.setter
    def pending_style(self, value):
        self.swagdb.pending_style[self.id] = value

    @property
    def timezone(self):
        return self.swagdb.timezone[self.id]

    @timezone.setter
    def timezone(self, value):
        self.swagdb.timezone[self.id] = value

    @property
    def timezone_lock_date(self):
        return self.swagdb.timezone_lock_date[self.id]

    @timezone_lock_date.setter
    def timezone_lock_date(self, value):
        self.swagdb.timezone_lock_date[self.id] = value

    @property
    def creation_date(self):
        return self.swagdb.creation_date[self.id]

    @creation_date.setter
    def creation_date(self, value):
        self.swagdb.creation_date[self.id] = value


class AccountInfo:
    def __init__(self, account):
        self.id = account.id
        self.discord_id = account.discord_id
        self.swag_balance = account.swag_balance
        self.last_mining_date = account.last_mining_date
        self.style_balance = account.style_balance
        self.style_rate = account.style_rate
        self.blocked_swag = account.blocked_swag
        self.unblocking_date = account.unblocking_date
        self.pending_style = account.pending_style
        self.timezone = account.timezone
        self.timezone_lock_date = account.timezone_lock_date
        self.creation_date = account.creation_date
