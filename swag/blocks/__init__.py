from .cagnotte_blocks import (
    CagnotteCreation,
    CagnotteRenaming,
    CagnotteParticipantsReset,
    CagnotteDeletion,
    CagnotteAddManagerBlock,
    CagnotteRevokeManagerBlock,
    CagnotteAddRankBlock,
    CagnotteAddAccountToRankBlock,
    CagnotteRemoveAccountToRankBlock,
    CagnotteRemoveRankBlock,
    ServiceCreation,
    UseService,
    CancelService,
    ServiceDelation,
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
    SacrificeYfuBlock,
)

from .system_blocks import (
    UserTimezoneUpdate,
    GuildTimezoneUpdate,
    EventGiveaway,
    AssetUploadBlock,
)
