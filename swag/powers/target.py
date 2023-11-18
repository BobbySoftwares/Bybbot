from enum import Flag, auto
from typing_extensions import Self


class TargetProperty(Flag):
    RANDOM = auto()
    CASTER_NOT_INCLUDED = auto()
    FROM_CASTER_ONLY = auto()

class TargetType(Flag):
    USER = auto()
    CAGNOTTE = auto()
    ACCOUNT = USER | CAGNOTTE
    YFU = auto()
    ANYTHING = ACCOUNT | YFU

class Targets():

    def __init__(self) -> None:
        self._stack_of_targets = []

    def user(self, number_of_user, properties = [] ) -> Self:
        self._add_to_stack(number_of_user,TargetType.USER, properties)
        return self

    def cagnotte(self, number_of_cagnotte, properties = []) -> Self:
        self._add_to_stack(number_of_cagnotte,TargetType.CAGNOTTE, properties)
        return self

    def account(self, number_of_account, properties = []) -> Self:
        self._add_to_stack(number_of_account,TargetType.ACCOUNT, properties)
        return self

    def yfu(self, number_of_yfu, properties = []) -> Self:
        self._add_to_stack(number_of_yfu,TargetType.YFU, properties)
        return self

    def anything(self, number_of_anything, properties = []) -> Self:
        self._add_to_stack(number_of_anything,TargetType.ANYTHING, properties)
        return self

    def _add_to_stack(self, number, target_type ,properties):
        for i in range(number):
            self._stack_of_targets.append((target_type, properties))
