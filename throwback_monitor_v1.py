#!/usr/bin/env python3
"""
Monitor de l'event "Throwback - Back to 80s, 90s & 00s" a menys de 35km de Barcelona.
Usa l'API GraphQL de Resident Advisor (ra.co).

Instal·lació:
    pip install requests geopy python-dotenv

Ús:
    python throwback_monitor.py            # Consulta immediata
    python throwback_monitor.py --watch    # Comprova cada X hores
"""

import requests
import argparse
import time
from datetime import datetime, date
from geopy.distance import geodesic
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN   = os.getenv("TOKEN_TELEGRAM")
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

EVENT_KEYWORDS  = ["throwback", "80s", "90s", "00s"]   # Totes han d'aparèixer al títol
BARCELONA       = (41.4794, 2.3201)                    # Coordenades de referència (Masnou)
MAX_KM          = 35
CHECK_HOURS     = 6
RA_URL          = "https://ra.co/graphql"

# ─── Colors terminal ──────────────────────────────────────────────────────────

G = "\033[92m"; Y = "\033[93m"; R = "\033[91m"
C = "\033[96m"; B = "\033[1m";  X = "\033[0m"

# ─── Query GraphQL — cerca d'events per àrea ──────────────────────────────────
# Busquem events a l'àrea de Barcelona i filtrem per títol localment.

PROMOTER_ID = "3760"

QUERY_PROMOTER = """
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

VARIABLES = {
    "indices": ["EVENT"],
    "searchTerm": "Throwback Barcelona"
}

def strip_ansi(text: str) -> str:
    for code in [G, Y, R, C, B, X]:
        text = text.replace(code, "")
    return text


def fetch_events() -> list[dict]:
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:149.0) Gecko/20100101 Firefox/149.0",
        "Referer": f"https://ra.co/promoters/{PROMOTER_ID}",
        "Origin": "https://ra.co",
    }

    r = requests.post(
        RA_URL,
        json={"query": QUERY_PROMOTER, "variables": {"id": PROMOTER_ID}, "operationName": "GET_VENUE_EVENTS"},
        headers=headers,
        timeout=15,
    )
    r.raise_for_status()
    data = r.json()

    if "errors" in data:
        raise ValueError(f"Error GraphQL: {data['errors']}")

    events = data.get("data", {}).get("venue", {}).get("events", [])

    today = date.today().isoformat()
    return [ev for ev in events if (ev.get("date") or "")[:10] >= today]

def is_throwback_event(event: dict) -> bool:
    """Retorna True si el títol conté totes les paraules clau (case-insensitive)."""
    title = (event.get("title") or "").lower()
    return all(kw.lower() in title for kw in EVENT_KEYWORDS)


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
    hora   = (event.get("startTime") or "")[11:16]
    pais   = (area.get("country") or {}).get("name", "?")
    ciutat = area.get("name", "?")
    date_s = (event.get("date") or "")[:10]
    titol  = event.get("title") or "Throwback"
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
    print(f"{B}🕺 Throwback — Back to 80s, 90s & 00s{X}")
    print(f"{B}   Events a {MAX_KM}km de Masnou/Barcelona{X}")
    print(f"   Consulta: {now}")
    print(f"{B}{'─'*55}{X}\n")

    print(f"{Y}▶ Consultant Resident Advisor (GraphQL)...{X}")
    all_events = fetch_events()
    print(f"   {len(all_events)} events futurs a Barcelona trobats.")

    # Filtre per títol
    throwback_events = [ev for ev in all_events if is_throwback_event(ev)]
    print(f"   {len(throwback_events)} coincideixen amb 'Throwback 80s/90s/00s'.\n")

    # Filtre per distància
    propers = []
    for ev in throwback_events:
        km = distance_from_barcelona(ev)
        if km is None or km <= MAX_KM:
            # Si no té coordenades, l'incloem igualment (pot ser Barcelona)
            km_display = km if km is not None else 0.0
            propers.append((ev, km_display))

    propers.sort(key=lambda x: x[0].get("date", ""))

    if propers:
        print(f"{G}{B}🎉 {len(propers)} event(s) Throwback trobat(s)!{X}\n")
        for ev, km in propers:
            ev_str = format_event(ev, km)
            print(ev_str)
            print()
            send_telegram(strip_ansi(ev_str))
    else:
        print(f"{R}😔 Cap event 'Throwback' trobat a menys de {MAX_KM}km de moment.{X}")
        print(f"\n   Comprova manualment: {C}https://ra.co/events/es/barcelona{X}")

    return propers


def watch_mode():
    print(f"{B}👁  Mode vigilant — comprovació cada {CHECK_HOURS}h{X}")
    print("   Prem Ctrl+C per aturar.\n")
    while True:
        try:
            propers = check_concerts()
            if propers:
                print(f"\n{G}✅ Event proper trobat! Segueixo vigilant...{X}")
        except Exception as e:
            print(f"{R}Error durant la consulta: {e}{X}")

        seg = CHECK_HOURS * 3600
        next_t = datetime.fromtimestamp(time.time() + seg).strftime("%H:%M:%S")
        print(f"\n   Propera comprovació a les {next_t}. Esperant...\n")
        time.sleep(seg)



# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=f"Monitor de l'event Throwback (80s/90s/00s) a {MAX_KM}km de Barcelona"
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