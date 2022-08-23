from abc import abstractmethod, abstractproperty
from typing import TYPE_CHECKING
from swag.artefacts.bonuses import Bonuses

from swag.currencies import Style
from swag.id import AccountId, GenericId, YfuId

if TYPE_CHECKING:
    from swag.blockchain.blockchain import SwagChain

class Power:
    @abstractproperty
    def title(self):
        pass

    @abstractproperty
    def type(self) -> str:
        pass

    @abstractproperty
    def effect(self):
        pass

    @abstractproperty
    def minimum_power_point(self):
        """
        The minimum amount of PP (Power Point) to have to be able to generate this power
        """
        pass

    def __init__(self,pp) -> None:
        self.power_point = pp

    def protection_cost(self, power):
        return Style("inf")

    def has_value(self):
        return hasattr(self,"_x_value")


class Active(Power):
    @abstractproperty
    def target(self):
        pass

    @property
    def type(self) -> str:
        return "[ACTIF]"

    @abstractmethod
    def _activation(self, chain: 'SwagChain', owner_id: AccountId, target_id: GenericId):
        pass

class Passive(Power):

    @property
    def type(self) -> str:
        return "[PASSIF]"

    @abstractmethod
    def add_bonus(self, bonuses: Bonuses):
        pass

