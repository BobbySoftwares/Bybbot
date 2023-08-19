from enum import Flag, auto
from math import floor
from typing import TYPE_CHECKING, List, OrderedDict

from swag.currencies import Style, Swag
from swag.errors import NotEnoughStyleInBalance, NotEnoughSwagInBalance
from swag.id import AccountId, UserId
from swag.powers.power import Active
from swag.powers.target import Targets
from swag.stylog import stylog

if TYPE_CHECKING:
    from swag.blockchain.blockchain import SwagChain


class Robbery(Active):
    title = "Cambriolage"
    effect = "Permet de voler {} à un utilisateur."
    target = Targets().user(1)

    minimum_power_point = 1

    def __init__(self, pp) -> None:
        super().__init__(pp)
        self._raw_x = (pp) * 1000

    @property
    def _x_value(self):
        return Swag(self._raw_x)

    def _activation(self, chain: "SwagChain", owner_id: AccountId, target_id: UserId):
        owner = chain._accounts[owner_id]
        target = chain._accounts[target_id]
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

    minimum_power_point = 1

    def __init__(self, pp) -> None:
        super().__init__(pp)
        self._raw_x = (pp) * 1000

    @property
    def _x_value(self):
        return Swag(self._raw_x * 1.2)

    def _activation(self, chain: "SwagChain", owner_id: AccountId, target_id: UserId):
        owner = chain._accounts[owner_id]
        target = chain._accounts[target_id]
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

    minimum_power_point = 1

    def __init__(self, pp) -> None:
        super().__init__(pp)
        self._raw_x = pp

    @property
    def _x_value(self):
        return Style(0.01 * self._raw_x * 2.5)

    def _activation(self, chain: "SwagChain", owner_id: AccountId, target_id: UserId):
        owner = chain._accounts[owner_id]
        target = chain._accounts[target_id]
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

    minimum_power_point = 1

    def __init__(self, pp) -> None:
        super().__init__(pp)
        self._raw_x = (pp) * 1000

    @property
    def _x_value(self):
        return Swag(self._raw_x * 2)

    def _activation(self, chain: "SwagChain", owner_id: AccountId, target_id: UserId):
        target = chain._accounts[target_id]
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

    minimum_power_point = 1

    def __init__(self, pp) -> None:
        super().__init__(pp)
        self._raw_x = pp

    @property
    def _x_value(self):
        return Style(0.01 * self._raw_x * 3)

    def _activation(self, chain: "SwagChain", owner_id: AccountId, target_id: UserId):
        target = chain._accounts[target_id]
        target.check_immunity(self)
        try:
            target.style_balance -= self._x_value
        except NotEnoughStyleInBalance:
            target.style_balance = Style(0)


class DryLoss(Active):
    title = "Perte sèche"
    effect = "Permet de faire disparaître {} d'un compte d'un utilisateur."
    target = Targets().user(1)

    minimum_power_point = 1

    def __init__(self, pp) -> None:
        super().__init__(pp)
        self._raw_x = (pp) * 1000

    @property
    def _x_value(self):
        return Swag(self._raw_x * 1.75)

    def _activation(self, chain: "SwagChain", owner_id: AccountId, target_id: UserId):
        target = chain._accounts[target_id]
        target.check_immunity(self)
        try:
            target -= self._x_value
        except NotEnoughSwagInBalance:
            target = Swag(0)


class TaxAudit(Active):
    title = "Contrôle fiscal"
    effect = "Permet d'envoyer {} d'un utilisateur vers la €agnotte '€'."
    target = Targets().user(1)

    minimum_power_point = 1

    def __init__(self, pp) -> None:
        super().__init__(pp)
        self._raw_x = (pp) * 1000

    @property
    def _x_value(self):
        return Swag(self._raw_x * 1.75)

    def _activation(self, chain: "SwagChain", owner_id: AccountId, target_id: UserId):
        zero = chain._accounts["€"]  # "€Bobbycratie"? can't remember what I meant
        target = chain._accounts[target_id]
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

    minimum_power_point = 1000

    def __init__(self, pp) -> None:
        super().__init__(pp)
        self._raw_x = (pp) * 1000

    @property
    def _x_value(self):
        return int(floor(stylog(self._raw_x)))  # Ne devrait jamais atteindre moins de 1

    def _activation(self, chain: "SwagChain", owner_id: AccountId, target_id: UserId):
        target = chain._accounts[target_id]
        target.check_immunity(self)
        target.last_mining_date = target.last_mining_date.shift(days=self._x_value)
