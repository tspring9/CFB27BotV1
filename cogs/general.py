import time

import discord
from discord import app_commands
from discord.ext import commands


class General(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.started_at = time.monotonic()

    @app_commands.command(name="ping", description="Check that the bot is alive")
    async def ping(self, interaction: discord.Interaction) -> None:
        latency_ms = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"🏈 Pong! `{latency_ms} ms`", ephemeral=True)

    @app_commands.command(name="uptime", description="How long the bot has been running")
    async def uptime(self, interaction: discord.Interaction) -> None:
        seconds = int(time.monotonic() - self.started_at)
        days, rem = divmod(seconds, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, _ = divmod(rem, 60)
        await interaction.response.send_message(
            f"⏱️ Up for {days}d {hours}h {minutes}m", ephemeral=True
        )

    @app_commands.command(name="help", description="List the bot's commands")
    async def help_(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(title="CFB 27 Dynasty Bot", color=discord.Color.dark_orange())
        for cmd in sorted(self.bot.tree.get_commands(), key=lambda c: c.name):
            embed.add_field(name=f"/{cmd.name}", value=cmd.description, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(General(bot))
