from typing import List
from arrow.parser import ParserError
from arrow import now, utcnow
from decimal import Decimal, ROUND_DOWN, ROUND_UP
from numpy import log1p
from shutil import move
from random import choice
from math import floor

from cbor2 import CBORDecodeEOF

from .cauchy import roll
from .errors import *

from .db import Currency, SwagDB, Cagnotte
from .transactions import TransactionType, concerns_cagnotte, concerns_user

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

    def get_cagnotte_info(self, cagnotte_idx):
        return self.swagdb.get_cagnotte_from_index(cagnotte_idx).get_info()

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
            return user.id

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

    ## Ajout des fonctions des cagnottes

    def create_cagnotte(self, cagnotte_name: str, currency: Currency, creator_id: int):
        self.swagdb.add_cagnotte(cagnotte_name, currency, creator_id)
        self.transactional_save()

    def get_active_cagnotte(self, cagnotte_idx) -> Cagnotte:
        if cagnotte_idx in self.swagdb.get_active_cagnotte_ids():
            return self.swagdb.get_cagnotte_from_index(cagnotte_idx)
        else:
            raise NoCagnotteRegistered(cagnotte_idx)

    def get_all_active_cagnotte(self):
        return [
            cagnotte
            for cagnotte in self.swagdb.get_cagnotte_infos()
            if cagnotte.is_active
        ]

    def get_cagnotte_history(self, cagnotte_idx):
        return [
            transaction
            for transaction in self.swagdb.blockchain
            if concerns_cagnotte(cagnotte_idx, transaction)
        ]

    def pay_to_cagnotte(
        self, donator_account_discord_id: int, cagnotte_idx: int, amount
    ):
        cagnotte = self.get_active_cagnotte(cagnotte_idx)
        donator_account = self.swagdb.get_account(donator_account_discord_id)
        # On regarde le type de la cagnotte pour pouvoir correctement choisir les fonctions qui devront être utiliser
        if cagnotte.currency == Currency.SWAG:

            # Check if the value of $wag is correct regardless its propriety
            if not isinstance(amount, int) or amount < 0:
                raise InvalidSwagValue

            # Check if the donator have enough $wag:
            if donator_account.swag_balance < amount:
                raise NotEnoughSwagInBalance(donator_account_discord_id)

            # Making the donation
            donator_account.swag_balance -= amount
            cagnotte.balance += amount

        elif cagnotte.currency == Currency.STYLE:

            # Check if the value of $tyle is correct regardless its propriety
            if not isinstance(amount, (int, float, Decimal)) or amount < 0:
                raise InvalidStyleValue

            # Check if the donator have enough $tyle:
            if donator_account.style_balance < amount:
                raise NotEnoughStyleInBalance

            donator_account.style_balance -= amount
            cagnotte.balance += amount

        # Write donation in the blockchain
        self.swagdb.blockchain.append(
            (
                utcnow().datetime,
                TransactionType.DONATION,
                (
                    donator_account.id,
                    cagnotte.id,
                    amount,
                    cagnotte.currency,
                ),
            )
        )

        cagnotte.participant.add(donator_account_discord_id)

        self.transactional_save()

    def receive_from_cagnotte(
        self,
        cagnotte_idx: int,
        receiver_account_discord_id: int,
        amount,
        emiter_account_discord_id: int,
    ):
        cagnotte = self.get_active_cagnotte(cagnotte_idx)
        receiver_account = self.swagdb.get_account(receiver_account_discord_id)

        if emiter_account_discord_id not in cagnotte.manager:
            raise NotInManagerGroupCagnotte

        # Check if the €agnotte have enough Money ($wag or $tyle):
        if cagnotte.balance < amount:
            raise NotEnoughMoneyInCagnotte(cagnotte.id)

        # On regarde le type de la cagnotte pour pouvoir correctement choisir les fonctions qui devront être utiliser
        if cagnotte.currency == Currency.SWAG:

            # Check if the value of $wag is correct regardless its propriety
            if not isinstance(amount, int) or amount < 0:
                raise InvalidSwagValue

            # Making the distribution
            receiver_account.swag_balance += amount
            cagnotte.balance -= amount

        elif cagnotte.currency == Currency.STYLE:

            # Check if the value of $tyle is correct regardless its propriety
            if not isinstance(amount, (int, float, Decimal)) or amount < 0:
                raise InvalidStyleValue

            receiver_account.style_balance += amount
            cagnotte.balance -= amount

            # Write distribution in the blockchain
        self.swagdb.blockchain.append(
            (
                utcnow().datetime,
                TransactionType.DISTRIBUTION,
                (
                    cagnotte.id,
                    receiver_account.id,
                    amount,
                    cagnotte.currency,
                ),
            )
        )
        self.transactional_save()

    def lottery_cagnotte(
        self,
        cagnotte_idx: str,
        lst_of_participant: List[int],
        emiter_account_discord_id: int,
    ):
        cagnotte = self.get_active_cagnotte(cagnotte_idx)

        # si la liste des participants est vide, alors par défaut, ce sont ceux qui on participé à la cagnotte qui vont être tiré au sort
        if not lst_of_participant:
            lst_of_participant = cagnotte.participant

        reward = cagnotte.balance
        winner = choice(lst_of_participant)

        self.receive_from_cagnotte(
            cagnotte_idx, winner, reward, emiter_account_discord_id
        )

        return winner, reward

    def share_cagnotte(
        self, cagnotte_idx: str, lst_of_account: list, emiter_account_discord_id: int
    ):
        cagnotte = self.get_active_cagnotte(cagnotte_idx)

        if (
            not lst_of_account
        ):  # Si la liste de compte est vide, tout les comptes de la bobbycratie seront pris par défaut
            lst_of_account = [
                account.discord_id for account in self.swagdb.get_account_infos()
            ]

        gain_for_everyone = cagnotte.balance / len(lst_of_account)

        if cagnotte.currency == Currency.SWAG:
            gain_for_everyone = int(gain_for_everyone)  # Le $wag est indivisible

        if cagnotte.currency == Currency.STYLE:
            gain_for_everyone = (cagnotte.balance / len(lst_of_account)).quantize(
                Decimal(".0001"), rounding=ROUND_DOWN
            )

        for account in lst_of_account:
            self.receive_from_cagnotte(
                cagnotte_idx, account, gain_for_everyone, emiter_account_discord_id
            )

        # si il reste de l'argent à redistribuer, on tire au sort celui qui gagne ce reste
        winner_rest, rest = None, None
        if cagnotte.balance != 0:
            winner_rest, rest = self.lottery_cagnotte(
                cagnotte_idx, lst_of_account, emiter_account_discord_id
            )

        return lst_of_account, gain_for_everyone, winner_rest, rest

    def destroy_cagnotte(self, cagnotte_idx: int, emiter_account_discord_id: int):
        cagnotte = self.get_active_cagnotte(cagnotte_idx)

        if emiter_account_discord_id not in cagnotte.manager:
            raise NotInManagerGroupCagnotte

        if cagnotte.balance != 0:
            raise ForbiddenDestructionOfCagnotte

        cagnotte.is_active = False

        self.transactional_save()

    def get_cagnotte_history(self, cagnotte_idx):
        return [
            transaction
            for transaction in self.swagdb.blockchain
            if concerns_cagnotte(cagnotte_idx, transaction)
        ]


def assert_timezone(timezone):
    try:
        now(timezone)
    except ParserError:
        raise InvalidTimeZone(timezone)
