from abc import abstractmethod, abstractproperty
from typing import TYPE_CHECKING, List
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
    def effect(self):
        pass

    @abstractproperty
    def minimum_power_points(self):
        """
        The minimum amount of PP (Power Point) to have to be able to generate this power
        """
        pass

    @abstractproperty
    def cost_factor(self) -> float:
        """
            Multiplicative factor of cost for a power.
            Is used to modify the final cost of a yfu power.
        Returns:
            int: cost factor should be never equal to 0 except for passive power
        """
        pass

    def __init__(self, pp) -> None:
        self.power_points = pp

    def protection_cost(self, power):
        return Style("inf")

    def get_effect(self):
        if hasattr(self, "_x_value"):
            return self.effect.format(self._x_value)
        else:
            return self.effect


class Active(Power):
    @abstractproperty
    def target(self):
        pass

    @abstractmethod
    def _activation(
        self, chain: "SwagChain", owner_id: AccountId, targets: List[GenericId]
    ):
        pass


class Passive(Power):
    @property
    def cost_factor(self) -> float:
        return 0  # les pouvoirs actifs n'ont pas de coût par définition

    @abstractmethod
    def add_bonus(self, bonuses: Bonuses):
        pass
