#!/usr/bin/env python3
"""
Monitor d'events de Barcelona a Dice.fm.
Filtra: 2 propers caps de setmana (Dv/Ds/Dg), de 16h a 22h.

Instal·lació:
    pip install requests python-dotenv

Ús:
    python barcelona_monitor_dice.py           # Consulta immediata
    python barcelona_monitor_dice.py --watch   # Comprova cada X hores
"""

import requests
import re
import json
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

DICE_URL    = "https://dice.fm/browse/barcelona-5d8cefe1e3e6e374e99e8cbe"
CHECK_HOURS = 6
HORA_MIN    = 16
HORA_MAX    = 22

# ─── Colors terminal ──────────────────────────────────────────────────────────

G = "\033[92m"; Y = "\033[93m"; R = "\033[91m"
C = "\033[96m"; B = "\033[1m";  X = "\033[0m"

# ─── Headers ─────────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en",
}

# ─── Helpers de dates ─────────────────────────────────────────────────────────

def get_weekend_days() -> set:
    avui = date.today()
    if avui.weekday() == 5:
        primer_divendres = avui - timedelta(days=1)
    elif avui.weekday() == 6:
        primer_divendres = avui - timedelta(days=2)
    else:
        primer_divendres = avui + timedelta(days=(4 - avui.weekday()) % 7)

    dies = set()
    for offset in range(2):   # Dv (0), Ds (1) — igual que RA
        dies.add(primer_divendres + timedelta(days=offset))
    return dies


def parse_event_start(event: dict):
    try:
        dt_str  = event["dates"]["event_start_date"]
        ev_date = date.fromisoformat(dt_str[:10])
        hora    = int(dt_str[11:13])
        return ev_date, hora
    except (KeyError, ValueError, TypeError):
        return None, None

# ─── Fetch ────────────────────────────────────────────────────────────────────

def fetch_all_events() -> list:
    r = requests.get(DICE_URL, headers=HEADERS, timeout=20)
    r.raise_for_status()
    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>',
        r.text, re.DOTALL
    )
    if not match:
        raise RuntimeError("No s'ha trobat __NEXT_DATA__ a la pàgina de Dice.fm")
    data = json.loads(match.group(1))
    return data["props"]["pageProps"].get("events", [])

# ─── Format ──────────────────────────────────────────────────────────────────

def format_preu(event: dict) -> str:
    price       = event.get("price") or {}
    amount      = price.get("amount")
    amount_from = price.get("amount_from")
    currency    = price.get("currency", "EUR")
    val = amount_from if amount is None else amount
    if val is None:
        return "—"
    if val == 0:
        return "Gratuït"
    return f"{val / 100:.0f} {currency}"


def format_event(event: dict) -> str:
    ev_date, hora = parse_event_start(event)
    dia_setmana   = ["Dl","Dt","Dc","Dj","Dv","Ds","Dg"][ev_date.weekday()] if ev_date else "?"
    date_s        = str(ev_date) if ev_date else "?"
    hora_s        = f"{hora:02d}:00" if hora is not None else "?"
    titol         = event.get("name", "?")
    lloc          = (event.get("venues") or [{}])[0].get("name", "?")
    artistes      = ", ".join(
        a.get("name", "") for a in
        (event.get("summary_lineup") or {}).get("top_artists", [])[:4]
    )
    tags  = ", ".join(t.get("title", "") for t in (event.get("tags_types") or []))
    preu  = format_preu(event)
    perm  = event.get("perm_name", "")
    url   = f"https://dice.fm/event/{perm}" if perm else "https://dice.fm"

    return (
        f"  {B}📅 {dia_setmana} {date_s}  {hora_s}{X}\n"
        f"     Event:    {titol}\n"
        f"     Lloc:     {lloc}\n"
        f"     Tags:     {tags if tags else '—'}\n"
        f"     Artistes: {artistes if artistes else '—'}\n"
        f"     Preu:     {preu}\n"
        f"     Info:     {C}{url}{X}"
    )


def strip_colors(text: str) -> str:
    for code in ["\033[92m","\033[93m","\033[91m","\033[96m","\033[1m","\033[0m"]:
        text = text.replace(code, "")
    return text

# ─── Check principal ──────────────────────────────────────────────────────────

def check_events() -> list:
    now          = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    weekend_days = get_weekend_days()
    weekend_str  = ", ".join(sorted(str(d) for d in weekend_days))

    print(f"\n{B}{'─'*55}{X}")
    print(f"{B}🎵 Events Barcelona — Tarda (Dice.fm){X}")
    print(f"   Caps de setmana: {weekend_str}")
    print(f"   Hora: {HORA_MIN}:00h – {HORA_MAX}:00h")
    print(f"   Consulta: {now}")
    print(f"{B}{'─'*55}{X}\n")

    print(f"{Y}▶ Consultant Dice.fm (Barcelona)...{X}")
    all_events = fetch_all_events()
    print(f"   {len(all_events)} events totals trobats.")

    matching = []
    for ev in all_events:
        ev_date, hora = parse_event_start(ev)
        if ev_date not in weekend_days:
            continue
        if hora is None or hora < HORA_MIN or hora >= HORA_MAX:
            continue
        matching.append(ev)

    matching.sort(key=lambda x: (
        str(parse_event_start(x)[0] or ""),
        parse_event_start(x)[1] or 0
    ))

    print(f"   {len(matching)} events coincideixen.\n")

    if matching:
        print(f"{G}{B}🎉 {len(matching)} event(s) trobats!{X}\n")
        for ev in matching:
            ev_str = format_event(ev)
            print(ev_str)
            print()
            send_telegram(strip_colors(ev_str))
    else:
        print(f"{R}😔 Cap event als propers caps de setmana en horari de tarda.{X}")
        print(f"\n   Comprova manualment: {C}{DICE_URL}{X}")

    return matching


def watch_mode():
    print(f"{B}👁  Mode vigilant — comprovació cada {CHECK_HOURS}h{X}")
    print("   Prem Ctrl+C per aturar.\n")
    while True:
        try:
            check_events()
        except Exception as e:
            print(f"{R}Error durant la consulta: {e}{X}")
        seg    = CHECK_HOURS * 3600
        next_t = datetime.fromtimestamp(time.time() + seg).strftime("%H:%M:%S")
        print(f"\n   Propera comprovació a les {next_t}. Esperant...\n")
        time.sleep(seg)


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Monitor d'events a Barcelona de tarda els caps de setmana (Dice.fm)"
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