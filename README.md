```
+============================================================+
|                                                            |
|              CONCERT MONITOR  v4.0                        |
|         (C) 2026 - All rights reserved                    |
|                                                            |
+============================================================+

  Monitor de concerts d'artistes favorits en un radi de
  distancia determinat, amb notificacions via Telegram.
  Pensat per ser executat via Windows Task Scheduler.


+------------------------------------------------------------+
|  ARTISTES I EVENTS                                         |
+------------------------------------------------------------+

  [1] Lost Frequencies
      Font    : Bandsintown API (js_lostfrequencies.com)
      Script  : lost_frequencies_monitor_v4.py
      Radi    : 200 km de Barcelona

  [2] Elikapowski
      Font    : Resident Advisor (GraphQL)
      Script  : elikapowski_monitor_v2.py
      Radi    : 35 km d'El Masnou

  [3] Events Barcelona per genere
      Font    : Resident Advisor (GraphQL)
      Script  : barcelona_monitor_v3.py
      Filtre  : House, Disco, Nu Disco, Deep House...
                Nomes divendres i dissabtes, 16h-22h
      Notif.  : Telegram

  [4] Events Barcelona de tarda
      Font    : Dice.fm (scraping HTML)
      Script  : barcelona_monitor_dice.py
      Filtre  : Tots els events de divendres i dissabte
                entre les 16h i les 22h
      Notif.  : Telegram


+------------------------------------------------------------+
|  INSTALACIO                                                |
+------------------------------------------------------------+

  C:\> pip install -r requirements.txt


+------------------------------------------------------------+
|  CONFIGURACIO TELEGRAM                                     |
+------------------------------------------------------------+

  Crea un fitxer .env a la mateixa carpeta:

      TOKEN_TELEGRAM=el_teu_token
      CHAT_ID=el_teu_chat_id

  Per obtenir el token: @BotFather a Telegram
  IMPORTANT: No pujar el .env a GitHub!


+------------------------------------------------------------+
|  US                                                        |
+------------------------------------------------------------+

  Execucio manual (tots els monitors alhora):
  C:\> python monitor.py

  Scripts individuals:
  C:\> python lost_frequencies_monitor_v4.py
  C:\> python elikapowski_monitor_v2.py
  C:\> python barcelona_monitor_v3.py
  C:\> python barcelona_monitor_dice.py

  Execucio automatica (recomanat):
  Configura Windows Task Scheduler per executar
  monitor.py cada dilluns (ex: a les 9h).


+------------------------------------------------------------+
|  COM FUNCIONA                                              |
+------------------------------------------------------------+

  MONITOR.PY
  ----------
  Script principal que importa i executa els quatre monitors
  sequencialment. Cada script segueix funcionant de forma
  independent si cal.

  LOST FREQUENCIES
  ----------------
  La web oficial usa el widget de Bandsintown. El script
  consulta l'API amb l'app_id oficial (js_lostfrequencies.com)
  i filtra els concerts per distancia a Barcelona.
  Envia notificacions via Telegram si troba concerts.

  ELIKAPOWSKI
  -----------
  L'artista publica els concerts a Resident Advisor.
  El script consulta l'API GraphQL de RA i filtra els
  concerts per distancia a El Masnou.
  Envia notificacions via Telegram si troba concerts.

  BARCELONA MONITOR (RA)
  ----------------------
  Consulta tots els events de Barcelona a Resident Advisor
  i filtra per genere (House, Disco, Nu Disco...) i paraules
  clau als titols. Nomes mostra events de divendres i
  dissabte entre les 16h i les 22h.
  Envia notificacions via Telegram amb els events trobats.

  BARCELONA MONITOR (DICE)
  ------------------------
  Fa scraping de la pagina de Barcelona a Dice.fm i extreu
  els events del proper cap de setmana (divendres i dissabte)
  entre les 16h i les 22h, sense filtre de genere.
  Envia notificacions via Telegram amb els events trobats.


+------------------------------------------------------------+
|  DEPENDENCIES                                              |
+------------------------------------------------------------+

  requests       Peticions HTTP
  geopy          Calcul de distancies geografiques
  python-dotenv  Carrega variables d'entorn des de .env


+------------------------------------------------------------+
|  ROADMAP                                                   |
+------------------------------------------------------------+

  [x] Notificacions via Telegram
  [x] Script unificat per a tots els artistes
  [x] Events de Barcelona via Dice.fm
  [ ] Suport per a mes artistes


+============================================================+
|  Press any key to continue...                              |
+============================================================+
```