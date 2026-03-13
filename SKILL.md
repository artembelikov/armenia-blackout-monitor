---
name: armenia-blackouts
description: >
  Check the ArmeniaBlackouts Telegram channel for new power outage messages
  and determine if a configured home address is affected. Use this skill
  when the agent needs to monitor electricity outages in Yerevan, Armenia,
  check blackout status, or run the scheduled blackout check from HEARTBEAT.md.
user-invocable: true
metadata: {"openclaw":{"requires":{"bins":["python3"]}}}
---

# Armenia Blackouts — Skill

Monitor **t.me/s/ArmeniaBlackouts** and report whether the configured address
is affected by a planned or emergency power outage.

## State file

All persistent state lives at `~/.openclaw/workspace/.blackouts-state.json`:

```json
{
  "last_message_id": 32100,
  "last_check": "2025-03-15T10:00:00",
  "messages_checksum": "e3b0c44298fc1c149afb..."
}
```

Create it with `{}` if it does not exist yet.

## Workflow

### Step 1 — Read state

```bash
cat ~/.openclaw/workspace/.blackouts-state.json 2>/dev/null || echo '{"last_message_id":0}'
```

### Step 2 — Read config

```bash
cat ~/.openclaw/skills/armenia-blackouts/config.json
```

The config contains:
- `address` — the user's home address to match against
- `district` — administrative district (e.g. `"Arabkir"`), used when a message
  mentions only a district without specific streets
- `language` — output language: `"en"` (default), `"ru"`, or `"hy"` (Armenian)

### Step 3 — Fetch Telegram channel page

```bash
python3 ~/.openclaw/skills/armenia-blackouts/scripts/fetch_messages.py
```

This fetches the **last 7 messages** from the channel and checks whether their
content has changed since the last run (via SHA-256 checksum stored in state).

Two possible outputs:

```json
{ "no_changes": true }
```
→ checksum unchanged. Output `NO_NEW_MESSAGES` and stop — do not spend tokens on parsing.

```json
{
  "checksum": "e3b0c44...",
  "messages": [
    { "id": 32101, "text": "...", "datetime": "2025-03-15T10:05:00+04:00", "url": "..." },
    { "id": 32102, "text": "...", "datetime": "2025-03-15T10:20:00+04:00", "url": "..." }
  ]
}
```
→ messages changed. Proceed to Step 4. Save `checksum` in Step 5.

### Step 4 — Analyze each message

Source messages are in Russian. For each message, determine:

1. **Is the configured address affected?**
   Match the street name and house number from `config.address` against the
   message text using fuzzy normalization (see Address matching rules below).
   If the message mentions only a district (no streets), compare it against
   `config.district`.

2. **Outage type**: `planned` / `emergency` / `restoration` / `unknown`

3. **Timing**: extract start time and estimated restoration if present.

Use your own language understanding — messages are in Russian and Armenian.
Do NOT call an external API for this step; analyze inline.

### Step 5 — Persist new state

Update state with the highest message ID, current timestamp, and new checksum.

```bash
python3 -c "
import json, pathlib
p = pathlib.Path('~/.openclaw/workspace/.blackouts-state.json').expanduser()
state = json.loads(p.read_text()) if p.exists() else {}
state['last_message_id'] = MAX_ID_HERE
state['last_check'] = 'ISO_NOW_HERE'
state['messages_checksum'] = 'CHECKSUM_FROM_STEP_3'
p.write_text(json.dumps(state, ensure_ascii=False, indent=2))
"
```

### Step 6 — Report

Compose the notification in the language specified by `config.language`
(default: `"en"`). Translate the summary and labels — keep street names and
district names in their original form for clarity.

**If any message affects the address:**

For `"en"` (English, default):
```
⚡ OUTAGE AFFECTS YOUR ADDRESS

📍 Address: <address>
📋 Type: Planned maintenance / Emergency / Restoration
🏙 Districts: ...
🗺 Streets: ...
🕐 Start: ...
🔧 Estimated restoration: ...

💬 <brief summary>
🔗 t.me/ArmeniaBlackouts/<message_id>
```

For `"ru"` (Russian):
```
⚡ ОТКЛЮЧЕНИЕ ЗАТРАГИВАЕТ ВАШ АДРЕС

📍 Адрес: <address>
📋 Тип: Плановые работы / Авария / Восстановление
🏙 Районы: ...
🗺 Улицы: ...
🕐 Начало: ...
🔧 Ожидаемое восстановление: ...

💬 <краткое резюме>
🔗 t.me/ArmeniaBlackouts/<message_id>
```

For `"hy"` (Armenian) — use the same emoji-prefixed structure but compose
all labels and summary text in fluent Armenian script. Do not transliterate.
Translate each label naturally: Address, Type, Districts, Streets, Start,
Estimated restoration. Keep street/district proper names in their original form.

**If no messages affect the address:**

| Language | Output |
|----------|--------|
| `en` | `✅ No new outages for your address. Messages checked: N` |
| `ru` | `✅ Новых отключений по вашему адресу нет. Проверено сообщений: N` |
| `hy` | Equivalent message in fluent Armenian script |

## Address matching rules

Messages mix Russian, Armenian, and transliteration. Apply these rules:

- `Баграмяна` = `Baghramyan` = `Bagr.`
- `Комитаса` = `Komitasi`
- District names (Russian / English): Кентрон/Kentron, Арабкир/Arabkir,
  Малатия/Malatia, Норк/Nork, Шенгавит/Shengavit, Давидашен/Davtashen,
  Аван/Avan, Эребуни/Erebuni, Нубарашен/Nubarashen, Канакер-Зейтун/Kanaker-Zeytun,
  Ачапняк/Achapnyak
- House ranges: `15-25` means houses 15 through 25; `12, 14, 16` means exactly
  those houses; a single `15` means house 15 only
- If only a district is mentioned (no street) → compare against `config.district`;
  if it matches → `affected=true, uncertainty=true`
- If street matches but house number is outside the range → `affected=false`

## Config file format

`~/.openclaw/skills/armenia-blackouts/config.json`:

```json
{
  "address": "Baghramyan 24, Yerevan",
  "district": "Arabkir",
  "language": "en"
}
```

- `district` — required for matching district-only announcements

Supported `language` values:
- `"en"` — English (default if omitted)
- `"ru"` — Russian
- `"hy"` — Armenian
