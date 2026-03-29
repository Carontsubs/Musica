#!/usr/bin/env python3
"""
Monitor de concerts d'Elikapowski a menys de 35km de Barcelona.
Usa l'API GraphQL de Resident Advisor (ra.co).

Instal·lació:
    pip install requests geopy

Ús:
    python elikapowski_monitor_v2.py            # Consulta immediata
    python elikapowski_monitor_v2.py --watch    # Comprova cada X hores
"""

import requests
import argparse
import time
from datetime import datetime, date
from geopy.distance import geodesic
import os
from dotenv import load_dotenv #Importem la funció per carregar .env

load_dotenv()

TELEGRAM_TOKEN  = os.getenv("TOKEN_TELEGRAM")
TELEGRAM_CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(missatge: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"{R}⚠️  Variables TELEGRAM_TOKEN o TELEGRAM_CHAT_ID no definides.{X}")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": missatge,
        "parse_mode": "HTML"
    }, timeout=10)



# ─── Configuració ─────────────────────────────────────────────────────────────

ARTIST_NAME = "Elikapowski"
ARTIST_ID   = "164268"
ARTIST_SLUG = "elikapowski"
RA_URL      = "https://ra.co/graphql"
BARCELONA = (41.4794, 2.3201)   #En si son les coordenades de Masnou
MAX_KM      = 35
CHECK_HOURS = 6

# ─── Colors terminal ──────────────────────────────────────────────────────────

G = "\033[92m"; Y = "\033[93m"; R = "\033[91m"
C = "\033[96m"; B = "\033[1m";  X = "\033[0m"

# ─── Query GraphQL ────────────────────────────────────────────────────────────

QUERY = """
query($id: ID!) {
  artist(id: $id) {
    name
    events(type: FROMDATE, limit: 50) {
      id
      title
      date
      startTime
      contentUrl
      venue {
        name
        address
        location { latitude longitude }
        area {
          name
          country { name }
        }
      }
    }
  }
}
"""

# ─── Funcions ─────────────────────────────────────────────────────────────────

def fetch_events() -> list[dict]:
    headers = {
        "Content-Type": "application/json",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:148.0) "
            "Gecko/20100101 Firefox/148.0"
        ),
        "Referer": f"https://ra.co/dj/{ARTIST_SLUG}",
        "Origin": "https://ra.co",
    }
    r = requests.post(
        RA_URL,
        json={"query": QUERY, "variables": {"id": ARTIST_ID}},
        headers=headers,
        timeout=15,
    )
    r.raise_for_status()
    data = r.json()

    if "errors" in data:
        raise ValueError(f"Error GraphQL: {data['errors']}")

    events = data.get("data", {}).get("artist", {}).get("events", [])

    # Filtrem events passats (FROMDATE de vegades inclou passats)
    today = date.today().isoformat()
    return [ev for ev in events if (ev.get("date") or "")[:10] >= today]


def distance_from_barcelona(event: dict) -> float | None:
    location = (event.get("venue") or {}).get("location") or {}
    lat = location.get("latitude")
    lon = location.get("longitude")
    if lat is None or lon is None:
        return None
    try:
        return geodesic(BARCELONA, (float(lat), float(lon))).km
    except Exception:
        return None
def format_preu(event: dict) -> str:
    cost = event.get("cost")
    if cost is None or cost == "":
        return "—"
    if str(cost).strip() == "0":
        return "Gratuït"
    return f"{cost}"


def format_event(event: dict, km: float) -> str:
    venue  = event.get("venue") or {}
    area   = venue.get("area") or {}
    hora    = (event.get("startTime") or "")[11:16]
    pais   = (area.get("country") or {}).get("name", "?")
    ciutat = area.get("name", "?")
    date_s = (event.get("date") or "")[:10]
    titol  = event.get("title") or ARTIST_NAME
    lloc   = venue.get("name", "?")
    url    = f"https://ra.co{event.get('contentUrl', '')}"
    preu   = format_preu(event)

    return (
        f"  {B}📅 {date_s}  {hora}{X}  —  {round(km)} km de Masnou\n"
        f"     Event:    {titol}\n"
        f"     Hora:     {hora}h\n"
        f"     Lloc:     {lloc}\n"
        f"     Ciutat:   {ciutat}, {pais}\n"
        f"     Preu:     {preu}\n"
        f"     Entrades: {C}{url}{X}"
    )


def check_concerts() -> list:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{B}{'─'*55}{X}")
    print(f"{B}🎵 {ARTIST_NAME} — Concerts a {MAX_KM}km de Barcelona{X}")
    print(f"   Consulta: {now}")
    print(f"{B}{'─'*55}{X}\n")

    print(f"{Y}▶ Consultant Resident Advisor (GraphQL)...{X}")
    events = fetch_events()
    print(f"   {len(events)} concerts futurs trobats.\n")

    propers = []
    for ev in events:
        km = distance_from_barcelona(ev)
        if km is not None and km <= MAX_KM:
            propers.append((ev, km))

    propers.sort(key=lambda x: x[0].get("date", ""))

    if propers:
        print(f"{G}{B}🎉 {len(propers)} concert(s) a menys de {MAX_KM}km de Barcelona!{X}\n")
        for ev, km in propers:
            ev_str = format_event(ev, km)
            print(ev_str)
            print()
            send_telegram(ev_str.replace("\033[92m","").replace("\033[93m","").replace("\033[91m","").replace("\033[96m","").replace("\033[1m","").replace("\033[0m",""))
    else:
        print(f"{R}😔 Cap concert d'{ARTIST_NAME} a menys de {MAX_KM}km de Barcelona de moment.{X}")
        print(f"\n   Comprova manualment: {C}https://ra.co/dj/{ARTIST_SLUG}{X}")

    return propers


def watch_mode():
    print(f"{B}👁  Mode vigilant — comprovació cada {CHECK_HOURS}h{X}")
    print("   Prem Ctrl+C per aturar.\n")
    while True:
        try:
            propers = check_concerts()
            if propers:
                print(f"\n{G}✅ Concert proper trobat! Segueixo vigilant...{X}")
        except Exception as e:
            print(f"{R}Error durant la consulta: {e}{X}")

        seg = CHECK_HOURS * 3600
        next_t = datetime.fromtimestamp(time.time() + seg).strftime("%H:%M:%S")
        print(f"\n   Propera comprovació a les {next_t}. Esperant...\n")
        time.sleep(seg)


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=f"Monitor de concerts d'{ARTIST_NAME} a {MAX_KM}km de Barcelona"
    )
    parser.add_argument(
        "--watch", action="store_true",
        help=f"Comprova automàticament cada {CHECK_HOURS} hores"
    )
    args = parser.parse_args()

    try:
        if args.watch:
            watch_mode()
        else:
            check_concerts()
    except KeyboardInterrupt:
        print(f"\n{Y}Aturat.{X}")
