from arrow.parser import ParserError
from arrow import now, utcnow
from decimal import Decimal, ROUND_UP
from numpy import log1p
from shutil import move
from random import choice
from math import ceil

from .cauchy import roll

from .errors import *

from .db import Cagnotte, SwagDB


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
        except (IOError, OSError):
            self.swagdb = SwagDB()

    def add_user(self, user, guild):
        self.swagdb.add_user(user, guild)
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
        self.swagdb.blockchain.append(("$wag Mine ⛏", user, mining_booty))

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
        self.swagdb.blockchain.append((giver, recipient, amount, "$wag"))

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
        self.swagdb.blockchain.append((giver, recipient, amount, "$tyle"))

        self.transactional_save()

    def block_swag(self, user, amount):
        user_account = self.swagdb.get_account(user)

        unblocking_date = (
            now(user_account.timezone)
            .shift(days=BLOCKING_TIME)
            .replace(microsecond=0, second=0, minute=0)
            .to("UTC")
            .datetime
        )

        # If no $tyle was generated yet, reset blockage
        if user_account.unblocking_date == unblocking_date:
            user_account.swag_balance += user_account.blocked_swag
            user_account.blocked_swag = 0
            user_account.unblocking_date = None

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
        self.swagdb.blockchain.append((user, "$tyle Generator Inc.", amount, "$wag"))

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
            ):
                returned_swag = user_account.blocked_swag

                user_account.swag_balance += returned_swag
                user_account.blocked_swag = 0
                self.swagdb.blockchain.append(
                    (
                        "$tyle Generator Inc.",
                        user_account.discord_id,
                        returned_swag,
                        "$wag",
                    )
                )

                returned_style = user_account.pending_style

                user_account.style_balance += returned_style
                user_account.pending_style = Decimal(0)
                self.swagdb.blockchain.append(
                    (
                        "$tyle Generator Inc.",
                        user_account.discord_id,
                        returned_style,
                        "$tyle",
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

        user_account.timezone_lock_date = lock_date
        user_account.timezone = timezone

        self.transactional_save()

        return lock_date

    ## Ajout des fonctions des cagnottes

    def create_cagnotte(self, cagnotte_name : str, currency : str, creator_id : int):
        self.swagdb.add_cagnotte(cagnotte_name,currency,creator_id)
        self.transactional_save()

    def get_active_cagnotte(self,cagnotte_idx) -> Cagnotte:
        if cagnotte_idx > 0 or cagnotte_idx < self.swagdb.cagnotte_number:
            cagnotte = self.swagdb.get_cagnotte_from_index(cagnotte_idx)
            if cagnotte.cagnotte_activation == True:
                return cagnotte
        
        raise NoCagnotteRegistered

    def get_all_active_cagnotte(self):
        return [
            cagnotte
            for cagnotte in self.swagdb.get_cagnotte_infos()
            if cagnotte.cagnotte_activation == True
        ]

    def donner_a_cagnotte(self,donator_account_discord_id : int, cagnotte_idx : int, montant):
        cagnotte = self.get_cagnotte(cagnotte_idx)
        donator_account = self.swagdb.get_active_cagnotte(donator_account_discord_id)
        #On regarde le type de la cagnotte pour pouvoir correctement choisir les fonctions qui devront être utiliser
        if cagnotte.get_info().cagnotte_currency == "$wag":

            #Check if the value of $wag is correct regardless its propriety
            if not isinstance(montant,int) or montant < 0:
                raise InvalidSwagValue

            #Check if the donator have enough $wag:
            if self.get_account_info(donator_account_discord_id).swag_balance - montant < 0:
                raise NotEnoughSwagInBalance

            #Making the donation
            donator_account.swag_balance -= montant
            cagnotte.cagnotte_montant += montant
        
        elif cagnotte.get_info().cagnotte_currency == "$tyle":

            #Check if the value of $tyle is correct regardless its propriety
            if not isinstance(montant,(int,float)) or montant < 0:
                raise InvalidStyleValue

            #Check if the donator have enough $tyle:
            if self.get_account_info(donator_account_discord_id).style_balance - montant < 0:
                raise NotEnoughStyleInBalance

            donator_account.swag_balance -= montant
            cagnotte.cagnotte_montant += montant

        ##TODO AJOUT DANS LA BLOCKCHAIN
        #self.swagAccounts[donator_account_name].write_in_history(self.account.history_movement.GIVE_TO,nom_cagnotte,montant,self.cagnottes[nom_cagnotte].currency)
        #self.cagnottes[nom_cagnotte].write_in_cagnotte_history(self.account.history_movement.RECEIVE_FROM,donator_account_name,montant)

        if donator_account_discord_id not in cagnotte.get_info().cagnotte_participant:
            cagnotte.cagnotte_participant.append(donator_account_discord_id) #TODO voir si ça marche

        self.transactional_save()

    def recevoir_depuis_cagnotte(self,cagnotte_idx : int, receiver_account_discord_id : int, montant, emiter_account_discord_id : int):
        cagnotte = self.get_active_cagnotte(cagnotte_idx)
        reciever_account = self.swagdb.get_account(receiver_account_discord_id)

        if emiter_account_discord_id not in cagnotte.get_info().cagnotte_gestionnaire:
            raise NotInGestionnaireGroupCagnotte

        #Check if the €agnotte have enough Money ($wag or $tyle):
        if cagnotte.get_info().cagnotte_montant - montant < 0:
            raise NotEnoughMoneyInCagnotte

        #On regarde le type de la cagnotte pour pouvoir correctement choisir les fonctions qui devront être utiliser
        if cagnotte.get_info().cagnotte_currency == "$wag":

            #Check if the value of $wag is correct regardless its propriety
            if not isinstance(montant,int) or montant < 0:
                raise InvalidSwagValue

            #Making the distribution
            reciever_account.swag_balance += montant
            cagnotte.cagnotte_montant -= montant
        
        elif cagnotte.get_info().cagnotte_montant == "$tyle":

            #Check if the value of $tyle is correct regardless its propriety
            if not isinstance(montant,(int,float)) or montant < 0:
                raise InvalidStyleValue

            reciever_account.style_balance += montant
            cagnotte.cagnotte_montant -= montant

        ##TODO AJOUT DANS LA BLOCKCHAIN
        #self.swagAccounts[receiver_account_name].write_in_history(self.account.history_movement.RECEIVE_FROM,nom_cagnotte,montant,self.cagnottes[nom_cagnotte].currency)
        #self.cagnottes[nom_cagnotte].write_in_cagnotte_history(self.account.history_movement.GIVE_TO,receiver_account_name,montant)
        self.transactional_save()

    def tirage_au_sort_cagnotte(self,cagnotte_idx : str, lst_of_participant : list, emiter_account_discord_id : int):
        cagnotte = self.get_active_cagnotte(cagnotte_idx)

        if not lst_of_participant: # si la liste des participants est vide, alors par défaut, ce sont ceux qui on participé à la cagnotte qui vont être tiré au sort
            lst_of_participant = cagnotte.get_info().cagnotte_participant

        gain = cagnotte.cagnotte_montant
        heureux_gagnant = choice(lst_of_participant)

        self.recevoir_depuis_cagnotte(cagnotte_idx,heureux_gagnant,gain,emiter_account_discord_id)

        return (heureux_gagnant,gain)


    def partage_cagnotte(self,cagnotte_idx : str, lst_of_account : list, emiter_account_discord_id : int):
        cagnotte = self.get_active_cagnotte(cagnotte_idx)

        if not lst_of_account: #Si la liste de compte est vide, tout les comptes de la bobbycratie seront pris par défaut
            lst_of_account = self.swagdb.discord_id

        gain_for_everyone = cagnotte.get_info().cagnotte_montant/len(lst_of_account)

        if cagnotte.get_info().cagnotte_currency == "$wag":
            gain_for_everyone = ceil(gain_for_everyone) #Le $wag est indivisible

        for account in lst_of_account: 
            self.recevoir_depuis_cagnotte(cagnotte_idx,account,gain_for_everyone,emiter_account_discord_id)

        gagnant_miette, gain_miette = None, None
        if cagnotte.get_info().cagnotte_montant != 0: #si il reste de l'argent à redistribuer, on tire au sort celui qui gagne les miettes
            gagnant_miette, gain_miette = self.tirage_au_sort_cagnotte(cagnotte_idx,lst_of_account,emiter_account_discord_id)

        return lst_of_account,gain_for_everyone,gagnant_miette,gain_miette

        
    def detruire_cagnotte(self,cagnotte_idx : str, emiter_account_discord_id : int):
        cagnotte = self.get_active_cagnotte(cagnotte_idx)

        if emiter_account_discord_id not in cagnotte.get_info().cagnotte_gestionnaire:
            raise NotInGestionnaireGroupCagnotte

        if cagnotte.get_info().cagnotte_montant != 0:
            raise DestructionOfNonEmptyCagnotte

        cagnotte.cagnotte_activation = False


def concerns_user(id, transaction):
    pass


def assert_timezone(timezone):
    try:
        now(timezone)
    except ParserError:
        raise InvalidTimeZone(timezone)
