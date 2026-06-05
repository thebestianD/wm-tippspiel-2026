# WM 2026 Tippspiel – Prototyp

Lauffähiger Prototyp für ein halbautomatisches WM-Tippspiel:

- Teilnehmer tippen alle 72 Vorrundenspiele.
- Daraus wird pro Teilnehmer ein eigener KO-Baum erzeugt.
- Teilnehmer wählen in der KO-Phase nur die Sieger, keine KO-Ergebnisse. Der KO-Baum ist klickbar und füllt sich im Browser automatisch weiter.
- Admin trägt echte Endergebnisse manuell ein.
- Ein eingetragenes Ergebnis gilt als Endergebnis; es gibt keinen Spielstatus.
- Admin kann Gruppentabellen manuell korrigieren, falls Tiebreaker/Fairplay nicht automatisch abgebildet werden sollen.
- Tipps sind ab `PREDICTION_LOCK_AT` serverseitig gesperrt.
- Leaderboard wertet Gruppenspiel-Tipps und korrekt vorhergesagte KO-Runden-Teilnahmen.
- Die Vorrunden-Tippseite ist kompakter und zeigt neben jeder Gruppe eine sofort aktualisierte Live-Tabelle.
- Match-Zeilen zeigen Datum/Uhrzeit in deutscher Sommerzeit sowie einen konservativen Free-TV-Hinweis für Deutschland.

## Technischer Stack

- Python 3.11 im Docker-Deployment; lokal wurde zusätzlich Python 3.14 kompatibel gemacht (`psycopg[binary]==3.3.4`).
- Flask
- SQLAlchemy
- SQLite lokal, Supabase/Postgres in Produktion
- Dockerfile für Hugging Face Spaces

## Hinweise zu Spielplan und Free-TV

Die Datei `wm_tippspiel/seed_data.py` enthält `MATCH_INFO` mit Kick-off-Zeiten aus dem FIFA-Spielplan. FIFA veröffentlicht die Zeiten als Eastern Time; die App zeigt sie im Interface auf Deutschland/Berlin-Sommerzeit umgerechnet an.

Bei der TV-Info ist nur sicher hinterlegt, was aktuell konkret bekannt ist: Eröffnungsspiel und Finale im ZDF sowie die drei deutschen Gruppenspiele gemäß aktuellen Medienberichten. Für alle übrigen Spiele steht `Free-TV offen / MagentaTV`, weil ARD/ZDF zwar insgesamt 60 Spiele zeigen, aber nicht jede einzelne Free-TV-Zuordnung im Prototyp hart als gesichert behandelt werden sollte. Du kannst diese Labels in `MATCH_INFO` jederzeit anpassen.

## Wichtige Prototypeinschränkung

Der Prototyp nutzt für die Zuordnung der acht besten Gruppendritten zu den Round-of-32-Slots einen constraint-basierten Resolver aus den offiziellen FIFA-Slot-Mengen, z. B. `1E vs 3ABCDF`. Für den produktiven Betrieb sollte die exakte 495-Zeilen-Tabelle aus FIFA Annex C als Lookup-Tabelle übernommen werden. Die Austauschstelle ist `wm_tippspiel/engine.py`, Funktion `_assign_third_place_groups`.

Die Grundlogik ist bewusst so gebaut, dass dieser Austausch nur eine Funktion betrifft.

## Lokal starten

```bash
cd wm_tippspiel_proto
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
# macOS/Linux
cp .env.example .env

# Windows cmd
copy .env.example .env

# Windows PowerShell
Copy-Item .env.example .env
python app.py
```

Dann öffnen:

```text
http://localhost:7860
```

Admin:

```text
http://localhost:7860/admin/login
```

Das Passwort steht in `.env` unter `ADMIN_PASSWORD`.

## Mit Docker lokal starten

```bash
docker build -t wm-tippspiel .
docker run --rm -p 7860:7860 \
  -e ADMIN_PASSWORD=bitte-aendern \
  -e SECRET_KEY=ein-langes-secret \
  wm-tippspiel
```

Danach öffnen:

```text
http://localhost:7860
```

Ohne `DATABASE_URL` nutzt der Container SQLite im Container. Das ist nur für Tests sinnvoll, weil Container-Speicher bei Deployments nicht verlässlich persistent ist.

## Supabase einrichten

1. Supabase-Projekt erstellen.
2. Unter **Settings → Database → Connection string → URI** den Postgres-Connection-String kopieren.
3. Für Hugging Face als Secret `DATABASE_URL` setzen.
4. Keine Tabellen manuell anlegen: Die App erstellt Tabellen beim Start automatisch und seedet Teams/Spiele.

Empfohlene Secrets:

```text
DATABASE_URL=postgresql://...
ADMIN_PASSWORD=...
SECRET_KEY=...
PREDICTION_LOCK_AT=2026-06-11T19:00:00Z
APP_NAME=WM 2026 Tippspiel
```

## Hugging Face Space deployen

1. Hugging Face → **New Space**.
2. SDK: **Docker**.
3. Visibility nach Wunsch: private oder public.
4. Dateien dieses Ordners ins Space-Repository hochladen oder per Git pushen.
5. Unter **Settings → Variables and secrets** die oben genannten Secrets setzen.
6. Space starten. Die App läuft auf Port `7860`.

## Tipp-Lock

Die Sperre wird in `PREDICTION_LOCK_AT` gesetzt. Standard:

```text
2026-06-11T19:00:00Z
```

Das entspricht dem WM-Eröffnungsspiel am 11.06.2026 um 21:00 Uhr in Deutschland/Berlin.

Die Sperre wird im Backend geprüft. Nach dieser Zeit werden POSTs für Teilnehmer-Tipps abgewiesen.

## Scoring

Standardwerte stehen in `wm_tippspiel/seed_data.py` unter `DEFAULT_SETTINGS`.

### Gruppenspiele

- Exaktes Ergebnis: 3 Punkte
- Richtige Tendenz: 1 Punkt
- Richtige Tordifferenz zusätzlich zur Tendenz: +1 Punkt

### KO-Runden

Es werden keine KO-Ergebnisse bewertet. Stattdessen zählt, ob eine Mannschaft korrekt als Erreicher einer Runde vorhergesagt wurde:

- Erreicht Sechzehntelfinale: 1 Punkt pro Team
- Erreicht Achtelfinale: 2 Punkte pro Team
- Erreicht Viertelfinale: 3 Punkte pro Team
- Erreicht Halbfinale: 4 Punkte pro Team
- Erreicht Finale: 6 Punkte pro Team
- Weltmeister: 10 Punkte

Ein Team kann mehrere Rundenpunkte sammeln, wenn es entsprechend weit kommt.

## Bedienung

### Vorrunde

Die Gruppen werden in kompakten Panels dargestellt. Während du Tore eingibst, aktualisiert sich die Tabelle rechts sofort. Bei normalen Fällen reicht diese Sofortanzeige aus; bei komplexen Tiebreakern zählt nach dem Speichern die Python-Regel-Engine.

### KO-Baum

Im KO-Baum klickst du das Team an, das weiterkommt. Die nächste Runde wird direkt im Browser gefüllt. Anschließend einmal **KO-Tipps speichern** klicken.

## Admin-Workflow

1. Unter `/admin/login` anmelden.
2. Gruppenergebnisse eintragen und speichern.
3. Live-Ergebnisse unter `/tables` kontrollieren.
4. Bei nicht automatisch auflösbaren Tiebreakern im Adminbereich eine Reihenfolge per Team-Codes eintragen, z. B. `MEX,KOR,RSA,CZE`.
5. Nach der Gruppenphase KO-Gewinner je Spiel eintragen und speichern.
6. Leaderboard unter `/leaderboard` prüfen.

## Tests

```bash
pytest -q
```

## Quellenhinweise für die Seed-Daten

Die Stammdaten orientieren sich am FIFA World Cup 2026 Match Schedule PDF und an den FIFA World Cup 26 Regulations. Für produktiven Betrieb sollten die finalen PDF-Versionen kurz vor Start nochmals geprüft werden.

## Update v5

Diese Version enthält gegenüber v4 folgende UI- und Stabilitätsänderungen:

- Emoji-Flaggen wurden durch kleine Flaggenbilder via `flagcdn.com` ersetzt, damit Windows/Browser ohne Emoji-Flag-Support nicht nur Ländercodes anzeigen.
- Hinweise wie „Admin-Korrektur empfohlen“ erscheinen nicht mehr in der Nutzeransicht, sondern nur im Adminbereich.
- Der KO-Baum nutzt jetzt die volle Seitenbreite und scrollt horizontal nur noch bei kleineren Fenstern.
- Die Admin-Ansicht ist strukturell an die Nutzeransicht angeglichen: Gruppen-Panels mit Live-Tabelle und klickbarer KO-Baum statt Radio-Listen.
- Die öffentliche Tabellenansicht zeigt keine Admin-Tiebreaker-Hinweise mehr.

Hinweis: Die Flaggenbilder werden extern geladen. Falls die App vollständig offline laufen soll, können die Flaggen später als lokale Assets ins Projekt gelegt werden.

## Update v6

Diese Version enthält gegenüber v5 folgende Änderungen:

- Der Reiter heißt nun **Live-Ergebnisse** statt **Tabellen** und nutzt die volle Seitenbreite.
- Eingetragene Admin-Ergebnisse werden für eingeloggte Nutzer farblich nach erzielten Vorrundenpunkten markiert.
- Vorrunden-Scoring geändert: exaktes Ergebnis 3 Punkte, richtige Tendenz 1 Punkt, plus 1 Punkt bei richtiger Tordifferenz.
- Der KO-Baum ist vertikal ausgerichtet: zusammengehörige Sechzehntelfinals und Achtelfinals stehen auf einer nachvollziehbaren Höhe.
- Der Speicherhinweis im KO-Baum ist nicht mehr sticky und überdeckt keine Rundenüberschriften mehr.

## Update v7

Diese Version enthält gegenüber v6 folgende Änderungen:

- Der Tab **Live-Ergebnisse** verhindert nun Überläufe der Gruppentabelle in den nächsten Gruppenblock; Tabellen in Gruppen-Panels sind nicht mehr sticky und bleiben innerhalb ihres Blocks.
- Ergebnisfelder werden client- und serverseitig normalisiert: `02` wird als `2` gespeichert und angezeigt.
- Zweistellige Torwerte ab `10` werden nicht blockiert, aber direkt im Formular markiert und nach dem Speichern zusätzlich als Hinweis gemeldet.
- Die Tipp-Lock-Zeit wird im Interface im deutschen Format angezeigt, z. B. `11.06.2026 21:00 MESZ` statt UTC-Notation.
