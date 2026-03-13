# Armenia Blackouts — OpenClaw Skill

Monitor power outages in Yerevan via the [ArmeniaBlackouts](https://t.me/s/ArmeniaBlackouts) Telegram channel.

## Setup

### 1. Install dependencies

```bash
pip3 install requests beautifulsoup4
```

### 2. Copy skill

```bash
cp -r armenia-blackouts ~/.openclaw/skills/
```

### 3. Configure address and language

Edit `~/.openclaw/skills/armenia-blackouts/config.json`:

```json
{
  "address": "Baghramyan 24, Yerevan",
  "language": "en"
}
```

Supported languages:
- `"en"` — English (default)
- `"ru"` — Russian
- `"hy"` — Armenian

### 4. Install HEARTBEAT.md into workspace

```bash
cp ~/.openclaw/skills/armenia-blackouts/HEARTBEAT.md ~/.openclaw/workspace/HEARTBEAT.md
```

> If you already have a HEARTBEAT.md — merge the section manually.

### 5. Configure heartbeat in openclaw.json

Merge the snippet from `openclaw-config-snippet.json` into `~/.openclaw/openclaw.json`.

Key settings:
- `every: "15m"` — check every 15 minutes
- `lightContext: true` — load only HEARTBEAT.md (saves tokens)
- `activeHours` — quiet period 23:00–07:00 (Asia/Yerevan), heartbeat does not run at night

```bash
openclaw config set agents.defaults.heartbeat.every "15m"
openclaw config set agents.defaults.heartbeat.lightContext true
```

### 6. Initialize state (skip history)

```bash
python3 ~/.openclaw/skills/armenia-blackouts/scripts/fetch_messages.py \
  && echo '{"last_message_id": 32100}' > ~/.openclaw/workspace/.blackouts-state.json
```

Replace `32100` with the current latest message ID.

### 7. Test manually

Send to the agent:
```
Check the ArmeniaBlackouts channel for new outages
```

Or use the slash command:

```
/armenia-blackouts
```

## How it works

```
openclaw heartbeat (every 15 min, only 07:00–23:00 Asia/Yerevan)
    └── reads HEARTBEAT.md
        └── runs armenia-blackouts skill
            ├── exec: fetch_messages.py → JSON of new messages
            ├── agent analyzes address match inline (Russian/Armenian NLP)
            ├── updates .blackouts-state.json
            └── if address affected → sends notification in configured language
```

At night (23:00–07:00) heartbeat is skipped via `activeHours`.
The first morning tick picks up all overnight messages.

## File structure

```
~/.openclaw/
├── openclaw.json                      ← heartbeat: every "15m" + activeHours
├── workspace/
│   ├── HEARTBEAT.md                   ← heartbeat checklist
│   └── .blackouts-state.json          ← last_message_id (created automatically)
└── skills/
    └── armenia-blackouts/
        ├── SKILL.md                   ← agent playbook
        ├── config.json                ← address + language
        └── scripts/
            └── fetch_messages.py      ← t.me/s/ArmeniaBlackouts scraper
```
