import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from dynasty import Matchup, Team, User, week_matchups
from sheets import SheetError

SHEET_ERRORS = (SheetError, aiohttp.ClientError, TimeoutError)


def mention(guild: discord.Guild | None, user: User) -> str:
    """@mention a user from the sheet; the sheet may hold a numeric ID or a username."""
    if user.discord_id.isdigit():
        return f"<@{user.discord_id}>"
    member = guild.get_member_named(user.discord_id) if guild else None
    return member.mention if member else f"@{user.name}"


def format_matchup(matchup: Matchup, teams: dict[str, Team], guild: discord.Guild | None) -> str:
    game = matchup.game

    def side(team_id: str, rank: str, user: User | None) -> str:
        team = teams.get(team_id)
        text = f"#{rank} " if rank else ""
        text += f"**{team.school if team else team_id}**"
        if user:
            text += f" ({mention(guild, user)})"
        return text

    away = side(game.away_team, game.away_rank, matchup.away_user)
    home = side(game.home_team, game.home_rank, matchup.home_user)
    line = f"🏈 {away} {'vs' if game.neutral_site else 'at'} {home}"
    if game.away_score and game.home_score:
        line += f" — **{game.away_score}-{game.home_score}** ({game.status or 'Final'})"
    return line


class DynastyCog(commands.Cog, name="Dynasty"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.dynasty = bot.dynasty

    async def _week_message(self, guild: discord.Guild | None, week: str | None) -> str:
        config = await self.dynasty.config()
        season = config.get("current_season", "")
        week = week or config.get("current_week", "")
        league = config.get("league_name") or "Dynasty"

        users, teams, games = await self.dynasty.users(), await self.dynasty.teams(), await self.dynasty.games()
        matchups, byes = week_matchups(games, users, season, week)

        header = f"**{league} — Week {week} Matchups** ({season})"
        if not matchups:
            return f"{header}\nNo games found for this week. Add them to the **Games** tab with status `Scheduled`."

        lines = [header, *(format_matchup(m, teams, guild) for m in matchups)]
        if byes:
            lines.append("💤 On bye: " + ", ".join(user.name for user in byes))
        return "\n".join(lines)

    async def _send_week(self, interaction: discord.Interaction, week: str | None, ping: bool) -> None:
        await interaction.response.defer(thinking=True)
        try:
            message = await self._week_message(interaction.guild, week)
        except SHEET_ERRORS as exc:
            await interaction.followup.send(f"⚠️ Couldn't read the dynasty sheet: {exc}")
            return
        mentions = discord.AllowedMentions(users=True) if ping else discord.AllowedMentions.none()
        await interaction.followup.send(message, allowed_mentions=mentions)

    @app_commands.command(name="matchups", description="Show user games for a week (no pings)")
    @app_commands.describe(week="Week to show, e.g. 3 or Bowl. Defaults to current_week in Config.")
    async def matchups(self, interaction: discord.Interaction, week: str | None = None) -> None:
        await self._send_week(interaction, week, ping=False)

    @app_commands.command(name="announce", description="Post a week's matchups and ping each coach")
    @app_commands.describe(week="Week to announce. Defaults to current_week in Config.")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def announce(self, interaction: discord.Interaction, week: str | None = None) -> None:
        await self._send_week(interaction, week, ping=True)

    @app_commands.command(name="coaches", description="List every coach and their team")
    async def coaches(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)
        try:
            users, teams = await self.dynasty.users(), await self.dynasty.teams()
        except SHEET_ERRORS as exc:
            await interaction.followup.send(f"⚠️ Couldn't read the dynasty sheet: {exc}")
            return

        embed = discord.Embed(title="Coaches", color=discord.Color.dark_orange())
        for user in sorted(users, key=lambda u: u.name.lower()):
            team = teams.get(user.team_id)
            value = f"{team.school} {team.mascot} · {team.conference}" if team else user.team_id
            embed.add_field(name=user.name, value=f"{value}\n{mention(interaction.guild, user)}", inline=True)
        await interaction.followup.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(DynastyCog(bot))
