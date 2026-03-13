#!/usr/bin/env python3
"""
Fetch new messages from t.me/s/ArmeniaBlackouts.

Reads last_message_id from ~/.openclaw/workspace/.blackouts-state.json
and prints a JSON array of newer messages to stdout.
Called by the OpenClaw agent via exec tool.
"""
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
MAX_MESSAGES = 15


def load_last_id() -> int:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text()).get("last_message_id", 0)
        except Exception:
            pass
    return 0


def fetch_messages(last_id: int) -> list[dict]:
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
        if msg_id <= last_id:
            continue

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
            try:
                dt = time_el["datetime"]
            except Exception:
                dt = None

        messages.append({
            "id": msg_id,
            "text": text,
            "datetime": dt,
            "url": f"https://t.me/{CHANNEL}/{msg_id}",
        })

    messages.sort(key=lambda x: x["id"])
    return messages[:MAX_MESSAGES]


if __name__ == "__main__":
    last_id = load_last_id()
    try:
        msgs = fetch_messages(last_id)
        print(json.dumps(msgs, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
