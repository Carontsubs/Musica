+============================================================+
|                                                            |
|              CONCERT MONITOR  v4.4                        |
|         (C) 2026 - All rights reserved                    |
|                                                            |
+============================================================+

  Monitor de concerts i events favorits en un radi de
  distancia determinat, amb notificacions via Telegram.
  Pensat per ser executat via Windows Task Scheduler.


+------------------------------------------------------------+
|  ARTISTES I EVENTS                                         |
+------------------------------------------------------------+

  [1] Lost Frequencies
      Font    : Bandsintown API (js_lostfrequencies.com)
      Script  : lost_frequencies_monitor_v4.py
      Radi    : 200 km de Barcelona
      Nota    : Script independent, NO inclos a monitor.py

  [2] Elikapowski
      Font    : Resident Advisor (GraphQL)
      Script  : elikapowski_monitor_v2.py
      Radi    : 35 km d'El Masnou

  [3] Events Barcelona per genere
      Font    : Resident Advisor (GraphQL)
      Script  : barcelona_monitor_v1.py
      Filtre  : House, Disco, Nu Disco, Deep House...
                Nomes divendres i dissabtes, 16h-22h
      Notif.  : Telegram

  [4] Events Barcelona de tarda
      Font    : Dice.fm (scraping HTML)
      Script  : barcelona_monitor_dice.py
      Filtre  : Tots els events de divendres i dissabte
                entre les 16h i les 22h
      Notif.  : Telegram

  [5] Throwback - Back to 80s, 90s & 00s
      Font    : Resident Advisor (GraphQL - venue La Terrrazza)
      Script  : throwback_monitor_v1.py
      Filtre  : Events amb "throwback", "80s", "90s", "00s"
                al titol, venue ID 3760 (La Terrrazza)
      Radi    : 35 km d'El Masnou
      Notif.  : Telegram

  [5b] Throwback - Detector de nous events
      Font    : Resident Advisor (GraphQL - venue La Terrrazza)
      Script  : throwback_early_bird.py
      Filtre  : Igual que [5] pero nomes notifica quan
                apareix un event que no havia vist abans
      Memoria : throwback_known.json (IDs ja vistos)
      Notif.  : Telegram
      Nota    : Script independent, NO inclos a monitor.py

  [6] Bridge 48 - Events de tarda
      Font    : Resident Advisor (GraphQL - venue Bridge 48)
      Script  : bridge48_monitor_v1.py
      Filtre  : Events de dissabte i diumenge entre 16h-22h
                Propers 2 caps de setmana des de l'execucio
                Venue ID 178344 (Bridge 48, Barcelona)
      Notif.  : Telegram

  [7] La Paloma - Events de cap de setmana
      Font    : Resident Advisor (GraphQL - venue La Paloma)
      Script  : paloma_monitor_v1.py
      Filtre  : Events de divendres i dissabte que acabin
                com a molt tard a les 03:00h de la matinada
                Propers 2 caps de setmana des de l'execucio
                Venue ID 207515 (La Paloma, Barcelona)
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
  C:\> python elikapowski_monitor_v2.py
  C:\> python barcelona_monitor_v1.py
  C:\> python barcelona_monitor_dice.py
  C:\> python throwback_monitor_v1.py
  C:\> python bridge48_monitor_v1.py
  C:\> python paloma_monitor_v1.py

  Scripts independents (NO inclosos a monitor.py):
  C:\> python lost_frequencies_monitor_v4.py
  C:\> python throwback_early_bird.py

  Execucio automatica (recomanat):
  Configura Windows Task Scheduler per executar
  monitor.py cada dilluns (ex: a les 9h).
  lost_frequencies_monitor_v4.py i throwback_early_bird.py
  es poden programar amb la seva propia frequencia.


+------------------------------------------------------------+
|  COM FUNCIONA                                              |
+------------------------------------------------------------+

  MONITOR.PY
  ----------
  Script principal que importa i executa sis monitors
  sequencialment: Elikapowski, Barcelona (RA), Barcelona
  (Dice), Throwback, Bridge 48 i La Paloma. Cada script
  segueix funcionant de forma independent si cal.
  Lost Frequencies i throwback_early_bird.py NO s'inclouen
  aqui i s'han d'executar per separat.

  LOST FREQUENCIES
  ----------------
  La web oficial usa el widget de Bandsintown. El script
  consulta l'API amb l'app_id oficial (js_lostfrequencies.com)
  i filtra els concerts per distancia a Barcelona.
  Envia notificacions via Telegram si troba concerts.
  Script independent, NO inclos a monitor.py.

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

  THROWBACK - BACK TO 80s, 90s & 00s
  ------------------------------------
  Consulta els events futurs del venue La Terrrazza
  (ID 3760) a Resident Advisor via GraphQL i filtra els
  que continguin "throwback", "80s", "90s" i "00s" al
  titol. Filtra per distancia a El Masnou (35km).
  Envia notificacions via Telegram si troba events.

  THROWBACK - DETECTOR DE NOUS EVENTS
  ------------------------------------
  Complementari a l'anterior. En lloc de mostrar tots els
  events Throwback cada vegada, nomes notifica quan apareix
  un event amb ID nou que no havia vist en execucions
  anteriors. Guarda la memoria a throwback_known.json.
  Pensat per executar-se diariament via Task Scheduler.
  Script independent, NO inclos a monitor.py.

  BRIDGE 48
  ---------
  Consulta els events futurs del venue Bridge 48
  (ID 178344) a Resident Advisor via GraphQL. Filtra
  els events dels propers 2 caps de setmana que comencin
  entre les 16h i les 22h. No requereix filtre de genere
  ni de distancia (venue fix a Barcelona).
  Envia notificacions via Telegram si troba events.

  LA PALOMA
  ---------
  Consulta els events futurs del venue La Paloma
  (ID 207515) a Resident Advisor via GraphQL. Filtra
  els events de divendres i dissabte dels propers 2 caps
  de setmana que acabin com a molt tard a les 03:00h de
  la matinada. Si un event no te hora de fi informada,
  s'inclou igualment per no perdre'l.
  Envia notificacions via Telegram si troba events.


+------------------------------------------------------------+
|  FITXERS DE MEMORIA                                        |
+------------------------------------------------------------+

  throwback_known.json   IDs d'events Throwback ja vistos.
                         Generat automaticament per
                         throwback_early_bird.py


+------------------------------------------------------------+
|  DEPENDENCIES                                              |
+------------------------------------------------------------+

  requests       Peticions HTTP
  geopy          Calcul de distancies geografiques
  python-dotenv  Carrega variables d'entorn des de .env


+------------------------------------------------------------+
|  FULL DE RUTA                                              |
+------------------------------------------------------------+

  [x] Notificacions via Telegram
  [x] Script unificat per a tots els artistes
  [x] Events de Barcelona via Dice.fm
  [x] Monitor per events recurrents (Throwback)
  [x] Detector de nous events amb memoria (Throwback)
  [x] Monitor per venue especific (Bridge 48)
  [x] Monitor per venue especific (La Paloma)
  [ ] Suport per a mes artistes


+============================================================+
|  Press any key to continue...                              |
+============================================================+