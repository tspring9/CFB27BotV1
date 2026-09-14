# CFB 27 Dynasty Bot

A Discord bot for our College Football 27 dynasty league.

## Commands

| Command              | What it does                                                   |
|----------------------|----------------------------------------------------------------|
| `/matchups [week]`   | Show user games for a week, no pings                           |
| `/announce [week]`   | Post a week's matchups and ping each coach (Manage Server only) |
| `/coaches`           | List every coach and their team                                |
| `/ping`              | Check the bot is alive                                         |
| `/uptime`            | How long the bot has been running                              |
| `/help`              | List commands                                                  |

`week` defaults to `current_week` on the sheet's **Config** tab.

## The dynasty sheet

The bot reads the Google Sheet published to the web (`SHEET_URL`), cached for 60 seconds.
Google can take a few minutes to publish edits.

- **Users**: `discord_id` can be a Discord username or numeric user ID (IDs are most reliable for pings).
- **Teams**: team codes used everywhere else.
- **Games**: enter each user team's schedule preseason with `status = Scheduled`, then fill in
  scores and set `status = Final` as weeks are played. A user with no game in a week is on a bye.
- **Config**: `current_season` and `current_week`.

## Project layout

```
bot.py              # Entry point: creates the bot, loads cogs, syncs slash commands
config.py           # Reads settings from .env
sheets.py           # Reads tabs from the published Google Sheet
dynasty.py          # Users / Teams / Games models and weekly matchup logic
cogs/               # Feature modules (one file per group of commands)
deploy/             # systemd service for running on the Linux server
```

## Discord setup (one time)

1. Developer Portal -> your app -> **Bot** -> **Reset Token** and copy it.
2. Same page -> **Privileged Gateway Intents** -> enable **Server Members Intent**.
3. Invite the bot using the OAuth2 URL (scopes `bot` + `applications.commands`).

## Run on the server (Ubuntu)

```bash
sudo apt update && sudo apt install -y git python3 python3-venv

cd ~
git clone https://github.com/tspring9/CFB27BotV1.git
cd CFB27BotV1

python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

cp .env.example .env
nano .env        # paste DISCORD_TOKEN and GUILD_ID

.venv/bin/python bot.py   # test run; Ctrl+C to stop
```

### Keep it running (starts on boot, restarts on crash)

```bash
sudo cp deploy/cfb27bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now cfb27bot

systemctl status cfb27bot        # is it running?
journalctl -u cfb27bot -f        # live logs
```

### Updating

```bash
cd ~/CFB27BotV1
git pull
.venv/bin/pip install -r requirements.txt
sudo systemctl restart cfb27bot
```
