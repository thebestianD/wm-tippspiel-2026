---
title: WM 2026 Tippspiel
emoji: 🏆
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: Halbautomatisches WM-2026-Tippspiel mit Gruppen, KO-Baum und Admin-Ergebnissen
---

# WM 2026 Tippspiel

Kompakter Prototyp für ein halbautomatisches Tippspiel zur WM 2026.

## Funktionen

- Teilnehmer tippen alle Vorrundenspiele.
- Pro Teilnehmer wird daraus ein eigener KO-Baum erzeugt.
- KO-Tipps funktionieren per Klick auf das weiterkommende Team.
- Admin trägt echte Endergebnisse manuell ein.
- Ein eingetragenes Admin-Ergebnis gilt als Endergebnis.
- Admin kann Gruppentabellen bei Sonderfällen manuell korrigieren.
- Tipps werden ab `PREDICTION_LOCK_AT` serverseitig gesperrt.
- Live-Ergebnisse zeigen eingeloggten Nutzern farbig, wie viele Punkte sie für gespielte Vorrundenspiele erhalten haben.
- Leaderboard wertet Gruppenspiele und korrekt vorhergesagte KO-Runden-Teilnahmen.

## Lokal starten

```bash
cd wm_tippspiel_proto
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
python app.py
```

Windows `cmd` statt `cp`:

```bat
copy .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Danach öffnen:

```text
http://localhost:7860
```

Admin:

```text
http://localhost:7860/admin/login
```

Das Admin-Passwort steht in `.env` unter `ADMIN_PASSWORD`.

## Hugging Face Space

Der Space läuft als Docker-Space auf Port `7860`. Die nötige Hugging-Face-Konfiguration steht im YAML-Block ganz oben in dieser `README.md`.

Empfohlene Secrets/Variables im Space:

```text
ADMIN_PASSWORD=dein-admin-passwort
SECRET_KEY=ein-langes-zufaelliges-secret
DATABASE_URL=sqlite:////data/wm_tippspiel.db
PREDICTION_LOCK_AT=2026-06-11T19:00:00Z
APP_NAME=WM 2026 Tippspiel
```

Für dauerhaft gespeicherte Daten sollte `/data` als persistenter Storage im Space eingerichtet sein. Ohne persistenten Storage kann die SQLite-Datenbank bei Neustarts verloren gehen.

## Docker lokal testen

```bash
docker build -t wm-tippspiel .
docker run --rm -p 7860:7860 \
  -e ADMIN_PASSWORD=bitte-aendern \
  -e SECRET_KEY=ein-langes-secret \
  wm-tippspiel
```

## Scoring

### Vorrunde

- Exaktes Ergebnis: 3 Punkte
- Richtige Tendenz: 1 Punkt
- Richtige Tordifferenz zusätzlich zur Tendenz: +1 Punkt

### KO-Runden

KO-Ergebnisse werden nicht bewertet. Es zählt, ob eine Mannschaft korrekt als Erreicher einer Runde vorhergesagt wurde:

- Erreicht Sechzehntelfinale: 1 Punkt pro Team
- Erreicht Achtelfinale: 2 Punkte pro Team
- Erreicht Viertelfinale: 3 Punkte pro Team
- Erreicht Halbfinale: 4 Punkte pro Team
- Erreicht Finale: 6 Punkte pro Team
- Weltmeister: 10 Punkte

## Admin-Workflow

1. Unter `/admin/login` anmelden.
2. Gruppenergebnisse eintragen und speichern.
3. Live-Ergebnisse unter `/tables` kontrollieren.
4. Bei nicht automatisch auflösbaren Tiebreakern im Adminbereich eine Reihenfolge per Team-Codes eintragen, z. B. `MEX,KOR,RSA,CZE`.
5. Nach der Gruppenphase KO-Gewinner im Admin-KO-Baum anklicken und speichern.
6. Leaderboard unter `/leaderboard` prüfen.

## Wichtige Prototypeinschränkung

Die Zuordnung der acht besten Gruppendritten nutzt aktuell einen constraint-basierten Resolver aus den offiziellen FIFA-Slot-Mengen. Für den produktiven Betrieb sollte die exakte 495-Zeilen-Tabelle aus FIFA Annex C als Lookup-Tabelle übernommen werden. Die Austauschstelle ist `wm_tippspiel/engine.py`, Funktion `_assign_third_place_groups`.

## Tests

```bash
pytest -q
```

## Nicht einchecken

Diese Dateien gehören nicht ins Git-Repository:

```text
.env
.venv/
wm_tippspiel.db
instance/
__pycache__/
.pytest_cache/
```
