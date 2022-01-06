from utils import GUILD_ID_BOBBYCRATIE
from swag.utils import update_forbes_classement
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

            await update_forbes_classement(
                self.client.get_guild(GUILD_ID_BOBBYCRATIE),
                self.swag_module,
                self.client,
            )
