from typing import TYPE_CHECKING

from disnake import SelectOption

from utils import GUILD_ID, get_guild_member_name

if TYPE_CHECKING:
    from swag.id import YfuId
    from disnake.ui import Select
    from swag.artefacts.accounts import Info
    from swag.client import SwagClient


def sort_yfus_id(yfu_set):
    return sorted(list(yfu_set), key=lambda yfu: yfu.id)


def yfus_to_select_options(yfus):
    return [
        SelectOption(
            label=f"{yfu.first_name} {yfu.last_name}",
            description=yfu.power.effect,
            emoji=yfu.clan,
            value=index,
        )
        for index, yfu in enumerate(yfus)
    ]


async def forbes_to_select_options(swag_client):
    guild = swag_client.discord_client.get_guild(GUILD_ID)
    client = swag_client.discord_client
    forbes = swag_client.swagchain.forbes
    return [
        SelectOption(
            label= await get_guild_member_name(user_id, guild, client),
            description=f"{account.swag_balance} -- {account.style_balance} -- {len(account.yfu_wallet)} ¥fu(s)",
            emoji="💰",
            value=user_id.id,
        )
        for user_id, account in forbes
    ]


def cagnottes_to_select_options(swag_client):
    cagnottes = swag_client.swagchain.cagnottes
    return [
        SelectOption(
            label=f"{cagnotte_id} {cagnotte.name}",
            description=f"{cagnotte.swag_balance} -- {cagnotte.style_balance} -- {len(cagnotte.yfu_wallet)} ¥fu(s)",
            emoji="🪙",
            value=cagnotte_id.id,
        )
        for cagnotte_id, cagnotte in cagnottes
    ]
