import typing

if typing.TYPE_CHECKING:
    from swag.client.client import SwagClient

import disnake
from swag.yfu import Yfu


async def execute_yfu_command(swag_client: SwagClient, message: str):
    command_yfu = message.content.split()

    if "générer" in command_yfu:
        pass


class YfuEmbed(disnake.Embed):
    @classmethod
    def from_yfu(cls, yfu: Yfu):
        yfu_dict = {
            "title": f"{yfu.clan} {yfu.first_name} {yfu.last_name}",
            "image": {"url": yfu.avatar_url},
            "color": yfu.YfuRarity.from_power_point(yfu.power_point).get_color(),
            "fields": [
                {"name": yfu.power.name, "value": yfu.power.effect, "inline": False},
                {"name": "Coût", "value": f"{yfu.activation_cost}", "inline": True},
                {"name": "Avidité", "value": f"{yfu.greed}", "inline": True},
                {"name": "Zenitude", "value": f"{yfu.zenitude}", "inline": True},
            ],
            "footer": {
                "text": f"{yfu.generation_date.format('YYYY-MM-DD')} \t{yfu.hash}"
            },
        }
        return disnake.Embed.from_dict(yfu_dict)
