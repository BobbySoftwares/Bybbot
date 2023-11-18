class NoSwagAccountRegistered(Exception):
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


class NoCagnotteAccountRegistered(Exception):
    """Raised when the cagnotte name or id is not present in the $wagChain™"""

    def __init__(self, name):
        self.name = name
        message = f"La €agnotte {name} n'existe pas dans la $wagChain™"
        super().__init__(message)


class NoReceiver(Exception):
    pass


class InvalidCagnotteId(Exception):
    def __init__(self, value):
        self.value = value
        message = f"L'id de €agnotte {value} est invalide"
        super().__init__(message)


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

    def __init__(self, name):
        self.name = name
        message = f"{name} n'est pas gestionnaire de cette €agnotte"
        super().__init__(message)

    pass


class AlreadyCagnotteManager(Exception):
    def __init__(self, name):
        self.name = name
        message = f"{name} est déjà gestionnaire de cette €agnotte"
        super().__init__(message)


class OrphanCagnotte(Exception):
    """Raised when an action result to remove all the manager of a €agnotte"""


class CagnotteDestructionForbidden(Exception):
    """Raised when someone want to destroy a Cagnotte which still contain money inside"""

    pass


class CagnotteUnspecifiedException(Exception):
    """Raised when a €agnotte Identifier (€n) is missing for the associated command"""

    pass


##Exception for ¥fus
class InvalidYfuId(Exception):
    pass

class IncorrectYfuName(Exception):
    def __init__(self, name):
        self.name = name
        message = f"Le renommage de la ¥fu avec le prénom {name} est incorrect"
        super().__init__(message)


class InvalidId(Exception):
    pass

class BadOwnership(Exception):
    def __init__(self, user_id, id) -> None :
        self.id = id
        message = f"La ¥fu {id} n'apartient pas à {user_id}"
        super().__init__(message)
    pass

class YfuNotReady(Exception):
    def __init__(self, id) -> None :
        self.id = id
        message = f"La ¥fu {id} ne peut pas encore être activé aujourd'hui"
        super().__init__(message)
    pass

class CantUseYfuPower(Exception):
    def __init__(self, id, target) -> None :
        self.id = id
        self.target = target
        message = f"{id} ne peut pas utilisé son pouvoir contre {target}"
        super().__init__(message)
    pass