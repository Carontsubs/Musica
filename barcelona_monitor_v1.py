#!/usr/bin/env python3
"""
Monitor d'events de Barcelona per gèneres i paraules clau a Resident Advisor.
Filtra: 2 propers caps de setmana (Dv/Ds/Dg), a partir de les 16h, amb preu.

Instal·lació:
    pip install requests

Ús:
    python barcelona_monitor_v3.py           # Consulta immediata
    python barcelona_monitor_v3.py --watch   # Comprova cada X hores
"""

import requests
import argparse
import time
from datetime import datetime, date, timedelta
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

RA_URL      = "https://ra.co/graphql"
AREA_ID     = 20       # Barcelona a Resident Advisor
CHECK_HOURS = 6
HORA_MIN    = 16       # A partir de les 16h

GENERES = [
    "House",
    "Disco",
    "Nu Disco",
    "Funk / Soul",
    "Afro House",
    "Deep House",
    "Progressive House",
    "Melodic House",
    "Tropical House",
    "Disco House",
]

PARAULES_CLAU = [
    "melodic",
    "tropical",
    "disco house",
    "nu disco",
    "deep house",
    "house music",
    "soulful",
    "funk",
    "soul",
    "groovy",
]

# ─── Colors terminal ──────────────────────────────────────────────────────────

G = "\033[92m"; Y = "\033[93m"; R = "\033[91m"
C = "\033[96m"; B = "\033[1m";  X = "\033[0m"

# ─── Headers ─────────────────────────────────────────────────────────────────

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:148.0) "
        "Gecko/20100101 Firefox/148.0"
    ),
    "Referer": "https://ra.co/events/es/barcelona",
    "Origin": "https://ra.co",
    "x-ra-content-language": "en",
}

# ─── Query ────────────────────────────────────────────────────────────────────

QUERY = """
query($filters: FilterInputDtoInput, $page: Int) {
  eventListings(filters: $filters, pageSize: 50, page: $page) {
    data {
      event {
        id
        title
        date
        startTime
        cost
        isTicketed
        contentUrl
        genres { name }
        venue { name }
        artists { name }
      }
    }
    totalResults
  }
}
"""

# ─── Helpers de dates ─────────────────────────────────────────────────────────

def get_weekend_days() -> set[date]:
    """Retorna els dies Dv/Ds/Dg dels 2 propers caps de setmana."""
    avui = date.today()
    # Dies de la setmana: 0=Dl, 4=Dv, 5=Ds, 6=Dg
    dies_fins_divendres = (4 - avui.weekday()) % 7
    if dies_fins_divendres == 0 and avui.weekday() == 4:
        dies_fins_divendres = 0
    
    # Primer cap de setmana
    primer_divendres = avui + timedelta(days=dies_fins_divendres)
    # Si avui ja és dissabte o diumenge, agafem aquest cap de setmana
    if avui.weekday() == 5:
        primer_divendres = avui - timedelta(days=1)
    elif avui.weekday() == 6:
        primer_divendres = avui - timedelta(days=2)

    dies = set()
    for offset in range(2):      # Dv, Ds, Dg del primer cap de setmana
        dies.add(primer_divendres + timedelta(days=offset))
    
    return dies


def event_hora(event: dict):
    """Retorna l'hora de l'event com a enter, o None si no hi és."""
    start = event.get("startTime") or ""
    try:
        # Format: "2026-03-28T22:00:00.000"
        return int(start[11:13])
    except (ValueError, IndexError):
        return None


def event_data(event: dict):
    """Retorna la data de l'event com a objecte date."""
    d = (event.get("date") or "")[:10]
    try:
        return date.fromisoformat(d)
    except ValueError:
        return None

# ─── Funcions principals ──────────────────────────────────────────────────────

def fetch_all_events() -> list[dict]:
    today = date.today().isoformat()
    all_events = []
    page = 1

    while True:
        r = requests.post(
            RA_URL,
            json={
                "query": QUERY,
                "variables": {
                    "filters": {
                        "areas": {"eq": AREA_ID},
                        "listingDate": {"gte": today},
                    },
                    "page": page,
                }
            },
            headers=HEADERS,
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()

        listings = data.get("data", {}).get("eventListings", {})
        events = [item["event"] for item in listings.get("data", [])]
        total = listings.get("totalResults", 0)

        all_events.extend(events)

        if len(all_events) >= total or not events or page >= 5:
            break
        page += 1

    return all_events


def is_match(event: dict) -> tuple[bool, str]:
    event_genres = [g["name"].lower() for g in event.get("genres", [])]
    for g in GENERES:
        if g.lower() in event_genres:
            return True, f"gènere: {g}"

    titol = (event.get("title") or "").lower()
    for kw in PARAULES_CLAU:
        if kw.lower() in titol:
            return True, f"títol: '{kw}'"

    return False, ""


def format_preu(event: dict) -> str:
    cost = event.get("cost")
    if cost is None or cost == "":
        return "—"
    if str(cost).strip() == "0":
        return "Gratuït"
    return f"{cost}"


def format_event(event: dict, motiu: str) -> str:
    ev_date = event_data(event)
    dia_setmana = ["Dl","Dt","Dc","Dj","Dv","Ds","Dg"][ev_date.weekday()] if ev_date else "?"
    date_s  = str(ev_date) if ev_date else "?"
    hora    = (event.get("startTime") or "")[11:16]
    titol   = event.get("title", "?")
    lloc    = (event.get("venue") or {}).get("name", "?")
    genres  = ", ".join(g["name"] for g in event.get("genres", []))
    artists = ", ".join(a["name"] for a in (event.get("artists") or [])[:4])
    url     = f"https://ra.co{event.get('contentUrl', '')}"
    preu    = format_preu(event)
    return (
        f"  {B}📅 {dia_setmana} {date_s}  {hora}{X}  [{Y}{motiu}{X}]\n"
        f"     Hora:     {hora}h\n"
        f"     Event:    {titol}\n"
        f"     Lloc:     {lloc}\n"
        f"     Gèneres:  {genres if genres else '—'}\n"
        f"     Artistes: {artists if artists else '—'}\n"
        f"     Preu:     {preu}\n"
        f"     Info:     {C}{url}{X}"
        
    )


def check_events() -> list:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    weekend_days = get_weekend_days()
    weekend_str = ", ".join(sorted(str(d) for d in weekend_days))

    print(f"\n{B}{'─'*55}{X}")
    print(f"{B}🎵 Events Barcelona — House / Disco / Nu Disco{X}")
    print(f"   Caps de setmana: {weekend_str}")
    print(f"   Hora mínima: {HORA_MIN}:00h")
    print(f"   Consulta: {now}")
    print(f"{B}{'─'*55}{X}\n")

    print(f"{Y}▶ Consultant Resident Advisor (Barcelona)...{X}")
    all_events = fetch_all_events()
    print(f"   {len(all_events)} events totals trobats.")

    matching = []
    for ev in all_events:
        # Filtre cap de setmana
        ev_d = event_data(ev)
        if ev_d not in weekend_days:
            continue

        # Filtre hora
        hora = event_hora(ev)
        if hora is not None and (hora < HORA_MIN or hora >= 22):
            continue

        # Filtre gènere / paraula clau
        ok, motiu = is_match(ev)
        if ok:
            matching.append((ev, motiu))

    matching.sort(key=lambda x: (x[0].get("date", ""), x[0].get("startTime", "")))  
    print(f"   {len(matching)} events coincideixen.\n")

    if matching:
        print(f"{G}{B}🎉 {len(matching)} event(s) trobats!{X}\n")
        for ev, motiu in matching:
            ev_data_str = format_event(ev, motiu)
            print(ev_data_str)
            print()
            send_telegram(ev_data_str.replace("\033[92m","").replace("\033[93m","").replace("\033[91m","").replace("\033[96m","").replace("\033[1m","").replace("\033[0m",""))    
        else:
            print(f"{R}😔 Cap event coincident als propers caps de setmana.{X}")
            print(f"\n   Comprova manualment: {C}https://ra.co/events/es/barcelona{X}")

    return matching


def watch_mode():
    print(f"{B}👁  Mode vigilant — comprovació cada {CHECK_HOURS}h{X}")
    print("   Prem Ctrl+C per aturar.\n")
    while True:
        try:
            check_events()
        except Exception as e:
            print(f"{R}Error durant la consulta: {e}{X}")

        seg = CHECK_HOURS * 3600
        next_t = datetime.fromtimestamp(time.time() + seg).strftime("%H:%M:%S")
        print(f"\n   Propera comprovació a les {next_t}. Esperant...\n")
        time.sleep(seg)


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Monitor d'events a Barcelona per gènere, cap de setmana i hora (RA)"
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