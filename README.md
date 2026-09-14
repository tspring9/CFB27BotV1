# CFB 27 Dynasty Bot

A Discord bot for our College Football 27 dynasty league.

## Commands

| Command   | What it does                     |
|-----------|----------------------------------|
| `/ping`   | Check the bot is alive           |
| `/uptime` | How long the bot has been running |
| `/help`   | List commands                    |

## Project layout

```
bot.py              # Entry point: creates the bot, loads cogs, syncs slash commands
config.py           # Reads settings from .env
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
