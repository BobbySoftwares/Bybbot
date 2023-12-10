from typing import TYPE_CHECKING, List

from disnake import SelectOption
import disnake

from utils import GUILD_ID, get_guild_member_name

if TYPE_CHECKING:
    from swag.yfu import Yfu
    from swag.id import YfuId
    from disnake.ui import Select
    from swag.client import SwagClient


def sort_yfu_ids(yfu_set):
    return sorted(list(yfu_set), key=lambda yfu: int(yfu.id[1:]))


def yfus_to_select_options(yfus: List["Yfu"]):
    return [
        SelectOption(
            label=f"{yfu.first_name} {yfu.last_name}",
            description=yfu.power.get_effect(),
            emoji=yfu.clan,
            value=yfu.id.id,
        )
        for yfu in yfus
    ]


def forbes_to_select_options(swag_client: "SwagClient", exclude=[]):
    guild = swag_client.discord_client.get_guild(GUILD_ID)
    forbes = swag_client.swagchain.forbes

    def get_user_name(user_id):
        if (member := guild.get_member(user_id.id)) is not None:
            return member.display_name
        elif (
            user_name := swag_client.discord_client.get_user(user_id.id).display_name
        ) is not None:
            return user_name
        else:
            return f"INVALID USER {user_id.id}"

    return [
        SelectOption(
            label=get_user_name(user_id),
            description=f"{account.swag_balance} -- {account.style_balance} -- {len(account.yfu_wallet)} ¥fu(s)",
            emoji="💰",
            value=user_id.id,
        )
        for user_id, account in forbes
        if user_id not in exclude
    ]


def cagnottes_to_select_options(swag_client: "SwagClient"):
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


class UnlimitedSelectMenu(disnake.ui.StringSelect):
    """Classe dérivé des SelectMenu pour pouvoir gérer plusieurs options à la fois"""

    MAXIMUM_OPTION_IN_SELECT = 25

    def __init__(self, arg_placeholder: str, arg_row: int):
        super().__init__(min_values=1, max_values=1, row=arg_row)

        self.option_packet = []  # Liste des SelectOption
        self.page_index = 0
        self.placeholder_fist_part = arg_placeholder

        self.update_placeholder()

    @property
    def maximum_page(self):
        return int(len(self.option_packet))

    def set_options(self, options: list):
        def divide_options(l: list):
            """Permet d'avoir des petits paquets de 25 options dans une liste"""
            for i in range(0, len(l), UnlimitedSelectMenu.MAXIMUM_OPTION_IN_SELECT):
                yield l[i : i + UnlimitedSelectMenu.MAXIMUM_OPTION_IN_SELECT]

        # Mise à jour de l'ensemble des options possibles
        self.option_packet = list(divide_options(options.copy()))

        self.update_select()

    def update_select(self):
        self.options.clear()

        # On ajoute uniquement les options du paquet courant dans le menu déroulant
        for option in self.option_packet[self.page_index]:
            self.append_option(option)

        # On change le placeholder pour rendre compte des pages
        self.update_placeholder()

    def update_placeholder(self):
        self.placeholder = (
            self.placeholder_fist_part
            + f" (Page {self.page_index + 1}/{self.maximum_page})"
            + "..."
        )

    def is_first_page(self) -> bool:
        return self.page_index == 0

    def is_last_page(self) -> bool:
        return self.page_index == self.maximum_page - 1

    def go_previous_page(self):
        if self.is_first_page():
            return

        self.page_index -= 1

        self.update_select()

    def go_next_page(self):
        if self.is_last_page():
            return

        self.page_index += 1

        self.update_select()
