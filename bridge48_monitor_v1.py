#!/usr/bin/env python3
"""
Monitor d'events de tarda al Bridge 48 (Barcelona).
Cerca events que comencin entre les 16:00 i les 22:00,
dins dels propers 2 caps de setmana a partir d'avui.

Instal·lació:
    pip install requests python-dotenv

Ús:
    python bridge48_monitor.py            # Consulta immediata
    python bridge48_monitor.py --watch    # Comprova cada X hores
"""

import requests
import argparse
import time
from datetime import datetime, date, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN   = os.getenv("TOKEN_TELEGRAM")
TELEGRAM_CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(missatge: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"{R}⚠️  Variables TOKEN_TELEGRAM o CHAT_ID no definides.{X}")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": missatge,
        "parse_mode": "HTML"
    }, timeout=10)


# ─── Configuració ─────────────────────────────────────────────────────────────

VENUE_ID        = "178344"          # Bridge 48 a Resident Advisor
HORA_MIN        = "16:00"           # Hora d'inici mínima (inclosa)
HORA_MAX        = "22:00"           # Hora d'inici màxima (inclosa)
NUM_WEEKENDS    = 2                 # Quants caps de setmana cap endavant mirar
CHECK_HOURS     = 6                 # Interval en mode --watch
RA_URL          = "https://ra.co/graphql"

# ─── Colors terminal ──────────────────────────────────────────────────────────

G = "\033[92m"; Y = "\033[93m"; R = "\033[91m"
C = "\033[96m"; B = "\033[1m";  X = "\033[0m"

# ─── Query GraphQL ────────────────────────────────────────────────────────────

QUERY_VENUE = """
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
        area {
          name
          country { name }
        }
      }
    }
  }
}
"""


def strip_ansi(text: str) -> str:
    for code in [G, Y, R, C, B, X]:
        text = text.replace(code, "")
    return text


def get_next_two_weekends() -> list[date]:
    """Retorna totes les dates (dissabte i diumenge) dels propers NUM_WEEKENDS caps de setmana."""
    today = date.today()
    # Troba el proper dissabte (weekday 5)
    days_until_saturday = (5 - today.weekday()) % 7
    if days_until_saturday == 0:
        days_until_saturday = 0  # avui és dissabte, l'incloem

    weekend_dates = []
    for i in range(NUM_WEEKENDS):
        saturday = today + timedelta(days=days_until_saturday + i * 7)
        sunday   = saturday + timedelta(days=1)
        weekend_dates.extend([saturday, sunday])
    return weekend_dates


def is_weekend_date(d: str, weekend_dates: list[date]) -> bool:
    """Comprova si la data de l'event (string YYYY-MM-DD) és un dels caps de setmana."""
    try:
        ev_date = date.fromisoformat(d[:10])
        return ev_date in weekend_dates
    except (ValueError, TypeError):
        return False


def is_tarda(start_time: str) -> bool:
    """
    Retorna True si l'hora d'inici de l'event és entre HORA_MIN i HORA_MAX (inclosos).
    start_time és un string ISO com "2025-04-05T18:00:00.000Z" o "18:00".
    """
    if not start_time:
        return False
    # Extreu HH:MM
    try:
        hora_part = start_time[11:16] if "T" in start_time else start_time[:5]
        return HORA_MIN <= hora_part <= HORA_MAX
    except Exception:
        return False


def fetch_events() -> tuple[str, list[dict]]:
    """Fa la crida GraphQL i retorna (nom_venue, llista_events_futurs)."""
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:149.0) Gecko/20100101 Firefox/149.0",
        "Referer": f"https://ra.co/clubs/{VENUE_ID}",
        "Origin": "https://ra.co",
    }
    r = requests.post(
        RA_URL,
        json={
            "query": QUERY_VENUE,
            "variables": {"id": VENUE_ID},
            "operationName": "GET_VENUE_EVENTS"
        },
        headers=headers,
        timeout=15,
    )
    r.raise_for_status()
    data = r.json()

    if "errors" in data:
        raise ValueError(f"Error GraphQL: {data['errors']}")

    venue_data = data.get("data", {}).get("venue", {})
    venue_name = venue_data.get("name", "Bridge 48")
    events     = venue_data.get("events", []) or []

    # Només events futurs (a partir d'avui)
    today = date.today().isoformat()
    future = [ev for ev in events if (ev.get("date") or "")[:10] >= today]
    return venue_name, future


def format_preu(event: dict) -> str:
    cost = event.get("cost")
    if cost is None or str(cost).strip() == "":
        return "—"
    if str(cost).strip() == "0":
        return "Gratuït"
    return str(cost)


def format_event(event: dict) -> str:
    venue  = event.get("venue") or {}
    area   = venue.get("area") or {}
    start  = event.get("startTime") or ""
    hora   = start[11:16] if "T" in start else start[:5]
    pais   = (area.get("country") or {}).get("name", "?")
    ciutat = area.get("name", "?")
    date_s = (event.get("date") or "")[:10]
    # Dia de la setmana en català
    try:
        ev_date = date.fromisoformat(date_s)
        DIES = ["Dilluns","Dimarts","Dimecres","Dijous","Divendres","Dissabte","Diumenge"]
        dia_setmana = DIES[ev_date.weekday()]
    except Exception:
        dia_setmana = ""
    titol  = event.get("title") or "Sense títol"
    lloc   = venue.get("name", "Bridge 48")
    adreça = venue.get("address", "")
    url    = f"https://ra.co{event.get('contentUrl', '')}"
    preu   = format_preu(event)

    return (
        f"  {B}📅 {dia_setmana}, {date_s}  ·  {hora}h{X}\n"
        f"     Títol:    {titol}\n"
        f"     Lloc:     {lloc}\n"
        f"     Adreça:   {adreça}\n"
        f"     Ciutat:   {ciutat}, {pais}\n"
        f"     Preu:     {preu}\n"
        f"     Entrades: {C}{url}{X}"
    )


def check_events() -> list:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    weekend_dates = get_next_two_weekends()
    weekend_str = ", ".join(d.strftime("%d/%m") for d in weekend_dates)

    print(f"\n{B}{'─'*58}{X}")
    print(f"{B}🌉 Bridge 48 — Events de tarda (cap de setmana){X}")
    print(f"   Horari filtrat: {HORA_MIN}h – {HORA_MAX}h")
    print(f"   Caps de setmana: {weekend_str}")
    print(f"   Consulta: {now}")
    print(f"{B}{'─'*58}{X}\n")

    print(f"{Y}▶ Consultant Resident Advisor (GraphQL)...{X}")
    venue_name, all_events = fetch_events()
    print(f"   Venue: {venue_name}  (ID {VENUE_ID})")
    print(f"   {len(all_events)} events futurs trobats.\n")

    # Filtre 1: cap de setmana
    weekend_events = [ev for ev in all_events if is_weekend_date(ev.get("date", ""), weekend_dates)]
    print(f"   → {len(weekend_events)} als propers {NUM_WEEKENDS} caps de setmana ({weekend_str}).")

    # Filtre 2: horari de tarda
    tarda_events = [ev for ev in weekend_events if is_tarda(ev.get("startTime", ""))]
    print(f"   → {len(tarda_events)} comencen entre {HORA_MIN}h i {HORA_MAX}h.\n")

    # Ordenem per data
    tarda_events.sort(key=lambda ev: ev.get("date", ""))

    if tarda_events:
        print(f"{G}{B}🎉 {len(tarda_events)} event(s) de tarda trobat(s)!{X}\n")
        for ev in tarda_events:
            ev_str = format_event(ev)
            print(ev_str)
            print()
            send_telegram(strip_ansi(ev_str))
    else:
        print(f"{R}😔 Cap event de tarda a Bridge 48 els propers {NUM_WEEKENDS} caps de setmana.{X}")
        print(f"\n   Comprova manualment: {C}https://ra.co/clubs/{VENUE_ID}{X}")

    return tarda_events


def watch_mode():
    print(f"{B}👁  Mode vigilant — comprovació cada {CHECK_HOURS}h{X}")
    print("   Prem Ctrl+C per aturar.\n")
    while True:
        try:
            events = check_events()
            if events:
                print(f"\n{G}✅ Events trobats! Segueixo vigilant...{X}")
        except Exception as e:
            print(f"{R}Error durant la consulta: {e}{X}")

        seg = CHECK_HOURS * 3600
        next_t = datetime.fromtimestamp(time.time() + seg).strftime("%H:%M:%S")
        print(f"\n   Propera comprovació a les {next_t}. Esperant...\n")
        time.sleep(seg)


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=f"Monitor d'events de tarda al Bridge 48 ({HORA_MIN}–{HORA_MAX}h), "
                    f"propers {NUM_WEEKENDS} caps de setmana"
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
            check_events()
    except KeyboardInterrupt:
        print(f"\n{Y}Aturat.{X}")