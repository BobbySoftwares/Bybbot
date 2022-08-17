from swag.currencies import Style
from ...stylog import stylog


class Immunity:
    title = "Immunité"
    tier = "SS"
    effect = (
        "Immunise contre les pouvoirs négatifs d'autres waifus (cappé au coût "
        "de construction ?)"
    )

    def protection_cost(self, power):
        return Style(0)


class UltimateImmunity:
    title = "Immunité suprême"
    tier = "SSSS"
    effect = (
        "Immunise contre les pouvoirs négatifs d'autres waifus (cappé au coût "
        "de construction ?)"
    )

    def protection_cost(self, power):
        return Style(0)


class PartialImmunity:
    title = "Immunité contre X"
    effect = "Immunise contre un type X de pouvoir négatif"

    def protection_cost(self, power):
        if self.power_kind is power:
            return Style(0)
        else:
            return Style("inf")


class Protection:
    title = "Protection"
    effect = "Protège contre un coût en style contre tous les effets négatifs"

    @property
    def _x_value(self):
        return int(stylog(self._raw_x))

    def protection_cost(self, power):
        return self._x_value


class PartialProtection:
    title = "Protection contre X"
    effect = "Protège contre un coût en style des effets négatifs de type x"

    @property
    def _x_value(self):
        return int(stylog(self._raw_x))

    def protection_cost(self, power):
        if self.power_kind is power:
            return self._x_value
        else:
            return Style("inf")
