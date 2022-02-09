from typing import TYPE_CHECKING

from disnake import SelectOption

if TYPE_CHECKING:
    from swag.id import YfuId
    from disnake.ui import Select


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
