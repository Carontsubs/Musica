# 🎵 Concert Monitor

Scripts per monitoritzar concerts d'artistes favorits en un radi de distància determinat.

## Artistes

| Script | Artista | Font de dades | Radi |
|--------|---------|---------------|------|
| `lost_frequencies_monitor_v4.py` | Lost Frequencies | Bandsintown (API oficial) | 200 km de Barcelona |
| `elikapowski_monitor_v2.py` | Elikapowski | Resident Advisor (GraphQL) | 35 km d'El Masnou |

---

## Instal·lació

```bash
pip install requests geopy
```

---

## Ús

### Consulta immediata
```bash
python lost_frequencies_monitor_v4.py
python elikapowski_monitor_v2.py
```

### Mode vigilant (comprova automàticament cada 6 hores)
```bash
python lost_frequencies_monitor_v4.py --watch
python elikapowski_monitor_v2.py --watch
```

---

## Com funciona

### Lost Frequencies
La web oficial ([lostfrequencies.com](https://lostfrequencies.com/tour-dates/)) usa el widget de Bandsintown. El script consulta directament l'API de Bandsintown amb l'`app_id` oficial de la web (`js_lostfrequencies.com`) i filtra els concerts per distància a Barcelona.

### Elikapowski
L'artista publica els seus concerts a [Resident Advisor](https://ra.co/dj/elikapowski). El script consulta l'API GraphQL de RA i filtra els concerts per distància a El Masnou.

---

## Exemple de sortida

```
───────────────────────────────────────────────────────
🎵 Lost Frequencies — Concerts a 200km de Barcelona
   Consulta: 2026-03-12 09:30:23
───────────────────────────────────────────────────────

▶ Consultant Bandsintown (app_id oficial)...
   33 concerts totals trobats.

😔 Cap concert a menys de 200km de Barcelona de moment.
   Comprova manualment: https://lostfrequencies.com/tour-dates/
```

---

## Dependències

- [`requests`](https://pypi.org/project/requests/) — peticions HTTP
- [`geopy`](https://pypi.org/project/geopy/) — càlcul de distàncies geogràfiques

---

## Roadmap

- [ ] Notificacions via Telegram
- [ ] Script unificat per a tots els artistes
- [ ] Suport per a més artistes
