# Heartbeat Checklist

This file is read by the OpenClaw agent on every heartbeat tick.
Follow these instructions strictly. Do not infer tasks from conversation history.

---

## 1. Armenia Blackouts Check

**Always run this check.**

Use the `armenia-blackouts` skill to check for new power outage messages.

Steps:
1. Read config: `~/.openclaw/skills/armenia-blackouts/config.json`
2. Run the full `armenia-blackouts` skill workflow
3. If any message affects the address → send the formatted notification
   (in the language specified by `config.language`)
4. If nothing new → reply `HEARTBEAT_OK` (no message to user)

**Important**: Always update `messages_checksum` and `last_check` in state, even if no messages affect the address.

---

## 2. Response format

- Outage affecting address → full notification (see skill output format)
- Nothing to report → reply exactly: `HEARTBEAT_OK`
- Error (network/parse failure) → reply: `HEARTBEAT_ERROR: <short reason>`

Do not send greetings, summaries of what you checked, or any other text.
Only send a message if there is something actionable for the user.
