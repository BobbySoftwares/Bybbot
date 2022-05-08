class Module:

    def register_commands(self):
        pass

    async def setup(self):
        pass

    async def add_jobs(self, scheduler):
        pass

    async def process(self, message):
        pass
