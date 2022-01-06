from decimal import Decimal, ROUND_UP
from numpy import log1p

from swag.currencies import Style

# In days
BLOCKING_TIME = 3

STYLA = 1.9712167541353567
STYLB = 6.608024397705518e-07


def stylog(swag_amount):
    return Decimal(STYLA * log1p(STYLB * swag_amount))


def unit_style_generation(blocked_swag, style_rate):
    return Style(
        (stylog(blocked_swag.value) * style_rate / 100 / (BLOCKING_TIME * 24)).quantize(
            Decimal(".0001"), rounding=ROUND_UP
        )
    )
