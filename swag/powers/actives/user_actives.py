from enum import Flag, auto
from math import floor, sqrt
from typing import TYPE_CHECKING, List, OrderedDict

from arrow import utcnow

from swag.currencies import Style, Swag
from swag.errors import NotEnoughStyleInBalance, NotEnoughSwagInBalance
from swag.id import AccountId, CagnotteId, UserId
from swag.powers.power import Active
from swag.powers.target import Targets
from swag.stylog import stylog, styxp

if TYPE_CHECKING:
    from swag.blockchain.blockchain import SwagChain


class Robbery(Active):
    title = "Cambriolage"
    effect = "Permet de voler {} à un utilisateur."
    target = Targets().user(1)
    cost_factor = 1

    minimum_power_points = 1

    @property
    def _x_value(self):
        return Swag(self._raw_x)

    def _activation(
        self, chain: "SwagChain", owner_id: AccountId, targets: List[UserId]
    ):
        owner = chain._accounts[owner_id]
        target = chain._accounts[targets[0]]
        target.check_immunity(self)
        try:
            target -= self._x_value
            owner += self._x_value
        except NotEnoughSwagInBalance:
            owner += target.swag_balance
            target.swag_balance = Swag(0)


class HoldUp(Active):
    title = "Hold-up"
    effect = "Permet de voler {} bloqué(s) à un utilisateur."
    target = Targets().user(1)
    cost_factor = 0.75

    minimum_power_points = 1

    @property
    def _x_value(self):
        return Swag(self._raw_x * 1.25)

    def _activation(
        self, chain: "SwagChain", owner_id: AccountId, targets: List[UserId]
    ):
        owner = chain._accounts[owner_id]
        target = chain._accounts[targets[0]]
        target.check_immunity(self)
        try:
            target.blocked_swag -= self._x_value
            owner += self._x_value
        except NotEnoughSwagInBalance:
            owner += target.blocked_swag
            target.blocked_swag = Swag(0)


class Takeover(Active):
    title = "OPA"
    effect = "Permet de voler {} en cours de génération d'un utilisateur."
    target = Targets().user(1)
    cost_factor = 0.1

    minimum_power_points = 1

    @property
    def _x_value(self):
        return Style(sqrt(self._raw_x / 100_000))

    def _activation(
        self, chain: "SwagChain", owner_id: AccountId, targets: List[UserId]
    ):
        owner = chain._accounts[owner_id]
        target = chain._accounts[targets[0]]
        target.check_immunity(self)
        try:
            target.pending_style -= self._x_value
            owner += self._x_value
        except NotEnoughStyleInBalance:
            owner += target.pending_style
            target.pending_style = Style(0)


class AssetLoss(Active):
    title = "Perte d'actifs"
    effect = "Permet de débloquer {} d'un utilisateur."
    target = Targets().user(1)
    cost_factor = 0.001
    minimum_power_points = 1

    @property
    def _x_value(self):
        return Swag(styxp(0.004 * sqrt(self._raw_x / 100)))

    def _activation(
        self, chain: "SwagChain", owner_id: AccountId, targets: List[UserId]
    ):
        target = chain._accounts[targets[0]]
        target.check_immunity(self)
        try:
            target.blocked_swag -= self._x_value
            target += self._x_value
        except NotEnoughSwagInBalance:
            target += target.blocked_swag
            target.blocked_swag = Swag(0)


class InsiderTrading(Active):
    title = "Délit d'initié"
    effect = "Permet faire disparaître {} en cours de génération d'un utilisateur."
    target = Targets().user(1)
    cost_factor = 0.05

    minimum_power_points = 1

    @property
    def _x_value(self):
        return Style(sqrt(self._raw_x / 100_000))

    def _activation(
        self, chain: "SwagChain", owner_id: AccountId, targets: List[UserId]
    ):
        target = chain._accounts[targets[0]]
        target.check_immunity(self)
        try:
            target.style_balance -= self._x_value
        except NotEnoughStyleInBalance:
            target.style_balance = Style(0)


class DryLoss(Active):
    title = "Perte sèche"
    effect = "Permet de faire disparaître {} d'un compte d'un utilisateur."
    target = Targets().user(1)
    cost_factor = 0.75

    minimum_power_points = 1

    @property
    def _x_value(self):
        return Swag(self._raw_x * 1.75)

    def _activation(
        self, chain: "SwagChain", owner_id: AccountId, targets: List[UserId]
    ):
        target = chain._accounts[targets[0]]
        target.check_immunity(self)
        try:
            target -= self._x_value
        except NotEnoughSwagInBalance:
            target = Swag(0)


class TaxAudit(Active):
    title = "Contrôle fiscal"
    effect = "Permet d'envoyer {} d'un utilisateur vers la €agnotte '€Bobbycratie'."
    target = Targets().user(1)
    cost_factor = 0.75

    minimum_power_points = 1

    @property
    def _x_value(self):
        return Swag(self.power_points * 1_750)

    def _activation(
        self, chain: "SwagChain", owner_id: AccountId, targets: List[UserId]
    ):
        zero = chain._accounts[CagnotteId("€Bobbycratie")]
        target = chain._accounts[targets[0]]
        target.check_immunity(self)
        try:
            target -= self._x_value
            zero += self._x_value
        except NotEnoughSwagInBalance:
            zero += target.swag_balance
            target = Swag(0)


class BankingBan(Active):
    title = "Interdit bancaire"
    effect = "Empêche quelqu'un de miner pendant {} jours."
    target = Targets().user(1)
    cost_factor = 1

    minimum_power_points = 1000

    def _correct_dampening(self):
        return styxp(self._x_value) / self._raw_x

    @property
    def _x_value(self):
        # Ne devrait jamais atteindre moins de 1
        return int(stylog(self._raw_x))

    def _activation(
        self, chain: "SwagChain", owner_id: AccountId, targets: List[UserId]
    ):
        target = chain._accounts[targets[0]]
        target.check_immunity(self)
        target.last_mining_date = utcnow().shift(days=self._x_value)
