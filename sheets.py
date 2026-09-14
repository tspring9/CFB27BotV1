import asyncio
import csv
import io
import re
import time

import aiohttp

# Each tab appears in the published HTML as: items.push({name: "Users", pageUrl: "...", gid: "313934619"
_TAB_RE = re.compile(r'name: "([^"]+)", pageUrl: "[^"]*", gid: "(\d+)"')


class SheetError(Exception):
    pass


class PublishedSheet:
    """Read-only access to a Google Sheet published to the web (File > Share > Publish to web)."""

    def __init__(self, pub_url: str, cache_seconds: int = 60):
        # https://docs.google.com/spreadsheets/d/e/<id>/pubhtml -> https://docs.google.com/spreadsheets/d/e/<id>
        self._base = pub_url.split("/pub")[0]
        self._cache_seconds = cache_seconds
        self._gids: dict[str, str] = {}
        self._cache: dict[str, tuple[float, list[dict[str, str]]]] = {}
        self._lock = asyncio.Lock()
        self._session: aiohttp.ClientSession | None = None

    async def close(self) -> None:
        if self._session:
            await self._session.close()

    async def _get(self, url: str) -> str:
        if self._session is None:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20))
        async with self._session.get(url) as resp:
            if resp.status != 200:
                raise SheetError(f"Google returned HTTP {resp.status}")
            return await resp.text(encoding="utf-8")

    async def _load_gids(self) -> None:
        html = await self._get(f"{self._base}/pubhtml")
        self._gids = dict(_TAB_RE.findall(html))
        if not self._gids:
            raise SheetError("Couldn't find any tabs. Is the sheet still published to the web?")

    async def rows(self, tab: str) -> list[dict[str, str]]:
        """Return a tab as a list of {header: value} dicts, skipping blank rows."""
        async with self._lock:
            cached = self._cache.get(tab)
            if cached and time.monotonic() - cached[0] < self._cache_seconds:
                return cached[1]

            if tab not in self._gids:
                await self._load_gids()
            if tab not in self._gids:
                raise SheetError(f"No tab named '{tab}' in the sheet.")

            text = await self._get(f"{self._base}/pub?gid={self._gids[tab]}&single=true&output=csv")
            rows = [
                {key.strip(): (value or "").strip() for key, value in row.items() if key}
                for row in csv.DictReader(io.StringIO(text))
            ]
            rows = [row for row in rows if any(row.values())]

            self._cache[tab] = (time.monotonic(), rows)
            return rows
