#!/usr/bin/env python3
"""
Monitor de concerts de Lost Frequencies a menys de 200km de Barcelona.
Usa l'API de Bandsintown amb l'app_id oficial de la web de l'artista.

Instal·lació:
    pip install requests geopy

Ús:
    python lost_frequencies_monitor_v3.py           # Consulta immediata
    python lost_frequencies_monitor_v3.py --watch   # Comprova cada X hores
"""

import requests
import argparse
import json
import re
import time
from datetime import datetime
from geopy.distance import geodesic

# ─── Configuració ─────────────────────────────────────────────────────────────

ARTIST      = "Lost Frequencies"
APP_ID      = "js_lostfrequencies.com"   # app_id oficial del widget de la web
API_URL     = (
    f"https://rest.bandsintown.com/V3.1/artists/Lost%20Frequencies/events/"
    f"?app_id={APP_ID}&callback=bitJsonp_callback"
)
BARCELONA   = (41.3851, 2.1734)
MAX_KM      = 200
CHECK_HOURS = 6

# ─── Colors terminal ──────────────────────────────────────────────────────────

G = "\033[92m"; Y = "\033[93m"; R = "\033[91m"
C = "\033[96m"; B = "\033[1m";  X = "\033[0m"

# ─── Funcions ─────────────────────────────────────────────────────────────────

def fetch_events() -> list[dict]:
    """Obté concerts via Bandsintown amb l'app_id oficial de la web."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:148.0) "
            "Gecko/20100101 Firefox/148.0"
        ),
        "Referer": "https://lostfrequencies.com/",
    }
    r = requests.get(API_URL, headers=headers, timeout=15)
    r.raise_for_status()

    # La resposta és JSONP: bitJsonp_callback([...])
    # Extraiem el JSON interior eliminant el wrapper de la funció
    text = r.text.strip()
    match = re.match(r"^[^(]+\((.*)\)\s*;?\s*$", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))

    # Si per algun motiu respon JSON net, ho intentem directament
    return r.json()


def distance_from_barcelona(event: dict) -> float | None:
    venue = event.get("venue", {})
    lat   = venue.get("latitude")
    lon   = venue.get("longitude")
    if not lat or not lon:
        return None
    try:
        return geodesic(BARCELONA, (float(lat), float(lon))).km
    except Exception:
        return None


def format_event(event: dict, km: float) -> str:
    venue  = event.get("venue", {})
    date   = event.get("datetime", "")[:10]
    lloc   = venue.get("name", "?")
    ciutat = venue.get("city", "?")
    pais   = venue.get("country", "?")
    url    = event.get("url", "")
    return (
        f"  {B}📅 {date}{X}  —  {round(km)} km de Barcelona\n"
        f"     Lloc:   {lloc}\n"
        f"     Ciutat: {ciutat}, {pais}\n"
        f"     Entrades: {C}{url}{X}"
    )


def check_concerts() -> list:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{B}{'─'*55}{X}")
    print(f"{B}🎵 {ARTIST} — Concerts a {MAX_KM}km de Barcelona{X}")
    print(f"   Consulta: {now}")
    print(f"{B}{'─'*55}{X}\n")

    print(f"{Y}▶ Consultant Bandsintown (app_id oficial)...{X}")
    events = fetch_events()
    print(f"   {len(events)} concerts totals trobats.\n")

    propers = []
    for ev in events:
        km = distance_from_barcelona(ev)
        if km is not None and km <= MAX_KM:
            propers.append((ev, km))

    propers.sort(key=lambda x: x[0].get("datetime", ""))

    if propers:
        print(f"{G}{B}🎉 {len(propers)} concert(s) a menys de {MAX_KM}km de Barcelona!{X}\n")
        for ev, km in propers:
            print(format_event(ev, km))
            print()
    else:
        print(f"{R}😔 Cap concert a menys de {MAX_KM}km de Barcelona de moment.{X}")
        print(f"\n   Comprova manualment: {C}https://lostfrequencies.com/tour-dates/{X}")

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
        description=f"Monitor de concerts de {ARTIST} a {MAX_KM}km de Barcelona"
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
