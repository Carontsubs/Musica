#!/usr/bin/env python3
"""
Monitor principal — executa tots els monitors de concerts.

    lost_frequencies_monitor_v4.py  → Lost Frequencies (Bandsintown)
    elikapowski_monitor_v2.py       → Elikapowski (Resident Advisor)
    barcelona_monitor_v3.py         → Events Barcelona per gènere (RA)
    barcelona_monitor_dice.py       → Events Barcelona de tarda (Dice.fm)
    throwback_monitor_v1.py         → Events Throwback (RA)

Instal·lació:
    pip install -r requirements.txt

Ús:
    python monitor.py           # Executa els quatre d'una vegada
    python monitor.py --watch   # Els quatre en mode vigilant (cada 6h)
"""

import argparse
import time
from datetime import datetime

# ─── Colors terminal ──────────────────────────────────────────────────────────

G = "\033[92m"; Y = "\033[93m"; R = "\033[91m"
C = "\033[96m"; B = "\033[1m";  X = "\033[0m"

CHECK_HOURS = 6

# ─── Importem els monitors ────────────────────────────────────────────────────
try:
    import barcelona_monitor_v1 as bcn
except ImportError:
    bcn = None
    print(f"{R}⚠️  barcelona_monitor_v3.py no trobat.{X}")

try:
    import barcelona_monitor_dice as dice
except ImportError:
    dice = None
    print(f"{R}⚠️  barcelona_monitor_dice.py no trobat.{X}")

try:
    import lost_frequencies_monitor_v4 as lf
except ImportError:
    lf = None
    print(f"{R}⚠️  lost_frequencies_monitor_v4.py no trobat.{X}")

try:
    import elikapowski_monitor_v2 as eli
except ImportError:
    eli = None
    print(f"{R}⚠️  elikapowski_monitor_v2.py no trobat.{X}")

try:
    import throwback_monitor_v1 as throwback
except ImportError:
    throwback = None
    print(f"{R}⚠️  throwback_monitor_v1.py no trobat.{X}")

try:
    import bridge48_monitor_v1 as bridge48
except ImportError:
    bridge48 = None
    print(f"{R}⚠️  bridge48_monitor_v1.py no trobat.{X}")

# ─── Funcions ─────────────────────────────────────────────────────────────────

def run_all():
    """Executa tots els monitors seqüencialment."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{B}{'═'*55}{X}")
    print(f"{B}🎵 CONCERT MONITOR — Execució completa{X}")
    print(f"   {now}")
    print(f"{B}{'═'*55}{X}")

    # ── Barcelona per gènere (RA) ─────────────────────────────────
    if bcn:
        try:
            bcn.check_events()
        except Exception as e:
            print(f"{R}Error Barcelona Monitor (RA): {e}{X}")
    else:
        print(f"{R}⚠️  Monitor de Barcelona (RA) no disponible.{X}")

    # ── Barcelona de tarda (Dice.fm) ──────────────────────────────
    if dice:
        try:
            dice.check_events()
        except Exception as e:
            print(f"{R}Error Barcelona Monitor (Dice): {e}{X}")
    else:
        print(f"{R}⚠️  Monitor de Barcelona (Dice) no disponible.{X}")
    # ── Lost Frequencies ──────────────────────────────────────────
    if lf:
        try:
            lf.check_concerts()
        except Exception as e:
            print(f"{R}Error Lost Frequencies: {e}{X}")
    else:
        print(f"{R}⚠️  Monitor de Lost Frequencies no disponible.{X}")

    # ── Elikapowski ───────────────────────────────────────────────
    if eli:
        try:
            eli.check_concerts()
        except Exception as e:
            print(f"{R}Error Elikapowski: {e}{X}")
    else:
        print(f"{R}⚠️  Monitor d'Elikapowski no disponible.{X}")


    # ── Throwback (RA) ──────────────────────────────
    if throwback:
        try:
            throwback.check_concerts()
        except Exception as e:
            print(f"{R}Error Throwback Monitor: {e}{X}")
    else:
        print(f"{R}⚠️  Monitor de Throwback (RA) no disponible.{X}")
        
    # ── Bridge 48 (RA) ──────────────────────────────
    if bridge48:
        try:
            bridge48.check_concerts()
        except Exception as e:
            print(f"{R}Error Bridge 48 Monitor: {e}{X}")
    else:
        print(f"{R}⚠️  Monitor de Bridge 48 (RA) no disponible.{X}")

    print(f"\n{B}{'═'*55}{X}")
    print(f"{B}✅ Execució completada.{X}")
    print(f"{B}{'═'*55}{X}\n")


def watch_mode():
    """Executa tots els monitors cada CHECK_HOURS hores."""
    print(f"{B}👁  Mode vigilant — comprovació cada {CHECK_HOURS}h{X}")
    print("   Prem Ctrl+C per aturar.\n")
    while True:
        try:
            run_all()
        except Exception as e:
            print(f"{R}Error durant la comprovació: {e}{X}")

        seg = CHECK_HOURS * 3600
        next_t = datetime.fromtimestamp(time.time() + seg).strftime("%H:%M:%S")
        print(f"\n   Propera comprovació a les {next_t}. Esperant...\n")
        time.sleep(seg)


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Monitor principal de concerts"
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
            run_all()
    except KeyboardInterrupt:
        print(f"\n{Y}Aturat.{X}")