from re import A
from arrow import Arrow
import disnake

from swag.artefacts.accounts import CagnotteAccount
from swag.id import CagnotteId


class CagnotteAccountEmbed(disnake.Embed):
    @classmethod
    def from_cagnotte_account(cls,cagnotte_id : CagnotteId, cagnotte_account : CagnotteAccount, bot : disnake.Client):

        managers = ", ".join([bot.get_user(user_id.id).display_name for user_id in cagnotte_account.managers])

        participants = ", ".join([bot.get_user(user_id.id).display_name for user_id in cagnotte_account.participants])
        if len(participants) == 0:
            participants = "N/A"
            
        account_dict = {
            "title": f"€agnotte {cagnotte_account.name}",
            "color": int("0xcfac23", base=16),
            "thumbnail" : {"url": f"https://dummyimage.com/1024x756/cfac23/333333&text={cagnotte_id.id}"},
            "fields": [
                
                {"name" : "👑 Gestionnaire(s)", "value" : managers, "inline" : False},

                {"name" : "💰 $wag", "value" : f"{cagnotte_account.swag_balance}", "inline" : True},
                {"name" : "👛 $tyle", "value" : f"{cagnotte_account.style_balance}", "inline" : True},
                
                {"name" : "🙋‍♀️🙋‍♂️ Participant(s)", "value" : participants, "inline" : False},
                
            ],
        }

        return disnake.Embed.from_dict(account_dict)