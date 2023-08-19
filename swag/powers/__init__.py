"""
Here is the list of power which can be generated during a Yfu generation.
Implemented power which are not present in this list will not be used !
"""

#### AVAILABLE ACTIVE POWERS ####

from .actives.user_actives import (
    Robbery,
    HoldUp,
    Takeover,
    AssetLoss,
    InsiderTrading,
    DryLoss,
    TaxAudit,
    BankingBan,
)

from .actives.cagnotte_actives import (
    Embezzlement,
    DishonestJointVenture
)

from .actives.yfu_actives import (
    Kidnapping,
    # Resurrection # Pas necessaire pour le moment car pas possibilite de tuer
    # UltimateResurrection # idem
    # Cloning # On va laisser quelques Yfu existé avant d'ajouter ce pouvoir
    # Copy #idem
    # Clone #idem
)

from .actives.multitargetted_actives import (
    AfricanPrince,
    BankAdministrationError,
)

from .actives.untargetted_actives import (
    #Looting, # Trop complexe et puissant pour le moment
    FiredampCryptoExplosion,
    # TaxEvasion # Trop puissant pour le moment
)

#### AVAILABLE PASSIVE POWERS ####

from .passives.bonus_passives import (
    # InsolentLuck, # pas interressant pour le moment
    TaxOptimization,
    MauritiusCommercialBank,
    StockPortfolio,
    StockMarketMastery,
    StateGuardianship,
    SuccessfulInvestment,
)

# TODO Protection