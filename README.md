```
+============================================================+
|                                                            |
|              CONCERT MONITOR  v2.0                        |
|         (C) 2026 - All rights reserved                    |
|                                                            |
+============================================================+

  Monitor de concerts d'artistes favorits en un radi de
  distancia determinat, amb notificacions via Telegram.


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


+------------------------------------------------------------+
|  INSTALACIO                                                |
+------------------------------------------------------------+

  C:\> pip install -r requirements.txt


+------------------------------------------------------------+
|  CONFIGURACIO TELEGRAM (opcional)                          |
+------------------------------------------------------------+

  Crea un fitxer .env a la mateixa carpeta:

      TELEGRAM_TOKEN=el_teu_token
      TELEGRAM_CHAT_ID=el_teu_chat_id

  Per obtenir el token: @BotFather a Telegram
  IMPORTANT: No pujar el .env a GitHub!


+------------------------------------------------------------+
|  US                                                        |
+------------------------------------------------------------+

  Consulta immediata:
  C:\> python lost_frequencies_monitor_v4.py
  C:\> python elikapowski_monitor_v2.py
  C:\> python barcelona_monitor_v3.py

  Mode vigilant (comprova cada 6 hores):
  C:\> python lost_frequencies_monitor_v4.py --watch
  C:\> python elikapowski_monitor_v2.py --watch
  C:\> python barcelona_monitor_v3.py --watch


+------------------------------------------------------------+
|  COM FUNCIONA                                              |
+------------------------------------------------------------+

  LOST FREQUENCIES
  ----------------
  La web oficial usa el widget de Bandsintown. El script
  consulta l'API amb l'app_id oficial (js_lostfrequencies.com)
  i filtra els concerts per distancia a Barcelona.

  ELIKAPOWSKI
  -----------
  L'artista publica els concerts a Resident Advisor.
  El script consulta l'API GraphQL de RA i filtra els
  concerts per distancia a El Masnou.

  BARCELONA MONITOR
  -----------------
  Consulta tots els events de Barcelona a Resident Advisor
  i filtra per genere (House, Disco, Nu Disco...) i paraules
  clau als titols. Nomes mostra events de divendres i
  dissabte entre les 16h i les 22h. Envia notificacions
  via Telegram quan troba events coincidents.


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
  [ ] Script unificat per a tots els artistes
  [ ] Suport per a mes artistes


+============================================================+
|  Press any key to continue...                              |
+============================================================+
```