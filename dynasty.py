import re
from dataclasses import dataclass

from sheets import PublishedSheet


@dataclass(frozen=True)
class User:
    discord_id: str  # Numeric Discord ID or a username
    name: str
    team_id: str


@dataclass(frozen=True)
class Team:
    team_id: str
    school: str
    mascot: str
    conference: str


@dataclass(frozen=True)
class Game:
    season: str
    week: str
    home_team: str
    away_team: str
    neutral_site: bool
    home_rank: str
    away_rank: str
    status: str
    home_score: str
    away_score: str


@dataclass(frozen=True)
class Matchup:
    game: Game
    home_user: User | None
    away_user: User | None


def _truthy(value: str) -> bool:
    return value.strip().upper() in {"TRUE", "YES", "Y", "1"}


def _is_example(row: dict[str, str]) -> bool:
    return row.get("notes", "").lower().startswith("example row")


def clean_week(week: str) -> str:
    """'week 1' / 'Wk 01' / 'W1' -> '1'; 'Bowl' stays 'Bowl'."""
    week = re.sub(r"^(week|wk|w)\s*(?=\d)", "", week.strip(), flags=re.IGNORECASE)
    return str(int(week)) if week.isdigit() else week


def normalize_week(week: str) -> str:
    """Comparison key so weeks match however they were typed."""
    return clean_week(week).lower()


class Dynasty:
    """Typed views over the dynasty spreadsheet tabs."""

    def __init__(self, sheet: PublishedSheet):
        self.sheet = sheet

    async def config(self) -> dict[str, str]:
        return {row["key"]: row.get("value", "") for row in await self.sheet.rows("Config") if row.get("key")}

    async def users(self) -> list[User]:
        return [
            User(discord_id=row["discord_id"], name=row.get("name") or row["discord_id"], team_id=row["team_id"])
            for row in await self.sheet.rows("Users")
            if row.get("discord_id") and row.get("team_id") and _truthy(row.get("active") or "TRUE")
        ]

    async def teams(self) -> dict[str, Team]:
        return {
            row["team_id"]: Team(row["team_id"], row.get("school", ""), row.get("mascot", ""), row.get("conference", ""))
            for row in await self.sheet.rows("Teams")
            if row.get("team_id")
        }

    async def games(self) -> list[Game]:
        return [
            Game(
                season=row.get("season", ""),
                week=row.get("week", ""),
                home_team=row.get("home_team", ""),
                away_team=row.get("away_team", ""),
                neutral_site=_truthy(row.get("neutral_site", "")),
                home_rank=row.get("home_rank", ""),
                away_rank=row.get("away_rank", ""),
                status=row.get("status", ""),
                home_score=row.get("home_score", ""),
                away_score=row.get("away_score", ""),
            )
            for row in await self.sheet.rows("Games")
            if row.get("home_team") and row.get("away_team") and not _is_example(row)
        ]


def week_matchups(games: list[Game], users: list[User], season: str, week: str) -> tuple[list[Matchup], list[User]]:
    """Games in a week that involve at least one user team, plus the users on a bye."""
    by_team = {user.team_id: user for user in users}
    matchups: list[Matchup] = []
    playing: set[str] = set()

    for game in games:
        if game.season != season or normalize_week(game.week) != normalize_week(week):
            continue
        home_user, away_user = by_team.get(game.home_team), by_team.get(game.away_team)
        if not (home_user or away_user):
            continue
        matchups.append(Matchup(game, home_user, away_user))
        playing.update((game.home_team, game.away_team))

    byes = [user for user in users if user.team_id not in playing]
    return matchups, byes
