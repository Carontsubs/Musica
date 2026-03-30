#!/usr/bin/env python3
"""
Detector de NOUS events Throwback a La Terrrazza.
Executa diàriament (Task Scheduler). Notifica per Telegram
només quan apareix un event que no havia vist abans.

Ús:
    python throwback_new_events.py
"""

import requests
import json
import os
from datetime import date, datetime
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN   = os.getenv("TOKEN_TELEGRAM")
TELEGRAM_CHAT_ID = os.getenv("CHAT_ID")

# ─── Configuració ─────────────────────────────────────────
VENUE_ID   = "3760"
RA_URL     = "https://ra.co/graphql"
KNOWN_FILE = "throwback_known.json"   # IDs ja vistos

G = "\033[92m"; Y = "\033[93m"; R = "\033[91m"
C = "\033[96m"; B = "\033[1m";  X = "\033[0m"

# ─── GraphQL ───────────────────────────────────────────────
QUERY = """
query GET_VENUE_EVENTS($id: ID!) {
  venue(id: $id) {
    name
    events(limit: 50, type: LATEST) {
      id
      title
      date
      startTime
      contentUrl
      cost
      venue {
        name
        area { name country { name } }
      }
    }
  }
}
"""

# ─── Telegram ─────────────────────────────────────────────
def send_telegram(missatge: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"{R}⚠️  Telegram no configurat.{X}")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": missatge,
        "parse_mode": "HTML"
    }, timeout=10)

# ─── Memòria ───────────────────────────────────────────────
def load_known() -> set:
    if not os.path.exists(KNOWN_FILE):
        return set()
    with open(KNOWN_FILE) as f:
        return set(json.load(f))

def save_known(ids: set):
    with open(KNOWN_FILE, "w") as f:
        json.dump(list(ids), f)

# ─── RA ────────────────────────────────────────────────────
def fetch_events() -> list[dict]:
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:149.0) Gecko/20100101 Firefox/149.0",
        "Referer": f"https://ra.co/clubs/{VENUE_ID}",
        "Origin": "https://ra.co",
    }
    r = requests.post(
        RA_URL,
        json={"query": QUERY, "variables": {"id": VENUE_ID}, "operationName": "GET_VENUE_EVENTS"},
        headers=headers,
        timeout=15,
    )
    r.raise_for_status()
    data = r.json()
    if "errors" in data:
        raise ValueError(f"Error GraphQL: {data['errors']}")

    today = date.today().isoformat()
    events = data.get("data", {}).get("venue", {}).get("events", [])
    # Només events futurs amb "throwback" al títol
    return [
        ev for ev in events
        if (ev.get("date") or "")[:10] >= today
        and "throwback" in (ev.get("title") or "").lower()
    ]

# ─── Main ──────────────────────────────────────────────────
def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{B}─── Throwback — detector de nous events ───{X}")
    print(f"    Consulta: {now}\n")

    known = load_known()
    events = fetch_events()
    print(f"    {len(events)} event(s) Throwback futurs a RA.")

    nous = [ev for ev in events if str(ev["id"]) not in known]

    if nous:
        print(f"{G}{B}🎉 {len(nous)} event(s) NOU(S) detectat(s)!{X}\n")
        for ev in nous:
            area  = (ev.get("venue") or {}).get("area", {})
            data_s = (ev.get("date") or "")[:10]
            hora  = (ev.get("startTime") or "")[11:16]
            titol = ev.get("title", "Throwback")
            url   = f"https://ra.co{ev.get('contentUrl', '')}"
            preu  = ev.get("cost") or "—"

            missatge = (
                f"🆕 <b>NOU EVENT THROWBACK!</b>\n"
                f"📅 {data_s} a les {hora}h\n"
                f"🎶 {titol}\n"
                f"📍 {area.get('name','?')}, {(area.get('country') or {}).get('name','?')}\n"
                f"🎟 Preu: {preu}\n"
                f"🔗 {url}"
            )
            print(missatge.replace("<b>","").replace("</b>",""))
            send_telegram(missatge)

        # Guardem els nous IDs
        known.update(str(ev["id"]) for ev in nous)
        save_known(known)
    else:
        print(f"    Cap event nou. Tots ja coneguts.")

    print(f"\n{B}─────────────────────────────────────────────{X}\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"{R}Error: {e}{X}")