from abc import abstractmethod, abstractproperty
from swag.artefacts.bonuses import Bonuses
from swag.blockchain.blockchain import SwagChain

from swag.currencies import Style
from swag.id import AccountId, GenericId, YfuId


class Power:
    @abstractproperty
    def title(self):
        pass

    @abstractproperty
    def effect(self):
        pass

    def protection_cost(self, power):
        return Style("inf")

    def add_bonus(self, bonuses: Bonuses):
        pass


class Active(Power):
    @abstractproperty
    def target(self):
        pass

    @abstractproperty
    def has_value(self):
        pass

    @abstractmethod
    def _activation(self, chain: SwagChain, owner_id: AccountId, target_id: GenericId):
        pass
