import logging

import discord
from discord.ext import commands

from config import Settings, load_settings
from dynasty import Dynasty
from sheets import PublishedSheet

log = logging.getLogger("cfb27bot")

EXTENSIONS = [
    "cogs.general",
    "cogs.dynasty",
]


class DynastyBot(commands.Bot):
    def __init__(self, settings: Settings):
        intents = discord.Intents.default()
        intents.members = True  # Requires "Server Members Intent" in the Developer Portal
        super().__init__(command_prefix=commands.when_mentioned, intents=intents, help_command=None)
        self.guild_id = settings.guild_id
        self.sheet = PublishedSheet(settings.sheet_url)
        self.dynasty = Dynasty(self.sheet)

    async def close(self) -> None:
        await self.sheet.close()
        await super().close()

    async def setup_hook(self) -> None:
        for ext in EXTENSIONS:
            await self.load_extension(ext)

        # Syncing to a single guild is instant; global sync can take a while to show up.
        if self.guild_id:
            guild = discord.Object(id=self.guild_id)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
        else:
            synced = await self.tree.sync()
        log.info("Synced %d slash command(s)", len(synced))

    async def on_ready(self) -> None:
        log.info("Logged in as %s (id %s)", self.user, self.user.id)


def main() -> None:
    settings = load_settings()
    discord.utils.setup_logging(level=logging.INFO)
    DynastyBot(settings).run(settings.token, log_handler=None)


if __name__ == "__main__":
    main()
