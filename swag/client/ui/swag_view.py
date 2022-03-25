from arrow import Arrow
import disnake

from swag.artefacts.accounts import SwagAccount
from swag.blocks.swag_blocks import Transaction
from swag.id import UserId


class SwagAccountEmbed(disnake.Embed):
    @classmethod
    def from_swag_account(cls, swag_account : SwagAccount, member : disnake.Member):

        if member.accent_color != None:
            color = member.accent_color.value
        else:
            color = int("0xffffff", base=16)

        if swag_account.unblocking_date != None:
            unblocking_date = Arrow.fromdatetime(dt = swag_account.unblocking_date).humanize(only_distance=True,locale="fr-fr",granularity=["day","hour","minute"])
        else:
            unblocking_date = "N/A"

        account_dict = {
            "title": f"Porte-Monnaie de {member.display_name}",
            "color": color,
            "thumbnail" : {"url": member.avatar.url},
            "fields": [
                {"name" : "📝 Date de création", "value" : swag_account.creation_date.format("DD/MM/YYYY"), "inline" : False},
                {"name" : "💰 $wag", "value" : f"{swag_account.swag_balance}", "inline" : True},
                {"name" : "👛 $tyle", "value" : f"{swag_account.style_balance}", "inline" : True},
                {"name" : "💹 Taux de bloquage", "value" : f"{swag_account.style_rate} %", "inline" : True},
                {"name" : "🔐 $wag bloqué", "value" : f"{swag_account.blocked_swag}", "inline" : True},
                {"name" : "💱 $tyle généré", "value" : f"{swag_account.pending_style}", "inline" : True},
                {"name" : "⏲️ Durée de blocage", "value" : unblocking_date, "inline" : True},
                {"name" : "👩‍🎤 Nombre de ¥fu", "value" : f"{len(swag_account.yfu_wallet)}", "inline" : False},
            ],
            "footer": {
                "text" : f"Timezone du compte : {swag_account.timezone}"
            }
        }

        return disnake.Embed.from_dict(account_dict)


class TransactionEmbed(disnake.Embed):
    @classmethod
    def from_transaction_block(cls, block : Transaction, bot : disnake.Client):

        issuer = bot.get_user(block.issuer_id.id)

        if block.giver_id is UserId:
            giver = bot.get_user(block.giver_id.id).display_name
        else :
            giver = f'{block.giver_id}'

        if block.recipient_id is UserId:
            recipient  = bot.get_user(block.recipient_id.id).display_name
        else :
            recipient = f'{block.recipient_id}'

        transaction_dict = {
            "title": f"{block.amount}",
            "color": int("0x0054e6", base=16),
            "author" : {"name" : issuer.display_name, "icon_url" : issuer.display_avatar.url},
            "fields": [
                {"name" : "➡️ Débiteur", "value" : giver, "inline" : True},
                {"name" : "🛂 Destinataire", "value" : recipient, "inline" : True},
            ],
        }

        return disnake.Embed.from_dict(transaction_dict)