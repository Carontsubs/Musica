#!/usr/bin/env python3
"""
Monitor d'events del club (venue ID 207515) a Resident Advisor.
Filtra events de divendres i dissabte dels propers 2 caps de setmana
que acabin com a molt tard a les 03:00h de la matinada.

Instal·lació:
    pip install requests python-dotenv

Ús:
    python club_207515_monitor.py            # Consulta immediata
    python club_207515_monitor.py --watch    # Comprova cada X hores
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

VENUE_ID        = "207515"    # ID del club a Resident Advisor
HORA_FI_MAX     = "03:00"     # Hora de fi màxima (les 03:00 de la matinada)
NUM_WEEKENDS    = 2           # Quants caps de setmana cap endavant mirar
CHECK_HOURS     = 6           # Interval en mode --watch
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
      endTime
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
    """
    Retorna les dates de divendres i dissabte dels propers NUM_WEEKENDS caps de setmana.
    Dissabte = weekday 5, Divendres = weekday 4.
    """
    today = date.today()
    # Troba el proper divendres (weekday 4)
    days_until_friday = (4 - today.weekday()) % 7

    weekend_dates = []
    for i in range(NUM_WEEKENDS):
        friday   = today + timedelta(days=days_until_friday + i * 7)
        saturday = friday + timedelta(days=1)
        weekend_dates.extend([friday, saturday])
    return weekend_dates


def is_target_date(d: str, target_dates: list[date]) -> bool:
    try:
        return date.fromisoformat(d[:10]) in target_dates
    except (ValueError, TypeError):
        return False


def acaba_a_temps(end_time: str) -> bool:
    """
    Retorna True si l'hora de fi de l'event és <= HORA_FI_MAX (03:00).
    endTime pot ser un ISO string com "2025-04-05T03:00:00.000Z" o "03:00".
    Si no hi ha endTime, s'inclou l'event (no el podem descartar per falta de dades).
    """
    if not end_time:
        return True  # Sense dades d'hora de fi, l'incloem
    try:
        hora_part = end_time[11:16] if "T" in end_time else end_time[:5]
        return hora_part <= HORA_FI_MAX
    except Exception:
        return True


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
    venue_name = venue_data.get("name", f"Club {VENUE_ID}")
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


def format_hora(time_str: str) -> str:
    if not time_str:
        return "?"
    return time_str[11:16] if "T" in time_str else time_str[:5]


def format_event(event: dict) -> str:
    venue   = event.get("venue") or {}
    area    = venue.get("area") or {}
    start   = event.get("startTime") or ""
    end     = event.get("endTime") or ""
    hora_ini = format_hora(start)
    hora_fi  = format_hora(end) if end else "?"
    pais    = (area.get("country") or {}).get("name", "?")
    ciutat  = area.get("name", "?")
    date_s  = (event.get("date") or "")[:10]
    try:
        ev_date = date.fromisoformat(date_s)
        DIES = ["Dilluns","Dimarts","Dimecres","Dijous","Divendres","Dissabte","Diumenge"]
        dia_setmana = DIES[ev_date.weekday()]
    except Exception:
        dia_setmana = ""
    titol   = event.get("title") or "Sense títol"
    lloc    = venue.get("name", f"Club {VENUE_ID}")
    adreça  = venue.get("address", "")
    url     = f"https://ra.co{event.get('contentUrl', '')}"
    preu    = format_preu(event)

    return (
        f"  {B}📅 {dia_setmana}, {date_s}  ·  {hora_ini}h – {hora_fi}h{X}\n"
        f"     Títol:    {titol}\n"
        f"     Lloc:     {lloc}\n"
        f"     Adreça:   {adreça}\n"
        f"     Ciutat:   {ciutat}, {pais}\n"
        f"     Preu:     {preu}\n"
        f"     Entrades: {C}{url}{X}"
    )


def check_events() -> list:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    target_dates = get_next_two_weekends()
    dates_str = ", ".join(d.strftime("%d/%m (%a)") for d in target_dates)

    print(f"\n{B}{'─'*60}{X}")
    print(f"{B}🎶 Club {VENUE_ID} — Events de divendres i dissabte{X}")
    print(f"   Filtre hora fi:  fins les {HORA_FI_MAX}h")
    print(f"   Dies objectiu:   {dates_str}")
    print(f"   Consulta: {now}")
    print(f"{B}{'─'*60}{X}\n")

    print(f"{Y}▶ Consultant Resident Advisor (GraphQL)...{X}")
    venue_name, all_events = fetch_events()
    print(f"   Venue: {venue_name}  (ID {VENUE_ID})")
    print(f"   {len(all_events)} events futurs trobats.\n")

    # Filtre 1: divendres i dissabtes dels propers 2 caps de setmana
    target_events = [ev for ev in all_events if is_target_date(ev.get("date", ""), target_dates)]
    print(f"   → {len(target_events)} cauen en divendres/dissabte dels propers {NUM_WEEKENDS} caps de setmana.")

    # Filtre 2: hora de fi <= 03:00
    finals = [ev for ev in target_events if acaba_a_temps(ev.get("endTime", ""))]
    print(f"   → {len(finals)} acaben a les {HORA_FI_MAX}h o abans.\n")

    finals.sort(key=lambda ev: ev.get("date", ""))

    if finals:
        print(f"{G}{B}🎉 {len(finals)} event(s) trobat(s)!{X}\n")
        for ev in finals:
            ev_str = format_event(ev)
            print(ev_str)
            print()
            send_telegram(strip_ansi(ev_str))
    else:
        print(f"{R}😔 Cap event trobat amb els filtres aplicats.{X}")
        print(f"\n   Comprova manualment: {C}https://ra.co/clubs/{VENUE_ID}{X}")

    return finals


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
        description=f"Monitor d'events de divendres/dissabte al club {VENUE_ID}, "
                    f"que acabin com a molt tard a les {HORA_FI_MAX}h"
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