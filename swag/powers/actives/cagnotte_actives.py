from swag.blockchain.blockchain import SwagChain
from swag.currencies import Style, Swag
from swag.errors import NotEnoughStyleInBalance, NotEnoughSwagInBalance
from swag.id import AccountId, CagnotteId
from swag.powers.actives.user_actives import Targetting
from swag.stylog import stylog


class Embezzlement:
    title = "Détournement de fonds"
    effect = "Permet de voler du swag d'une cagnotte"
    target = Targetting.CAGNOTTE
    has_value = True

    @property
    def _x_value(self):
        return Swag(self._raw_x)

    def _activation(self, chain: SwagChain, owner_id: AccountId, target_id: CagnotteId):
        owner = chain._accounts[owner_id]
        target = chain._accounts[target_id]
        target.check_immunity(self)
        try:
            target -= self._x_value
            owner += self._x_value
        except NotEnoughSwagInBalance:
            owner += target.swag_balance
            target.swag_balance = Swag(0)


class DishonestJointVenture:
    title = "Joint-venture malhonnête"
    effect = "Permet de voler du style d'une cagnotte"
    target = Targetting.CAGNOTTE
    has_value = True

    @property
    def _x_value(self):
        return Style(stylog(self._raw_x))

    def _activation(self, chain: SwagChain, owner_id: AccountId, target_id: CagnotteId):
        owner = chain._accounts[owner_id]
        target = chain._accounts[target_id]
        target.check_immunity(self)
        try:
            target -= self._x_value
            owner += self._x_value
        except NotEnoughStyleInBalance:
            owner += target.style_balance
            target.style_balance = Style(0)
