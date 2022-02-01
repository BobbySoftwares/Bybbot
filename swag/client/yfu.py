import disnake
from swag.yfu import Yfu
from swag.blocks.yfu_blocks import YfuGenerationBlock


async def execute_yfu_command(swag_client, message):
    command_yfu = message.content.split()

    if "générer" in command_yfu:
        yfu_block = YfuGenerationBlock(
            issuer_id=message.author.id, user_id=message.author.id
        )
        await swag_client.swagchain.append(yfu_block)

        await message.channel.send(
            f"{message.author.mention}, **{yfu_block.first_name} {yfu_block.last_name}** a rejoint vos rangs à des fins de test !",
            embed=YfuEmbed.from_yfu(
                swag_client.swagchain.account(yfu_block.user_id).yfu_wallet[-1]
            ),
        )
    else:
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
