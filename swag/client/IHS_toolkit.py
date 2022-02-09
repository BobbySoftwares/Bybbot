from typing import TYPE_CHECKING

from disnake import SelectOption

from utils import get_guild_member_name

if TYPE_CHECKING:
    from swag.id import YfuId
    from disnake.ui import Select
    from swag.artefacts.accounts import Info


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


def forbes_to_select_options(forbes, guild, client):
    return [
        SelectOption(
            label=get_guild_member_name(user_id, guild, client),
            description=f"{account.swag_balance} {account.style_balance} {len(account.yfu_wallet)} ¥fu(s)",
            value=index,
        )
        for index, user_id, account in enumerate(forbes)
    ]


def cagnottes_to_select_options(cagnottes):
    return [
        SelectOption(
            label=f"{cagnotte_id} {cagnotte.name}",
            description=f"{cagnotte.swag_balance} {cagnotte.style_balance} {len(cagnotte.yfu_wallet)} ¥fu(s)",
            value=index,
        )
        for index, cagnotte_id, cagnotte in enumerate(cagnottes)
    ]
