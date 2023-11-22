from .cagnotte_blocks import (
    CagnotteCreation,
    CagnotteRenaming,
    CagnotteParticipantsReset,
    CagnotteDeletion,
    CagnotteAddManagerBlock,
    CagnotteRevokeManagerBlock,
)
from .swag_blocks import (
    AccountCreation,
    AccountDeletion,
    Mining,
    Transaction,
    SwagBlocking,
    ReturnOnInvestment,
    StyleGeneration,
)

from .yfu_blocks import (
    YfuGenerationBlock,
    RenameYfuBlock,
    TokenTransactionBlock,
    YfuPowerActivation,
)

from .system_blocks import (
    UserTimezoneUpdate,
    GuildTimezoneUpdate,
    EventGiveaway,
    AssetUploadBlock,
)
