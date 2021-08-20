from utils import GUILD_ID_BOBBYCRATIE
from swag.utils import update_forbes_classement
from swag.transactions import TransactionType
from arrow.api import utcnow
from module import Module


class MaintenanceClient(Module):
    def __init__(self, client, admins, swag_module) -> None:
        self.client = client
        self.admins = set(admins)
        self.swag_module = swag_module

    async def process(self, message):
        if message.content.startswith("!sudo") and message.author.id in self.admins:
            command = message.content.split()

            if "reboot" in command:
                await self.client.logout()

            if "$wag" in command:

                destinataire = message.mentions
                if len(destinataire) != 1:
                    await message.channel.send(
                        "Merci de mentionner un destinataire (@Bobby Machin) "
                        "pour lui donner du$wag !"
                    )
                    return
                destinataire = destinataire[0]

                recipient = destinataire.id

                # Récupération de la valeur envoyé

                montant = int(
                    "".join(argent for argent in command if argent.isnumeric())
                )

                # envoie du swag
                recipient_account = self.swag_module.swag_bank.swagdb.get_account(
                    recipient
                )

                recipient_account.swag_balance += montant

                # écriture dans l'historique
                self.swag_module.swag_bank.swagdb.blockchain.append(
                    (
                        utcnow().datetime,
                        TransactionType.ADMIN,
                        (recipient_account.id, montant),
                    )
                )

                self.swag_module.swag_bank.transactional_save()

            await update_forbes_classement(
                self.client.get_guild(GUILD_ID_BOBBYCRATIE),
                self.swag_module,
                self.client,
            )

            await self.client.close()
