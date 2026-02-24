# 📡 BandWacht - OpenWebRX Band Monitor

**Teil des [FunkPilot](https://funkpilot.oeradio.at) Ökosystems**

BandWacht verbindet sich mit beliebigen OpenWebRX-Instanzen via WebSocket, überwacht das Spektrum auf Trägersignale und löst Benachrichtigungen und/oder Aufnahmen aus.

## Features

- 🔌 **Remote-Monitoring**: Verbindet sich zu jeder öffentlichen oder eigenen OpenWebRX-Instanz
- 🎯 **Gezielte Frequenzüberwachung**: Definiere spezifische Frequenzen mit individuellen Schwellwerten
- 🔍 **Full-Band-Scan**: Erkennt automatisch alle Träger im sichtbaren Band
- 📢 **Flexible Benachrichtigungen**: Console, Gotify, Telegram, ntfy, Webhook
- 🎙️ **Aufnahme**: Automatische Audioaufnahme bei Carrier-Erkennung
- 📊 **CSV-Logging**: Alle Detektionen werden protokolliert
- 🐳 **Docker-Ready**: Containerisiert einsetzbar
- 🔄 **Multi-Instanz**: Überwache mehrere SDRs gleichzeitig
- ⚡ **Hysterese & Cooldown**: Vermeidet Fehlalarme durch intelligente Signalverarbeitung
- 🌐 **Web UI**: Live-Spektrum, Konfiguration und Ereignis-Logbuch im Browser

## Schnellstart

### Installation

```bash
pip install -r requirements.txt
```

### Einfache Nutzung

```bash
# Band überwachen
python bandwacht.py --url http://my-webrx:8073 --band 2m

# Bestimmte Frequenzen
python bandwacht.py --url http://my-webrx:8073 \
  --freq 145.500 145.6125 438.950 \
  --threshold -55

# Full-Band-Scan mit Aufnahme
python bandwacht.py --url http://my-webrx:8073 --scan --record

# Profil umschalten (z.B. von 80m auf 2m)
python bandwacht.py --url http://my-webrx:8073 --profile "rtlsdr|2m" --scan

# Mit ntfy Benachrichtigung
python bandwacht.py --url http://my-webrx:8073 \
  --freq 145.500 \
  --notify console ntfy --ntfy-topic mein-bandwacht

# Debug-Modus (zeigt WebSocket-Nachrichten)
python bandwacht.py --url http://my-webrx:8073 --scan --debug
```

### Konfigurationsdatei

```bash
python bandwacht.py --config examples/kaernten_relais.json
```

### Docker

```bash
# Config anlegen
cp examples/kaernten_relais.json config/bandwacht.json
# URL anpassen!

# Starten
docker compose up -d
```

## Konfiguration

### JSON Config Beispiel

```json
{
    "url": "http://my-openwebrx:8073",
    "profile": "rtlsdr|2m",
    "threshold_db": -55,
    "targets": [
        {
            "freq_mhz": 145.500,
            "bandwidth_khz": 12,
            "label": "S20 Anruf",
            "threshold_db": -50
        },
        {
            "freq_mhz": 438.950,
            "bandwidth_khz": 12,
            "label": "OE8XVK Villach"
        }
    ],
    "record": true,
    "log_csv": true,
    "notify": {
        "console": true,
        "ntfy": { "topic": "bandwacht" },
        "gotify": { "url": "http://gotify:8080", "token": "xxx" },
        "telegram": { "bot_token": "123:ABC", "chat_id": "123" },
        "webhook": { "url": "http://funkpilot/api/events" }
    }
}
```

### CLI Parameter

**Verbindung & Konfiguration**

| Parameter | Kurz | Default | Beschreibung |
|-----------|------|---------|-------------|
| `--url` | `-u` | - | OpenWebRX URL (Pflicht, oder `--config`) |
| `--config` | `-c` | - | JSON-Konfigurationsdatei (ersetzt alle anderen Argumente) |
| `--profile` | `-p` | - | OpenWebRX Profil-ID zum Umschalten (z.B. `rtlsdr\|2m`) |

**Frequenzauswahl**

| Parameter | Kurz | Default | Beschreibung |
|-----------|------|---------|-------------|
| `--band` | `-b` | - | Bandname (2m, 70cm, 20m, etc.) |
| `--freq` | `-f` | - | Frequenzen in MHz (mehrere möglich) |
| `--freq-bw` | | 12 kHz | Überwachungsbandbreite pro Frequenz |
| `--scan` | | off | Full-Band-Scan aktivieren |

**Erkennung**

| Parameter | Default | Beschreibung |
|-----------|---------|-------------|
| `--threshold` / `-t` | -55 dB | Erkennungsschwelle |
| `--hysteresis` | 5 dB | Hysterese (Unterschied Trigger/Release) |
| `--hold-time` | 2 s | Haltezeit bevor ein Event ausgelöst wird |
| `--cooldown` | 10 s | Mindestabstand zwischen Alarmen |

**Benachrichtigungen**

| Parameter | Default | Beschreibung |
|-----------|---------|-------------|
| `--notify` / `-n` | console | Backends: `console`, `gotify`, `telegram`, `ntfy`, `webhook` |
| `--gotify-url` | - | Gotify Server-URL |
| `--gotify-token` | - | Gotify App-Token |
| `--telegram-token` | - | Telegram Bot-Token |
| `--telegram-chat` | - | Telegram Chat-ID |
| `--ntfy-topic` | - | ntfy Topic-Name |
| `--ntfy-server` | https://ntfy.sh | ntfy Server-URL |
| `--webhook-url` | - | Webhook-URL für POST-Benachrichtigungen |

**Aufnahme & Logging**

| Parameter | Kurz | Default | Beschreibung |
|-----------|------|---------|-------------|
| `--record` | `-r` | off | Audioaufnahme bei Carrier-Erkennung |
| `--recording-dir` | | ./recordings | Verzeichnis für Aufnahmen |
| `--csv` | | off | CSV-Logging aktivieren |
| `--csv-file` | | ./bandwacht_log.csv | CSV-Dateipfad |
| `--verbose` | `-v` | off | Ausführliche Ausgabe |
| `--debug` | | off | Debug-Ausgabe (inkl. WebSocket-Nachrichten) |

### Unterstützte Bänder

160m, 80m, 60m, 40m, 30m, 20m, 17m, 15m, 12m, 10m, 6m, **2m**, **70cm**, 23cm, PMR, Freenet, CB, AIS, NOAA, Airband

## Multi-Instanz-Betrieb

Überwache mehrere OpenWebRX-Instanzen gleichzeitig:

```bash
python bandwacht_multi.py --config examples/multi_instance.json
```

Dies ermöglicht z.B. ein verteiltes Monitoring-Netzwerk über ganz Österreich.

## Architektur

```
┌──────────────────┐     WebSocket      ┌──────────────────┐
│  OpenWebRX #1    │◄──────────────────►│                  │
│  (z.B. Kärnten)  │   FFT + Audio      │                  │
└──────────────────┘                    │                  │
                                        │   BandWacht      │──► Console
┌──────────────────┐     WebSocket      │                  │──► Gotify
│  OpenWebRX #2    │◄──────────────────►│   Spectrum       │──► Telegram
│  (z.B. Stmk)    │   FFT + Audio      │   Analyzer       │──► ntfy
└──────────────────┘                    │                  │──► Webhook
                                        │                  │──► WAV Recording
┌──────────────────┐     WebSocket      │                  │──► CSV Log
│  Öffentl. WebRX  │◄──────────────────►│                  │
│  (beliebig)      │   FFT (read-only)  │                  │
└──────────────────┘                    └──────────────────┘
```

## Wie es funktioniert

1. **WebSocket-Verbindung**: BandWacht verbindet sich zum OpenWebRX-Server über den gleichen WebSocket-Endpunkt, den auch der Browser nutzt (`ws://host:port/ws/`)

2. **FFT-Daten empfangen**: Der Server sendet komprimierte FFT-Spektrumdaten (ADPCM) die das gesamte sichtbare Band darstellen

3. **Spektrumanalyse**: Die FFT-Daten werden dekomprimiert und auf definierte Frequenzbereiche analysiert. Ein adaptiver Noise-Floor-Schätzer vermeidet Fehlalarme.

4. **Carrier-Erkennung**: Signale über dem Schwellwert (absolut oder relativ zum Noise Floor) lösen nach einer Haltezeit Events aus

5. **Benachrichtigung & Aufnahme**: Events werden an konfigurierte Backends gesendet und optional wird Audio aufgenommen

## Einschränkungen

- **Ein Slot pro Verbindung**: Jede WebSocket-Verbindung belegt einen Client-Slot am Server
- **Profil-Wechsel**: BandWacht kann das Profil (Band) am Server umschalten (`--profile`), aber der SDR kann nur ein Band gleichzeitig empfangen
- **Audio-Aufnahme limitiert**: Audio wird nur für die aktuell eingestellte Demodulator-Frequenz empfangen (Limitation von OpenWebRX)
- **Öffentliche Server**: Können jederzeit offline gehen oder die Konfiguration ändern

## Web UI

BandWacht enthält eine vollständige Web-Oberfläche zur Live-Überwachung, Konfiguration und Ereignishistorie.

### Features

- **Live-Spektrum**: Echtzeit-FFT-Darstellung im Browser (Canvas-basiert)
- **Dashboard**: SDR-Instanzen starten/stoppen, Live-Ereignis-Feed
- **Konfiguration**: SDR-Instanzen, Überwachungsziele, Erkennungsparameter, Benachrichtigungen
- **Logbuch**: Paginierte Ereignishistorie mit Filtern, CSV-Export, Audio-Wiedergabe
- **Statistiken**: Häufigste Frequenzen, tägliche/wöchentliche Übersicht (Recharts)
- **Responsive**: Desktop + Mobile, dunkles SDR-Theme

### Architektur

```
Browser (React + Vite + Tailwind)
    │
    ├── REST API ──► FastAPI Backend
    │                   ├── MonitorManager (wraps BandWacht engine)
    │                   ├── SQLite via async SQLAlchemy
    │                   └── Serves built frontend as static files
    │
    └── WebSocket ◄── /ws/spectrum/{id} (live FFT) + /ws/events (detections)
```

### Web UI starten (Entwicklung)

```bash
# Backend
cd web/backend && pip install -r requirements.txt
uvicorn web.backend.main:app --reload

# Frontend (separates Terminal)
cd web/frontend && npm install && npm run dev
```

### Web UI deployen (Docker)

```bash
# .env.production konfigurieren
cp .env.production.example .env.production
# Werte anpassen (DEPLOY_HOST, REMOTE_DIR, etc.)

# Deployment
./deploy-bandwacht-web.sh
```

Die Web UI läuft als eigenständiger Docker-Container (Port 3418) und ist unter https://bandwacht.oeradio.at erreichbar.

### API Endpunkte

| Endpunkt | Beschreibung |
|----------|-------------|
| `GET/POST /api/v1/instances` | SDR-Instanzen CRUD |
| `POST /api/v1/instances/{id}/start\|stop` | Monitor starten/stoppen |
| `GET/POST /api/v1/targets` | Überwachungsziele CRUD |
| `GET /api/v1/events` | Ereignisse (paginiert, filterbar) |
| `GET /api/v1/events/export` | CSV-Export |
| `GET /api/v1/recordings/{file}` | WAV-Aufnahmen streamen |
| `GET/PUT /api/v1/settings` | Erkennungsparameter |
| `WS /ws/spectrum/{id}` | Live FFT-Daten (~10fps) |
| `WS /ws/events` | Live Erkennungs-Events |

## Integration mit FunkPilot

BandWacht ist als Modul für das FunkPilot-Ökosystem konzipiert:

- **relaisblick**: Liefert Repeater-Frequenzen als Watch-Targets
- **FunkPilot API**: Events können an die FunkPilot-API gesendet werden
- **Webhook**: Flexibler Endpoint für weitere Integrationen

## Lizenz

MIT

## Autor

OE8YML - [FunkPilot](https://funkpilot.oeradio.at) | [Strali Solutions](https://strali.solutions)
