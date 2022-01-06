class NoAccountRegistered(Exception):
    """Raised when an account name is not present in the $wagChain"""

    def __init__(self, name):
        self.name = name
        message = f"{name} n'a pas de compte sur la $wagChain™"
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


class InvalidSwagValue(Exception):
    """Raised when an invalid amount of swag is asked i.e not integor or negative"""

    pass


class InvalidStyleValue(Exception):
    """Raised when an invalid amount of style is asked i.e negative"""

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


class InvalidTimeZone(Exception):
    """Raised when an invalid timezone name is used"""

    def __init__(self, name):
        self.name = name
        message = f"{name} n'est pas une timezone valide"
        super().__init__(message)


class TimeZoneFieldLocked(Exception):
    """Raised when an user tries to set its timezone before its 24 hours lock."""

    def __init__(self, date):
        self.date = date
        message = f"Vous ne pouvez pas changer de timezone avant {date}."
        super().__init__(message)


##Exception for €agnottes


class NoCagnotteRegistered(Exception):
    """Raised when the cagnotte name or id is not present in the $wagChain™"""

    def __init__(self, name):
        self.name = name
        message = f"La €agnotte {name} n'existe pas dans la $wagChain™"
        super().__init__(message)


class NoReceiver(Exception):
    pass


class InvalidCagnotteId(Exception):
    pass


class CagnotteNameAlreadyExist(Exception):
    """Raised when a new cagnotte is created with an already used name"""

    pass


class NotEnoughMoneyInCagnotte(Exception):
    """Raised when a Cagnotte should have a negative value of $wag or $tyle"""

    def __init__(self, cagnotte_id):
        self.id = cagnotte_id
        message = f"La €agnotte {cagnotte_id} n'a pas assez d'argent pour faire la transaction demandé"
        super().__init__(message)


class NotCagnotteManager(Exception):
    """Raised when someone who is not a gestionnaire of a Cagnotte try to use a gestionnaire-action only"""

    pass


class CagnotteDestructionForbidden(Exception):
    """Raised when someone want to destroy a Cagnotte which still contain money inside"""

    pass


class CagnotteUnspecifiedException(Exception):
    """Raised when a €agnotte Identifier (€n) is missing for the associated command"""

    pass
