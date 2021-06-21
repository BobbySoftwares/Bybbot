from datetime import date, datetime, timedelta
from enum import Enum, auto

from .cauchy import roll
import pickle


SWAG_BASE = 1000
SWAG_LUCK = 100000

TIME_OF_BLOCK = 3  # en jours
SWAG_STYLE_RATIO = 1 / 1000000  # 1 style pour 1 millions de $wag


class NoAccountRegistered(Exception):
    """Raised when an account name is not present in the SwagBank"""

    def __init__(self, name):
        self.name = name
        message = f"{name} n'a pas de compte sur $wagBank"
        super().__init__(message)


class AccountAlreadyExist(Exception):
    """Raised when a someone who already have an account create a new account"""

    pass


class NotEnoughSwagInBalance(Exception):
    """Raised when a account should have a negative value of swag"""

    def __init__(self, name):
        self.name = name
        message = f"{name} n'a pas assez d'argent sur son compte"
        super().__init__(message)


class InvalidValue(Exception):
    """Raised when an invalid amount of swag is asked i.e not integor or negative"""

    pass


class AlreadyMineToday(Exception):
    """Raised when an account try to mine the same day"""

    pass


class StyleStillBlocked(Exception):
    """Raised when someone want to interact with his $tyle but it's still blocked"""

    pass


class NotEnoughStyleInBalance(Exception):
    """Raised when a account should have a negative value of $tyle"""

    pass


class SwagBank:
    """Classe représentant la $wagBank, avec ses fonctionnalités et ses comptes."""

    class Account:
        """Un compte chez $wag bank"""

        class HistoryMovement(Enum):
            """Énumérateur qui permet d'indiquer si on a donné une monnaie (GIVE_TO) ou reçu (RECEIVE_FROM). Utilisé pour l'historique."""

            GIVE_TO = auto()
            RECEIVE_FROM = auto()

            def __str__(self) -> str:
                if self is self.GIVE_TO:
                    return "-->"
                else:
                    return "<--"

        def __init__(
            self,
            balance=0,
            history=None,
            last_time_mining=date.min,
            date_of_creation=date.today(),
        ):
            """Création du compte V1, avec le solde de $wag

            Args:
                balance (int, optional):             Nombre de $wag à la création du compte. Defaults to 0.
                history ([type], optional):          historique de transaction à l'initialisation du compte. Defaults to None.
                last_time_mining ([type], optional): Date du dernier minage, à l'initialisation du compte. Defaults to date.min.
                date_of_creation ([type], optional): Date de création, à l'initialisation du compte. Defaults to date.today().
            """
            self.balance = balance
            if history is None:
                self.history = []
            else:
                self.history = history.copy()
            self.last_time_mining = last_time_mining
            self.date_of_creation = date_of_creation

        def write_in_history(self, h_movement, account_name, value):
            """Écrit dans l'historique du compte

            Args:
                h_movement (HistoryMovement): Indiquer si l'argent à été donné (GIVE_TO) ou reçu (RECEIVE_FROM)
                account_name (Account): l'autre compte en relation avec la transaction
                value (int): Argent en jeu lors de la transaction
            """
            self.history.insert(
                0, (h_movement, account_name, value)
            )  # Une transaction est représenté par un tuple

    class AccountV2(Account):
        """Évolution de du compte V1 qui ajoute le $tyle. Hérite du compte V1."""

        def __init__(self, account_v1):
            """La création d'un compte V2 se fait à partir d'un compte V1 pour assurer le transfert entre les comptes V1 et V2.

            Args:
                AccountV1 (Account): compte V1
            """
            super().__init__(
                account_v1.balance,
                account_v1.history.copy(),
                account_v1.last_time_mining,
                account_v1.date_of_creation,
            )  # Construction
            self.balance_style = 0
            self.blocked_swag = 0
            self.dateAndTimeOfBlockage = datetime.min
            self.styleGrowthRate = 100  # in pourcent
            self.styleBonusRate = 0  # in pourcent

        def write_in_history(self, h_movement, account_name, value, currency="$wag"):
            """Surchage de la fonction write_in_history du compte V1

            Args:
                h_movement (HistoryMovement): Indiquer si l'argent à été donné (GIVE_TO) ou reçu (RECEIVE_FROM)
                account_name (Account): l'autre compte en relation avec la transaction
                value (int): Argent en jeu lors de la transaction
                currency (str, optional): Indique le type de monnaie qui a été échangé. Defaults to "$wag".
            """
            self.history.insert(0, (h_movement, account_name, value, currency))

    def __init__(self):
        """Initialisation de $wagBank"""
        try:
            self.swag_accounts = pickle.load(
                open("bank.swag", "rb")
            )  # On essaye d'ouvrir le fichier contenant l'ensemble des comptes
            for key_account_name, account in self.swag_accounts.items():
                if (
                    type(account) is self.Account
                ):  # Si il reste des comptes de type V1 dans le dictionnaire alors :
                    self.swag_accounts[key_account_name] = self.AccountV2(
                        AccountV1=Account
                    )  # Mise à jour du compte 1 vers le compte 2

            self.save_accounts()

        except (
            OSError,
            IOError,
        ) as e:  # Si le fichier des comptes n'existe pas, on crée un dictionnaire de compte vide, et on crée le fichier des comptes.
            self.swag_accounts = {}
            pickle.dump(self.swag_accounts, open("bank.swag", "wb"))

        # Check the must swag
        self.the_swaggest = None

        # On regarde si le dictionnaire des comptes n'est pas vide, si c'est le cas, on met à jour le plus swag.
        if self.swag_accounts:
            self.the_swaggest = self.get_the_new_swaggest()

    def save_accounts(self):
        """Permet de sauvegarder le dictionnaire des comptes dans un fichier système."""
        pickle.dump(self.swag_accounts, open("bank.swag", "wb"))

    def add_account(self, account_name):
        """Crée un nouveau compte chez $wagBank

        Args:
            account_name (String): Nom de compte, souvent le nom d'utilisateur général (ex : GlichiKun#4059)

        Raises:
            AccountAlreadyExist: Levée si un compte à ce nom existe déjà
        """
        if account_name not in self.swag_accounts.keys():
            self.swag_accounts[account_name] = self.AccountV2(self.Account())
            self.save_accounts()
        else:
            raise AccountAlreadyExist

    def get_balance_of(self, account_name):
        """Récupère le montant de $wag dans un compte

        Args:
            account_name (String): Nom de compte, souvent le nom d'utilisateur général (ex : GlichiKun#4059)

        Raises:
            NoAccountRegistered: Levée si il n'existe pas de compte au nom donné

        Returns:
            int: Montant de $wag
        """
        if account_name in self.swag_accounts.keys():
            return self.swag_accounts[account_name].balance
        else:
            raise NoAccountRegistered(account_name)

    def get_history(self, account_name):
        """Récupère l'historique des transaction du compte

        Args:
            account_name (String): Nom de compte, souvent le nom d'utilisateur général (ex : GlichiKun#4059)

        Raises:
            NoAccountRegistered: Levée si il n'existe pas de compte au nom donné

        Returns:
            List[tuple]: Liste des transactions
        """
        if account_name in self.swag_accounts.keys():
            return self.swag_accounts[account_name].history
        else:
            raise NoAccountRegistered(account_name)

    def move_money(self, account_name, howmany):
        """Permet d'ajouter ou d'enlever (en utilisant un howmany négatif) du $wag dans un compte

        Args:
            account_name (String): Nom de compte, souvent le nom d'utilisateur général (ex : GlichiKun#4059)
            howmany (int): valeur de $wag à ajouter (ou enlever si négatif !)

        Raises:
            NoAccountRegistered: Levée si il n'existe pas de compte au nom donné
        """
        if account_name in self.swag_accounts.keys():
            self.swag_accounts[account_name].balance = (
                self.swag_accounts[account_name].balance + howmany
            )
            self.save_accounts()
        else:
            raise NoAccountRegistered(account_name)

    def give_swag(self, expeditor_account_name, destinator_account_name, value_to_give):
        """Appelé pour réaliser une transaction de $wag complète entre deux comptes.

        Args:
            expeditor_account_name (String): Nom du compte de celui qui donne du $wag.
            destinator_account_name (String): Nom du compte de celui qui reçoit du $wag.
            value_to_give (int): quantité de $wag à échanger.

        Raises:
            InvalidValue: Levée si value_to_give n'est pas un entier positif.
            NotEnoughSwagInBalance: Levée si l'expéditeur n'a pas assez de $wag
        """

        # Check if the valueIsNotNegative or not int
        if value_to_give < 0 or not isinstance(value_to_give, int):
            raise InvalidValue

        # Check if the expeditor have enough money:
        if self.get_balance_of(expeditor_account_name) - value_to_give < 0:
            raise NotEnoughSwagInBalance(expeditor_account_name)

        # Make the transaction:
        self.move_money(expeditor_account_name, -value_to_give)  # Négatif
        self.move_money(destinator_account_name, value_to_give)  # Positif

        # Write transaction in history
        self.swag_accounts[expeditor_account_name].write_in_history(
            self.Account.HistoryMovement.GIVE_TO, destinator_account_name, value_to_give
        )
        self.swag_accounts[destinator_account_name].write_in_history(
            self.Account.HistoryMovement.RECEIVE_FROM,
            expeditor_account_name,
            value_to_give,
        )
        self.save_accounts()

    def mine(self, account_name):
        """Appelé lorsqu'un minage de $wag est demandé

        Args:
            account_name ([type]): Nom de compte, souvent le nom d'utilisateur général (ex : GlichiKun#4059)

        Raises:
            AlreadyMineToday: Levée si la personne a déjà miné dans la journée

        Returns:
            int: la quantité de $wag gagné par le minage
        """
        self.move_money(
            account_name, 0
        )  # petit tricks pour vérifier si le compte existe bien

        # On ne peut miner qu'une fois par jour
        if (
            not self.swag_accounts[account_name].last_time_mining < date.today()
        ):  # On vérifie si la date de la dernière fois qu'on a miné est bien inférieure à la date d'aujourd'hui
            raise AlreadyMineToday

        mining_booty = roll(
            SWAG_BASE, SWAG_LUCK
        )  # Génération d'un nombre aléatoire, en suivant une loi de Cauchy
        self.move_money(account_name, mining_booty)  # Ajout de cet argent au compte
        self.swag_accounts[
            account_name
        ].last_time_mining = date.today()  # Mise à jour de la date du dernier minage
        self.swag_accounts[account_name].write_in_history(
            self.Account.HistoryMovement.RECEIVE_FROM, "$wag Mine ⛏", mining_booty
        )  # écriture dans l'historique
        self.save_accounts()

        return mining_booty

    def get_list_of_account(self):
        """Récupère l'ensemble des noms de compte

        Returns:
            List[String]: Liste des noms de compte
        """
        return self.swag_accounts.keys()

    def get_classement(self, premier_en_premier=True):
        """Récupère la liste des comptes de $wagbank, classé en fonction de leur fortune en $wag

        Args:
            premier_en_premier (bool, optional): Si à True, le premier sera rangé en tête de la liste, Si False, il sera dernier de la liste. Defaults to True.

        Returns:
            Dict: Dictionnaire des comptes classé en fonction du $wag
        """
        return {
            key: account.balance
            for key, account in sorted(
                self.swag_accounts.items(),
                key=lambda item: item[1].balance,
                reverse=premier_en_premier,
            )
        }

    def get_the_new_swaggest(self):
        """Récupère la première personne du classement du $wag

        Returns:
            String: Nom de compte de celui qui a le plus de $wag
        """
        for user in self.get_classement().keys():
            return user

    def get_style_balance_of(self, account_name):
        """Récupère la quantité de $tyle dans le compte

        Args:
            account_name ([type]): Nom de compte, souvent le nom d'utilisateur général (ex : GlichiKun#4059)

        Raises:
            NoAccountRegistered: Levée si il n'existe pas de compte au nom donné

        Returns:
            Float: Quantité de $tyle dans le compte
        """
        if account_name in self.swag_accounts.keys():
            return self.swag_accounts[account_name].balance_style
        else:
            raise NoAccountRegistered(account_name)

    def get_bloked_swag(self, account_name):
        """Recupère le nombre de $wag actuellement bloqué pour la génération de $tyle pour un compte spécifique

        Args:
            account_name ([type]): Nom de compte, souvent le nom d'utilisateur général (ex : GlichiKun#4059)

        Raises:
            NoAccountRegistered: Levée si il n'existe pas de compte au nom donné

        Returns:
            int: quantité de $wag bloqué
        """
        if account_name in self.swag_accounts.keys():
            return self.swag_accounts[account_name].blocked_swag
        else:
            raise NoAccountRegistered(account_name)

    def get_style_total_growth_rate(self, account_name):
        """Récupère le taux de blocage total du $tyle actuel du compte

        Args:
            account_name ([type]): Nom de compte, souvent le nom d'utilisateur général (ex : GlichiKun#4059)

        Raises:
            NoAccountRegistered: Levée si il n'existe pas de compte au nom donné

        Returns:
            Float: Taux de blocage (100% + bonus de blocage)
        """
        if account_name in self.swag_accounts.keys():
            return (
                self.swag_accounts[account_name].styleGrowthRate
                + self.swag_accounts[account_name].styleBonusRate
            )
        else:
            raise NoAccountRegistered(account_name)

    def get_date_of_unblocking_swag(self, account_name):
        """Récupère la date de fin de blocage du $wag

        Args:
            account_name ([type]): Nom de compte, souvent le nom d'utilisateur général (ex : GlichiKun#4059)

        Raises:
            NoAccountRegistered: Levée si il n'existe pas de compte au nom donné

        Returns:
            datetime: jour et heure du déblocage du $wag
        """
        if account_name in self.swag_accounts.keys():
            blocking_duration = timedelta(days=3)
            return (
                self.swag_accounts[account_name].dateAndTimeOfBlockage
                + blocking_duration
            )
        else:
            raise NoAccountRegistered(account_name)

    def move_style(self, account_name, howmany):  # peut être utiliser pour le négatif
        """Permet d'ajouter ou d'enlever (en utilisant un howmany négatif) du $tyle dans un compte

        Args:
            account_name (String): Nom de compte, souvent le nom d'utilisateur général (ex : GlichiKun#4059)
            howmany (float): valeur de $tyle à ajouter (ou enlever si négatif !)

        Raises:
            NoAccountRegistered: Levée si il n'existe pas de compte au nom donné
        """
        if account_name in self.swag_accounts.keys():
            self.swag_accounts[account_name].balance_style = (
                self.swag_accounts[account_name].balance_style + howmany
            )
            self.save_accounts()
        else:
            raise NoAccountRegistered(account_name)

    def give_style(
        self, expeditor_account_name, destinator_account_name, value_to_give
    ):
        """Appelé pour réaliser une transaction de $tyle complète entre deux comptes.

        Args:
            expeditor_account_name (String): Nom du compte de celui qui donne du $tyle.
            destinator_account_name (String): Nom du compte de celui qui reçoit du $tyle.
            value_to_give (float): quantité de $tyle à échanger.

        Raises:
            InvalidValue: Levée si value_to_give n'est pas un nombre positif.
            NotEnoughSwagInBalance: Levée si l'expéditeur n'a pas assez de $tyle
        """
        # Check if the valueIsNotNegative or not int or float
        print(value_to_give)
        if value_to_give < 0 or not isinstance(value_to_give, (int, float)):
            raise InvalidValue

        # Check if the expeditor have enough $style:
        if self.get_style_balance_of(expeditor_account_name) - value_to_give < 0:
            raise NotEnoughStyleInBalance

        # Make the transaction:
        self.move_style(expeditor_account_name, -value_to_give)
        self.move_style(destinator_account_name, value_to_give)

        # Write transaction in history
        self.swag_accounts[expeditor_account_name].write_in_history(
            self.Account.HistoryMovement.GIVE_TO,
            destinator_account_name,
            value_to_give,
            currency="$tyle",
        )
        self.swag_accounts[destinator_account_name].write_in_history(
            self.Account.HistoryMovement.RECEIVE_FROM,
            expeditor_account_name,
            value_to_give,
            currency="$tyle",
        )
        self.save_accounts()

    def block_swag_to_get_style(self, account_name, amount_of_swag):
        """Appelée lorsqu'un utilisateur souhaite bloquer du $wag pour gagner du $tyle

        Args:
            account_name (String): Nom de compte, souvent le nom d'utilisateur général (ex : GlichiKun#4059)
            amount_of_swag (int): quantité de $wag que l'utilisateur souhaite bloquer

        Raises:
            InvalidValue: Levée si la quantité de $wag n'est pas un entier positif
            NotEnoughSwagInBalance: Levée si l'utilisateur n'a pas assez de $wag dans son compte
            StyleStillBlocked: Levée si l'utilisateur a toujours du $wag bloqué
        """

        # Check if the valueIsNotNegative or not int
        if amount_of_swag < 0 or not isinstance(amount_of_swag, int):
            raise InvalidValue

        # Check if the account have enough money:
        if self.get_balance_of(account_name) - amount_of_swag < 0:
            raise NotEnoughSwagInBalance(account_name)

        # Check if there is already swag blocked
        if self.swag_accounts[account_name].blocked_swag != 0:
            raise StyleStillBlocked

        self.move_money(account_name, -amount_of_swag)
        self.swag_accounts[account_name].blocked_swag = amount_of_swag
        self.swag_accounts[account_name].dateAndTimeOfBlockage = datetime.now()
        self.swag_accounts[account_name].write_in_history(
            self.AccountV2.HistoryMovement.GIVE_TO,
            "$tyle Generator Inc.",
            amount_of_swag,
            currency="$wag",
        )
        self.save_accounts()

    def is_blocking_swag(self, account_name):
        """Indique si un compte est actuellement entrain de bloquer du $wag ou non

        Args:
            account_name (String): Nom de compte, souvent le nom d'utilisateur général (ex : GlichiKun#4059)

        Returns:
            Bool: True si blocage en cours, False sinon
        """
        return self.get_bloked_swag(account_name) > 0

    def update_bonus_growth_rate(self):
        """Met à jour le bonus de blocage en fonction du classement du forbes"""
        classement = self.get_classement(premier_en_premier=False)

        x = 1
        nbr_partcipant = len(classement)
        for account_name in classement.keys():
            self.swag_accounts[account_name].styleBonusRate = round(
                (10 / 3) * (pow(16, x / nbr_partcipant) - 1), 2
            )  # Fonction mathématique, qui permet au premier d'avoir toujours 50%, et à celui à la moitié du classement 10%
            x += 1
        self.save_accounts()

    def earn_style(self, account_name):
        """Lance la génération de $tyle en fonction du bonus et du $wag bloqué

        Args:
            account_name (String): Nom de compte, souvent le nom d'utilisateur général (ex : GlichiKun#4059)
        """
        block_booty = (
            self.get_bloked_swag(account_name)
            * SWAG_STYLE_RATIO
            * (self.get_style_total_growth_rate(account_name) * 0.01)
        ) / (
            TIME_OF_BLOCK * 24
        )  # division pour gagner toute les heures
        self.move_style(account_name, block_booty)
        self.swag_accounts[account_name].write_in_history(
            self.AccountV2.HistoryMovement.RECEIVE_FROM,
            "$tyle Generator Inc.",
            block_booty,
            currency="$tyle",
        )
        self.save_accounts()

    def everyone_earn_style(self):
        """Activer la fonction earn_style sur tout les comptes enregistré à $wagBank"""
        for account_name in self.swag_accounts.keys():
            if self.is_blocking_swag(account_name):
                self.earn_style(account_name)

    def deblock_swag(self, account_name):
        """Fonction qui débloque le $wag si la date de déblocage est passé

        Args:
            account_name (String): Nom de compte, souvent le nom d'utilisateur général (ex : GlichiKun#4059)

        Raises:
            StyleStillBlocked: Levée si l'utilisateur a toujours du $wag bloqué
        """
        if datetime.now() < self.get_date_of_unblocking_swag(
            account_name
        ):  # Nous sommes toujours dans la période de blocage
            raise StyleStillBlocked

        returned_swag = self.get_bloked_swag(account_name)

        self.move_money(account_name, returned_swag)
        self.swag_accounts[account_name].blocked_swag = 0
        self.swag_accounts[account_name].write_in_history(
            self.AccountV2.HistoryMovement.RECEIVE_FROM,
            "$tyle Generator Inc.",
            returned_swag,
            currency="$wag",
        )
        self.save_accounts()
