from module import Module


class MaintenanceClient(Module):
    def __init__(self, client, admins) -> None:
        self.client = client
        self.admins = set(admins)

    async def process(self, message):
        if message.content.startswith("!sudo") and message.author.id in self.admins:
            command = message.content.split()
            if "reboot" in command:
                await self.client.logout()
