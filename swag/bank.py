from arrow.parser import ParserError
from arrow import now, utcnow
from decimal import Decimal, ROUND_UP
from numpy import log1p
from shutil import move
from cbor2 import CBORDecodeEOF

from .cauchy import roll
from .errors import *
from .db import SwagDB
from .transactions import TransactionType, concerns_user

SWAG_BASE = 1000
SWAG_LUCK = 100000

# In days
BLOCKING_TIME = 3

STYLA = 1.9712167541353567
STYLB = 6.608024397705518e-07


def stylog(swag):
    return Decimal(STYLA * log1p(STYLB * swag))


class SwagBank:
    def __init__(
        self,
        db_path,
    ) -> None:
        self.db_path = db_path
        try:
            self.swagdb = SwagDB.load_database(db_path)
        except (CBORDecodeEOF, FileNotFoundError):
            try:
                self.swagdb = SwagDB.load_database(f"{db_path}.bk")
            except (CBORDecodeEOF, FileNotFoundError):
                try:
                    self.swagdb = SwagDB.load_database(f"{db_path}.bk.bk")
                except FileNotFoundError:
                    self.swagdb = SwagDB()

    def add_user(self, user, guild):
        id, t = self.swagdb.add_user(user, guild)
        self.swagdb.blockchain.append((t, TransactionType.CREATION, id))
        self.transactional_save()

    def transactional_save(self):
        try:
            move(f"{self.db_path}.bk", f"{self.db_path}.bk.bk")
        except FileNotFoundError:
            pass
        try:
            move(self.db_path, f"{self.db_path}.bk")
        except FileNotFoundError:
            pass
        self.swagdb.save_database(self.db_path)

    def mine(self, user):
        user_account = self.swagdb.get_account(user)

        t = now(user_account.timezone).datetime
        # On ne peut miner qu'une fois par jour
        if (
            user_account.last_mining_date is not None
            and user_account.last_mining_date.date() >= t.date()
        ):
            raise AlreadyMineToday

        # Génération d'un nombre aléatoire, en suivant une loi de Cauchy
        mining_booty = roll(SWAG_BASE, SWAG_LUCK)
        # Ajout de cet argent au compte
        user_account.swag_balance += mining_booty
        # Mise à jour de la date du dernier minage
        user_account.last_mining_date = t
        # écriture dans l'historique
        self.swagdb.blockchain.append(
            (utcnow().datetime, TransactionType.MINE, (user_account.id, mining_booty))
        )

        self.transactional_save()

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
        self.swagdb.blockchain.append(
            (
                utcnow().datetime,
                TransactionType.SWAG,
                (giver_account.id, recipient_account.id, amount),
            )
        )

        self.transactional_save()

    def get_account_info(self, user):
        return self.swagdb.get_account(user).get_info()

    def style_transaction(self, giver, recipient, amount):
        giver_account = self.swagdb.get_account(giver)
        recipient_account = self.swagdb.get_account(recipient)

        # Check if the valueIsNotNegative or not int
        if amount < 0 or not isinstance(amount, Decimal):
            raise InvalidStyleValue

        # Check if the expeditor have enough money:
        if giver_account.style_balance < amount:
            raise NotEnoughStyleInBalance(giver)

        # Make the transaction:
        giver_account.style_balance -= amount
        recipient_account.style_balance += amount

        # Write transaction in history
        self.swagdb.blockchain.append(
            (
                utcnow().datetime,
                TransactionType.STYLE,
                (giver_account.id, recipient_account.id, amount),
            )
        )

        self.transactional_save()

    def block_swag(self, user, amount):
        user_account = self.swagdb.get_account(user)

        t = now(user_account.timezone)

        unblocking_date = (
            t.shift(days=BLOCKING_TIME)
            .replace(microsecond=0, second=0, minute=0)
            .to("UTC")
            .datetime
        )

        # If no $tyle was generated yet, reset blockage
        if user_account.unblocking_date == unblocking_date:
            user_account.swag_balance += user_account.blocked_swag
            user_account.blocked_swag = 0
            user_account.unblocking_date = None
            self.swagdb.blockchain.append(
                (
                    t.to("UTC").datetime,
                    TransactionType.RELEASE,
                    (user_account.id, amount),
                )
            )

        # Check if the valueIsNotNegative or not int
        if amount <= 0 or not isinstance(amount, int):
            raise InvalidSwagValue

        # Check if the account have enough money:
        if user_account.swag_balance < amount:
            raise NotEnoughSwagInBalance(user)

        # Check if there is already swag blocked
        if user_account.blocked_swag > 0:
            raise StyleStillBlocked

        user_account.swag_balance -= amount
        user_account.blocked_swag = amount
        user_account.unblocking_date = unblocking_date
        self.swagdb.blockchain.append(
            (t.to("UTC").datetime, TransactionType.BLOCK, (user_account.id, amount))
        )

        self.transactional_save()

    def get_forbes(self):
        return sorted(
            self.swagdb.get_account_infos(),
            key=lambda item: item.swag_balance,
            reverse=True,
        )

    def get_the_new_swaggest(self):
        for user in self.get_forbes():
            return user.discord_id

    def update_bonus_growth_rate(self):
        forbes = sorted(
            self.swagdb.get_accounts(),
            key=lambda item: item.swag_balance,
            reverse=True,
        )

        # Fonction mathématique, qui permet au premier d'avoir toujours
        # 50%, et à celui à la moitié du classement 10%
        N = self.swagdb.user_number()

        def rate(rank):
            return Decimal(100 + 10 / 3 * (pow(16, 1 - rank / N) - 1)).quantize(
                Decimal(".01"), rounding=ROUND_UP
            )

        for rank, user_account in enumerate(forbes):
            user_account.style_rate = rate(rank)

        self.transactional_save()

    def earn_style(self):
        for user_account in self.swagdb.get_accounts():
            block_booty = (
                stylog(user_account.blocked_swag)
                * user_account.style_rate
                / 100
                / (BLOCKING_TIME * 24)
            ).quantize(Decimal(".0001"), rounding=ROUND_UP)

            user_account.pending_style += block_booty

        self.transactional_save()

    def swag_unblocker(self):
        for user_account in self.swagdb.get_accounts():
            if (
                user_account.unblocking_date is not None
                and user_account.unblocking_date <= now()
                and 0 < user_account.blocked_swag
            ):
                returned_swag = user_account.blocked_swag

                user_account.swag_balance += returned_swag
                user_account.blocked_swag = 0
                self.swagdb.blockchain.append(
                    (
                        utcnow().datetime,
                        TransactionType.RELEASE,
                        (
                            user_account.id,
                            returned_swag,
                        ),
                    )
                )

                returned_style = user_account.pending_style

                user_account.style_balance += returned_style
                user_account.pending_style = Decimal(0)
                self.swagdb.blockchain.append(
                    (
                        utcnow().datetime,
                        TransactionType.ROI,
                        (
                            user_account.id,
                            returned_style,
                        ),
                    )
                )
                self.transactional_save()
                yield user_account.discord_id, returned_swag, returned_style

    def get_history(self, user):
        id = self.swagdb.get_account(user).id
        return [
            transaction
            for transaction in self.swagdb.blockchain
            if concerns_user(id, transaction)
        ]

    def set_guild_timezone(self, guild, timezone):
        assert_timezone(timezone)
        self.swagdb.guild_timezone[guild] = timezone

        self.transactional_save()

    def set_timezone(self, user, timezone):
        user_account = self.swagdb.get_account(user)

        assert_timezone(timezone)

        t = utcnow()
        if t <= user_account.timezone_lock_date:
            raise TimeZoneFieldLocked(user_account.timezone_lock_date)
        lock_date = t.shift(days=1)

        user_account.timezone_lock_date = lock_date.datetime
        user_account.timezone = timezone

        self.transactional_save()

        return lock_date


def assert_timezone(timezone):
    try:
        now(timezone)
    except ParserError:
        raise InvalidTimeZone(timezone)
