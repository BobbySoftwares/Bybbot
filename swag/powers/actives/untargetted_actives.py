from typing import TYPE_CHECKING

from numpy import inf

# from swag.artefacts.accounts import CagnotteAccount
from swag.currencies import Swag
from swag.errors import NotEnoughSwagInBalance
from swag.id import AccountId, UserId
from swag.powers.power import Active
from swag.powers.target import TargetProperty, Targets
from swag.stylog import stylog

if TYPE_CHECKING:
    from swag.blockchain.blockchain import SwagChain


class Looting(Active):
    title = "Pillage"
    effect = "Permet de voler {} à tout le monde !"
    target = Targets()  # Pas de target car c'est tout le monde !
    cost_factor = 4

    minimum_power_point = 2000

    def __init__(self, pp) -> None:
        super().__init__(pp)
        self._raw_x = (pp) * 1000

    @property
    def _x_value(self):
        return self._raw_x

    def _activation(self, chain: "SwagChain", owner_id: AccountId, target_id: None):
        """Try to loot the entire world

        First, try to loot $wag balance of non-immunized users. If
        there is not enough $wag, loot from blocked $wag.

        If there is still not enough $wag, things starts to get real
        bad, and the same process is repeated for (no longer) immunized
        users, then cagnottes, then immunized cagnottes, and then, if
        no $wag remains anywhere, the rest contributes to enhance this
        power's x_value.
        """
        # owner = chain._accounts[owner_id]
        # tobbyb_id = UserId(856190053860114483)
        # targets = {}
        # sucked_targets = {}
        # immunized_targets = {}
        # cagnottes_targets = {}
        # immunized_cagnottes_targets = {}
        # for target_id, target in chain._accounts.items():
        #     if target_id != owner_id:
        #         if type(target) is CagnotteAccount:
        #             try:
        #                 target.check_immunity(self)
        #                 cagnottes_targets.insert(target)
        #             except NotImplementedError:
        #                 immunized_cagnottes_targets.insert(target)
        #         else:
        #             try:
        #                 target.check_immunity(self)
        #                 targets.insert(target)
        #             except NotImplementedError:
        #                 immunized_targets.insert(target)

        # targetss = [
        #     targets,
        #     immunized_targets,
        #     cagnottes_targets,
        #     immunized_cagnottes_targets,
        # ]
        # rest = Swag(self._x_value)
        # for targets in targetss:
        #     while rest > Swag(0) and len(targets) != 0:
        #         n = len(targets)
        #         punction = Swag(rest.value // n)
        #         if punction == Swag(0):
        #             try:
        #                 chain._accounts[tobbyb_id] -= rest
        #                 owner += rest
        #             except NotEnoughSwagInBalance:
        #                 owner += chain._accounts[tobbyb_id].swag_balance
        #                 rest -= chain._accounts[tobbyb_id].swag_balance
        #                 chain._accounts[tobbyb_id].swag_balance = Swag(0)

        #             break
        #         for target in list(targets):
        #             try:
        #                 target -= punction
        #                 owner += punction
        #                 rest -= punction
        #             except NotEnoughSwagInBalance:
        #                 owner += target.swag_balance
        #                 rest -= target.swag_balance
        #                 target.swag_balance = Swag(0)
        #                 sucked_targets.insert(target)
        #                 targets.remove(target)

        #     while rest > Swag(0) and len(targets) != 0:
        #         n = len(sucked_targets)
        #         punction = Swag(rest.value // n)
        #         if punction == Swag(0):
        #             try:
        #                 chain._accounts[tobbyb_id] -= rest
        #                 owner += rest
        #             except NotEnoughSwagInBalance:
        #                 owner += chain._accounts[tobbyb_id].swag_balance
        #                 rest -= chain._accounts[tobbyb_id].swag_balance
        #                 chain._accounts[tobbyb_id].swag_balance = Swag(0)
        #         for target in list(sucked_targets):
        #             try:
        #                 target.blocked_swag -= punction
        #                 owner += punction
        #                 rest -= punction
        #             except NotEnoughSwagInBalance:
        #                 owner += target.blocked_swag
        #                 rest -= target.blocked_swag
        #                 target.blocked_swag = Swag(0)
        #                 sucked_targets.remove(target)

        # self._secret_x += rest.value


class FiredampCryptoExplosion(Active):
    title = "Cryptogrisou"
    effect = "Empêche toute le monde sauf l'utilisateur de miner pendant {} jours."
    target = Targets()  #  Pas de target car c'est tout le monde !
    cost_factor = 1.5

    minimum_power_point = 64000

    def __init__(self, pp) -> None:
        super().__init__(pp)
        self._raw_x = (pp) * 1000

    @property
    def _x_value(self):
        return int(stylog(self._raw_x / 64))

    def _activation(self, chain: "SwagChain", owner_id: AccountId, target_id: None):
        for target in chain._accounts.values():
            if target_id != owner_id:
                try:
                    target.check_immunity(self)
                    target.last_mining_date = target.last_mining_date.shift(
                        days=self._x_value
                    )
                except NotImplementedError:
                    pass
                except AttributeError:
                    pass


class TaxEvasion(Active):
    title = "Fraude fiscale"
    effect = "Permet de miner {} fois de plus par jour."
    target = Targets()
    cost_factor = 2

    minimum_power_point = 2000

    def __init__(self, pp) -> None:
        super().__init__(pp)
        self._raw_x = (pp) * 1000

    @property
    def _x_value(self):
        return int(stylog(self._raw_x / 2))

    def _activation(self, chain: "SwagChain", owner_id: AccountId, target_id: None):
        owner = chain._accounts[owner_id]
        bonuses = owner.bonuses(chain)

        if (
            owner.last_mining_date is not None
            and owner.last_mining_date.date() > self.timestamp.to(owner.timezone).date()
        ):
            raise NotImplementedError

        amounts = [Swag(bonuses.roll()) for _ in range(self._x_value)]
        owner += sum(amounts)


# TODO
class Harvest(Active):
    title = "Moisson"
    effect = "Permet de tenter de récolter une ¥fu."
    target = Targets()
    cost_factor = 2

    def _activation(self, chain: "SwagChain", owner_id: AccountId, target_id: None):
        raise NotImplementedError
