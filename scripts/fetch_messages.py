#!/usr/bin/env python3
"""
Fetch the last 7 messages from t.me/s/ArmeniaBlackouts.

Compares a SHA-256 checksum of the fetched messages against the stored
checksum in ~/.openclaw/workspace/.blackouts-state.json.

Outputs:
  {"no_changes": true}            — checksum unchanged, skip LLM parsing
  [{"id":..., "text":...}, ...]   — messages changed, includes "checksum" key
Called by the OpenClaw agent via exec tool.
"""
import hashlib
import json
import pathlib
import re
import sys

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print(json.dumps({"error": "Missing deps: pip3 install requests beautifulsoup4"}))
    sys.exit(1)

STATE_FILE = pathlib.Path("~/.openclaw/workspace/.blackouts-state.json").expanduser()
CHANNEL = "ArmeniaBlackouts"
URL = f"https://t.me/s/{CHANNEL}"
MAX_MESSAGES = 7


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {}


def fetch_last_messages() -> list[dict]:
    resp = requests.get(
        URL,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; blackout-monitor/1.0)",
            "Accept-Language": "ru-RU,ru;q=0.9",
        },
        timeout=30,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    messages = []
    for widget in soup.select(".tgme_widget_message"):
        data_post = widget.get("data-post", "")
        m = re.search(r"/(\d+)$", data_post)
        if not m:
            continue
        msg_id = int(m.group(1))

        text_el = widget.select_one(".tgme_widget_message_text")
        if text_el:
            for br in text_el.find_all("br"):
                br.replace_with("\n")
            text = text_el.get_text(separator="", strip=True)
        else:
            text = widget.get_text(separator=" ", strip=True)

        dt = None
        time_el = widget.select_one(".tgme_widget_message_date time")
        if time_el and time_el.get("datetime"):
            dt = time_el["datetime"]

        messages.append({
            "id": msg_id,
            "text": text,
            "datetime": dt,
            "url": f"https://t.me/{CHANNEL}/{msg_id}",
        })

    messages.sort(key=lambda x: x["id"])
    return messages[-MAX_MESSAGES:]


def compute_checksum(messages: list[dict]) -> str:
    raw = "|".join(f"{m['id']}:{m['text']}" for m in messages)
    return hashlib.sha256(raw.encode()).hexdigest()


if __name__ == "__main__":
    state = load_state()
    stored_checksum = state.get("messages_checksum", "")

    try:
        msgs = fetch_last_messages()
        checksum = compute_checksum(msgs)

        if checksum == stored_checksum:
            print(json.dumps({"no_changes": True}))
        else:
            print(json.dumps({"checksum": checksum, "messages": msgs}, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
