import cbor2
from decimal import Decimal

from .errors import *


class SwagDB:
    def __init__(
        self,
        next_id=0,
        ids={},  # HashMap<Ident, Index>
        users=[],  # Vec<Ident>
        swag_balance=[],  #: Vec<Int>
        swag_last_mining=[],  #: Vec<Date>
        style_balance=[],  #: Vec<Float> // ou Int pour éviter les ennuis ?
        style_rate=[],  #: Vec<Float> // ou Int pour éviter les ennuis ?
        blocked_swag=[],  #: Vec<Int>
        blocking_date=[],  #: Vec<DateTime>
        pending_style=[],
        swag_history=[],  #: Vec<Transaction>
        the_swaggest=None,
    ) -> None:
        self.next_id = next_id
        self.ids = ids

        self.users = users
        self.swag_balance = swag_balance
        self.swag_last_mining = swag_last_mining
        self.style_balance = style_balance
        self.style_rate = style_rate
        self.blocked_swag = blocked_swag
        self.blocking_date = blocking_date
        self.pending_style = pending_style

        self.swag_history = swag_history
        self.the_swaggest = the_swaggest

    @staticmethod
    def load_database(file):
        return SwagDB(**cbor2.loads(open(file, "rb")))

    def save_database(self, file):
        cbor2.dumps(vars(self), open(file, "wb"))

    def add_user(self, user):
        if user not in self.ids:
            self.ids[user] = self.next_id
            self.next_id += 1

            self.users.append(user)
            self.swag_balance.append(0)
            self.swag_last_mining.append(None)
            self.style_balance.append(Decimal(0))
            self.style_rate.append(Decimal(100))
            self.blocked_swag.append(0)
            self.blocking_date.append(None)
            self.pending_style.append(Decimal(0))
        else:
            raise AccountAlreadyExist

    def get_account(self, user):
        try:
            return SwagAccount(self, self.ids[user])
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
    def user(self):
        return self.swagdb.users[self.id]

    @property
    def swag_balance(self):
        return self.swagdb.swag_balance[self.id]

    @swag_balance.setter
    def swag_balance(self, value):
        self.swagdb.swag_balance[self.id] = value

    @property
    def swag_last_mining(self):
        return self.swagdb.swag_last_mining[self.id]

    @swag_last_mining.setter
    def swag_last_mining(self, value):
        self.swagdb.swag_last_mining[self.id] = value

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
    def blocking_date(self):
        return self.swagdb.blocking_date[self.id]

    @blocking_date.setter
    def blocking_date(self, value):
        self.swagdb.blocking_date[self.id] = value

    @property
    def pending_style(self):
        return self.swagdb.pending_style[self.id]

    @pending_style.setter
    def pending_style(self, value):
        self.swagdb.pending_style[self.id] = value


class AccountInfo:
    def __init__(self, account):
        self.id = account.id
        self.user = account.user
        self.swag_balance = account.swag_balance
        self.swag_last_mining = account.swag_last_mining
        self.style_balance = account.style_balance
        self.style_rate = account.style_rate
        self.blocked_swag = account.blocked_swag
        self.blocking_date = account.blocking_date
        self.pending_style = account.pending_style
