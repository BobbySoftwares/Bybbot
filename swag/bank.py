from datetime import date, datetime, timedelta
from enum import Enum, auto
from decimal import Decimal
from numpy import log1p

from .cauchy import roll

from .errors import *

from .db import SwagDB, SwagAccount


SWAG_BASE = 1000
SWAG_LUCK = 100000

TIME_OF_BLOCK = 3  # en jours

STYLA = 1.9712167541353567
STYLB = 6.608024397705518e-07


def stylog(swag):
    return STYLA * log1p(STYLB * swag)


class SwagBank:
    def __init__(
        self,
        db_path,
    ) -> None:
        self.db_path = db_path
        try:
            self.swagdb = SwagDB.load_database(db_path)
        except (IOError, OSError):
            self.swagdb = SwagDB()

    def add_user(self, user):
        self.swagdb.add_user(user)

    def get_balance_of(self, user):
        return self.swagdb.get_account(user).swag_balance

    def mine(self, user):
        user_account = self.swagdb.get_account(user)

        # On ne peut miner qu'une fois par jour
        if user_account.swag_last_mining == date.today():
            raise AlreadyMineToday

        # Génération d'un nombre aléatoire, en suivant une loi de Cauchy
        mining_booty = roll(SWAG_BASE, SWAG_LUCK)
        # Ajout de cet argent au compte
        user_account.swag_balance += mining_booty
        # Mise à jour de la date du dernier minage
        user_account.swag_last_mining = date.today()
        # écriture dans l'historique
        self.swagdb.blockchain.append(("$wag Mine ⛏", user, mining_booty))

        return mining_booty

    def swag_transaction(self, giver, recipient, amount):
        giver_account = self.swagdb.get_account(giver)
        recipient_account = self.swagdb.get_account(recipient)

        # Check if the valueIsNotNegative or not int
        if amount < 0 or not isinstance(amount, int):
            raise InvalidSwagValue

        # Check if the expeditor have enough money:
        if giver_account.swag_balance < amount:
            raise NotEnoughSwagInBalance(giver)

        # Make the transaction:
        giver_account.swag_balance -= amount
        recipient_account.swag_balance += amount

        # Write transaction in history
        self.swagdb.blockchain.append((giver, recipient, amount, "$wag"))

    def get_account_info(self, user):
        return self.swagdb.get_account(user).get_info()

    def style_transaction(self, giver, recipient, amount):
        giver_account = self.swagdb.get_account(giver)
        recipient_account = self.swagdb.get_account(recipient)

        # Check if the valueIsNotNegative or not int
        if amount < 0 or not isinstance(amount, (int, float, Decimal)):
            raise InvalidStyleValue

        # Check if the expeditor have enough money:
        if giver_account.style_balance < amount:
            raise NotEnoughStyleInBalance(giver)

        # Make the transaction:
        giver_account.style_balance -= amount
        recipient_account.style_balance += amount

        # Write transaction in history
        self.swagdb.blockchain.append((giver, recipient, amount, "$tyle"))

    def block_swag(self, user, amount):
        user_account = self.swagdb.get_account(user)

        # Check if the valueIsNotNegative or not int
        if amount < 0 or not isinstance(amount, int):
            raise InvalidSwagValue

        # Check if the account have enough money:
        if user_account.swag_balance < amount:
            raise NotEnoughSwagInBalance(user)

        # Check if there is already swag blocked
        if user_account.blocked_swag > 0:
            raise StyleStillBlocked

        user_account.swag_balance -= amount
        user_account.blocked_swag = amount
        self.swagdb.blockchain.append((user, "$tyle Generator Inc.", amount, "$wag"))

    def get_user_list(self):
        return self.swagdb.ids.keys()

    def get_forbes(self):
        return sorted(
            self.swagdb.get_account_infos(),
            key=lambda item: item.swag_balance,
            reverse=True,
        )

    def get_the_new_swaggest(self):
        for user in self.get_forbes():
            return user.id

    def update_bonus_growth_rate(self):
        forbes = sorted(
            self.swagdb.get_accounts(),
            key=lambda item: item.swag_balance,
            reverse=False,
        )

        # Fonction mathématique, qui permet au premier d'avoir toujours
        # 50%, et à celui à la moitié du classement 10%
        def rate(rank):
            return round((10 / 3) * (pow(16, rank / self.swagdb.user_number()) - 1), 2)

        for rank, user_account in enumerate(forbes):
            user_account.style_rate = rate(rank)

    def earn_style(self):
        for user_account in self.swagdb.get_accounts():
            block_booty = (
                stylog(user_account.blocked_swag)
                * (user_account.style_rate * 0.01)
                / (TIME_OF_BLOCK * 24)
            )

            user_account.pending_style += block_booty

    def unblock_swag(self, user):
        user_account = self.swagdb.get_account(user)

        if datetime.now() < user_account.unblocking_date:
            raise StyleStillBlocked

        returned_swag = user_account.blocked_swag

        user_account.swag_balance += returned_swag
        user_account.blocked_swag = 0
        self.swagdb.blockchain.append(
            (
                "$tyle Generator Inc.",
                user,
                returned_swag,
                "$wag",
            )
        )

    def get_history(self, user):
        id = self.swagdb.get_account(user).id
        return [
            transaction
            for transaction in self.swagdb.blockchain
            if concerns_user(id, transaction)
        ]


def concerns_user(id, transaction):
    pass
