import json
import random
import requests
from arrow import Arrow
import disnake

from swag.artefacts.accounts import SwagAccount
from swag.artefacts.bonuses import Bonuses
from swag.blocks.swag_blocks import Mining, Transaction
from swag.currencies import Swag
from swag.id import UserId
from utils import TENOR_API_KEY, format_number


class SwagAccountEmbed(disnake.Embed):
    @classmethod
    def from_swag_account(
        cls, swag_account: SwagAccount, bonus_account: Bonuses, member: disnake.Member
    ):
        if member.accent_color != None:
            color = member.accent_color.value
        else:
            color = int("0xffffff", base=16)

        if swag_account.unblocking_date != None:
            unblocking_date = Arrow.fromdatetime(
                dt=swag_account.unblocking_date
            ).humanize(
                only_distance=True,
                locale="fr-fr",
                granularity=["day", "hour", "minute"],
            )
        else:
            unblocking_date = "N/A"

        account_dict = {
            "title": f"Porte-Monnaie de {member.display_name}",
            "color": color,
            "thumbnail": {"url": member.avatar.url},
            "fields": [
                {
                    "name": "📝 Date de création",
                    "value": swag_account.creation_date.format("DD/MM/YYYY"),
                    "inline": False,
                },
                {
                    "name": "",
                    "value": "",
                    "inline": False,
                },
                {
                    "name": "💰 $wag",
                    "value": f"{swag_account.swag_balance}",
                    "inline": True,
                },
                {
                    "name": "👛 $tyle",
                    "value": f"{swag_account.style_balance}",
                    "inline": True,
                },
                {
                    "name": "💹 Taux de bloquage",
                    "value": f"{swag_account.style_rate} %",
                    "inline": True,
                },
                {
                    "name": "",
                    "value": "",
                    "inline": False,
                },
                {
                    "name": "🔐 $wag bloqués",
                    "value": f"{swag_account.blocked_swag}",
                    "inline": True,
                },
                {
                    "name": "⚖️ $wag Base",
                    "value": format_number(bonus_account.base),
                    "inline": True,
                },
                {
                    "name": "🍀 $wag Luck",
                    "value": format_number(bonus_account.luck),
                    "inline": True,
                },
                {
                    "name": "",
                    "value": "",
                    "inline": False,
                },
                {
                    "name": "⛏️ Nombre de minage/jours",
                    "value": format_number(bonus_account.minings),
                    "inline": True,
                },
                {
                    "name": "🎲 Avantage",
                    "value": format_number(bonus_account.avantage),
                    "inline": True,
                },
                {
                    "name": "❌ Multiplicateur de minage",
                    "value": f"{bonus_account.multiplier}",
                    "inline": True,
                },
                {
                    "name": "",
                    "value": "",
                    "inline": False,
                },
                {
                    "name": "🎰 Chance à la lotterie",
                    "value": format_number(bonus_account.lottery_luck),
                    "inline": True,
                },
                {
                    "name": "👩‍🎤 Nombre de ¥fu",
                    "value": f"{len(swag_account.yfu_wallet)}",
                    "inline": True,
                },
            ],
            "footer": {"text": f"Timezone du compte : {swag_account.timezone}"},
        }

        return disnake.Embed.from_dict(account_dict)


class TransactionEmbed(disnake.Embed):
    @classmethod
    def from_transaction_block(cls, block: Transaction, bot: disnake.Client):
        issuer = bot.get_user(block.issuer_id.id)

        if block.giver_id is UserId:
            giver = bot.get_user(block.giver_id.id).display_name
        else:
            giver = f"{block.giver_id}"

        if block.recipient_id is UserId:
            recipient = bot.get_user(block.recipient_id.id).display_name
        else:
            recipient = f"{block.recipient_id}"

        transaction_dict = {
            "title": f"{block.amount}",
            "color": int("0x0054e6", base=16),
            "author": {
                "name": issuer.display_name,
                "icon_url": issuer.display_avatar.url,
            },
            "fields": [
                {"name": "➡️ Débiteur", "value": giver, "inline": True},
                {"name": "🛂 Destinataire", "value": recipient, "inline": True},
            ],
        }

        return disnake.Embed.from_dict(transaction_dict)


class MiningEmbed(disnake.Embed):
    @classmethod
    def from_mining_block(cls, block: Mining, bot: disnake.Client):
        user = bot.get_user(block.user_id.id)

        detailed_mining_message = ""

        # Ajout d'un message detaillé du minage sur un bonus (avantage / minage multiple / multiplicateur de minage)
        # S'est ajouté
        if block.amount.value != block.harvest[0]["details"]["avantages"][0]:
            detailed_mining_message = "\n\n### Détail du minage : "

            for i, mining in enumerate(block.harvest):
                avantage_len = len(mining["details"]["avantages"])
                detailed_mining_message += (
                    f"\n {f'{i+1}.' if len(block.harvest) > 1 else ''}"
                    f"{mining['details']['multiplier']} × "
                    f"{'max(' if avantage_len > 1 else ''}{', '.join(format_number(a) for a in mining['details']['avantages'])}{')' if avantage_len > 1 else ''}"
                    f" = {Swag(mining['result'])}"
                )

        mining_dict = {
            # Pas d'utilisation du titre car le titre ne supporte pas les mention sur desktop à ce jour
            "color": int("0xd1b671", base=16),
            "thumbnail": {
                "url": user.display_avatar.url,
            },
            "description": f"### {block.user_id} a miné ⛏️ !\n ## {format_number(block.amount.value)} $wag"  # Gestion un peu spéciale des espaces pour les embeds
            + detailed_mining_message,
            "image": {"url": cls.search_gif_from_mining(block), "width": 512},
        }

        return disnake.Embed.from_dict(mining_dict)

    @classmethod
    def search_gif_from_mining(cls, block: Mining) -> str:
        result = ""
        keyword_by_mining = {
            10000: [
                "bad",
                "poor",
                "awfull",
                "empty",
                "desert",
                "no money",
            ],
            50000: ["sad", "unhappy", "not good", "cringe", "awkward"],
            100000: ["ok", "cool", "why not ?", "smile"],
            200000: ["nice", "wonderfull", "happy", "mining"],
            1000000: [
                "rich",
                "super happy",
                "hyped",
                "picsou",
                "dollars",
                "raining money",
            ],
        }

        keywords = list(keyword_by_mining.values())[-1]

        for k, v in keyword_by_mining.items():
            if block.amount.value < k:
                keywords = v
                break

        # get the top 8 GIFs for the search term
        r = requests.get(
            "https://tenor.googleapis.com/v2/search?q=%s&key=%s&client_key=%s&limit=%s"
            % (random.choice(keywords), TENOR_API_KEY, "Bybbot", 50)
        )

        print(
            "https://tenor.googleapis.com/v2/search?q=%s&key=%s&client_key=%s&limit=%s"
            % (random.choice(keywords), TENOR_API_KEY, "Bybbot", 50)
        )

        if r.status_code == 200:
            # load the GIFs using the urls for the smaller GIF sizes
            result = random.choice(json.loads(r.content)["results"])["media_formats"][
                "gif"
            ]["url"]
        else:
            print("erreur API tenor")

        return result
