from enum import Flag, auto
from typing import List
from swag.blockchain.blockchain import SwagChain
from swag.currencies import Style, Swag
from swag.errors import NotEnoughStyleInBalance, NotEnoughSwagInBalance
from swag.id import AccountId, UserId
from swag.powers.power import Active
from swag.stylog import stylog


class Targetting(Flag):
    NONE = auto()
    USER = auto()
    CAGNOTTE = auto()
    ACCOUNT = USER | CAGNOTTE
    YFU = auto()
    ANYTHING = ACCOUNT | YFU
    USERS = auto()
    CAGNOTTES = auto()
    ACCOUNTS = USERS | CAGNOTTES
    YFUS = auto()
    ANYTHINGS = ACCOUNTS | YFUS


class Robbery(Active):
    title = "Cambriolage"
    effect = "Permet de voler du swag"
    target = Targetting.USER
    has_value = True

    @property
    def _x_value(self):
        return Swag(self._raw_x)

    def _activation(self, chain: SwagChain, owner_id: AccountId, target_id: UserId):
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
    effect = "Permet de voler du swag bloqué"
    target = Targetting.USER
    has_value = True

    @property
    def _x_value(self):
        return Swag(self._raw_x)

    def _activation(self, chain: SwagChain, owner_id: AccountId, target_id: UserId):
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
    effect = "Permet de voler du style généré"
    target = Targetting.USER
    has_value = True

    @property
    def _x_value(self):
        return Style(stylog(self._raw_x))

    def _activation(self, chain: SwagChain, owner_id: AccountId, target_id: UserId):
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
    effect = "Permet de débloquer une partie du swag de quelqu'un"
    target = Targetting.USER
    has_value = True

    @property
    def _x_value(self):
        return Swag(self._raw_x)

    def _activation(self, chain: SwagChain, owner_id: AccountId, target_id: UserId):
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
    effect = "Permet de détruire une partie du style généré d'autrui"
    target = Targetting.USER
    has_value = True

    @property
    def _x_value(self):
        return Style(stylog(self._raw_x))

    def _activation(self, chain: SwagChain, owner_id: AccountId, target_id: UserId):
        target = chain._accounts[target_id]
        target.check_immunity(self)
        try:
            target.style_balance -= self._x_value
        except NotEnoughStyleInBalance:
            target.style_balance = Style(0)


class DryLoss(Active):
    title = "Perte sèche"
    effect = "Permet de détruire le swag d'un compte"
    target = Targetting.USER
    has_value = True

    @property
    def _x_value(self):
        return Swag(self._raw_x)

    def _activation(self, chain: SwagChain, owner_id: AccountId, target_id: UserId):
        target = chain._accounts[target_id]
        target.check_immunity(self)
        try:
            target -= self._x_value
        except NotEnoughSwagInBalance:
            target = Swag(0)


class TaxAudit(Active):
    title = "Contrôle fiscal"
    effect = "Permet d'envoyer du swag d'un autre joueur vers la cagnotte 0"
    target = Targetting.USER
    has_value = True

    @property
    def _x_value(self):
        return Swag(self._raw_x)

    def _activation(self, chain: SwagChain, owner_id: AccountId, target_id: UserId):
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
    effect = "Empêche quelqu'un de miner pendant X jours"
    target = Targetting.USER
    has_value = True

    @property
    def _x_value(self):
        return int(stylog(self._raw_x))

    def _activation(self, chain: SwagChain, owner_id: AccountId, target_id: UserId):
        target = chain._accounts[target_id]
        target.check_immunity(self)
        target.last_mining_date = target.last_mining_date.shift(days=self._x_value)
