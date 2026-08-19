# Mood

Ein privater, dunkler Medien-Organizer mit verschlüsseltem Tresor und einem
Vollbild-„Mood“-Slideshow-Modus. Gebaut mit **Python + PySide6 (Qt)**.

Die Dateien werden mit AES (Fernet) verschlüsselt, die Ordnernamen sind
undurchsichtige Hashes, und der Zugang ist passwortgeschützt (mit Sperre nach
zu vielen Fehlversuchen).

---

## Schnellstart

### Windows
Doppelklick auf **`start_mood.bat`**. Beim ersten Start werden die
Abhängigkeiten automatisch installiert.

### macOS / Linux
```bash
./start_mood.sh
```
Legt beim ersten Start eine lokale virtuelle Umgebung (`.venv`) an, installiert
alles aus `requirements.txt` und startet die App.

### Manuell (alle Systeme)
```bash
pip install -r requirements.txt
python main.py
```

Benötigt **Python 3.10+**.

---

## Portabel

Die App speichert ihre Daten (`Media/`, `mood.db`, Einstellungen, Tresor-Schlüssel)
**neben den Programmdateien**. Du kannst den ganzen `Mood`-Ordner auf einen
USB-Stick oder einen anderen Rechner (Windows / macOS / Linux) kopieren – er
läuft überall.

Willst du die Daten woanders ablegen, setze die Umgebungsvariable **`MOOD_HOME`**:

```bash
# Linux / macOS
MOOD_HOME="/pfad/zu/meinen/daten" python main.py

# Windows (PowerShell)
$env:MOOD_HOME="D:\MeineDaten"; python main.py
```

---

## Abhängigkeiten
Siehe `requirements.txt`. Kurz:

| Paket | Wofür |
|-------|-------|
| PySide6 | Oberfläche (Qt) |
| Pillow, pillow-heif | Bilder + HEIC/HEIF |
| opencv-python-headless | Video-Thumbnails |
| imageio-ffmpeg | mitgeliefertes ffmpeg (falls keines im System) |
| send2trash | Löschen in den Papierkorb |
| cryptography | Verschlüsselung |

Videos werden mit `ffmpeg` konvertiert. Ist keines im System installiert, wird
automatisch das mit `imageio-ffmpeg` mitgelieferte benutzt.

---

## Tastenkürzel

**Hauptfenster**
- `Ctrl+I` – Dateien importieren
- `Ctrl+G` – Mood-Modus starten
- `Entf` / `Backspace` – ausgewählte Dateien löschen
- `F9` – Log-Datei öffnen

**Mood-Modus (Vollbild)**
- `Leertaste` – nächstes Bild/Set
- `1` `2` `3` `4` – Anzahl Kacheln
- `R` – Zufalls-/Reihenfolge-Modus
- `C` – Countdown an/aus
- `H` – Info-Leiste
- `B` – Blackout (sofort schwarz; Taste in Einstellungen änderbar)
- `X` – Panic (App sofort schließen; Taste änderbar)
- `Esc` – schließen

---

## Aufbau

| Datei | Aufgabe |
|-------|---------|
| `main.py` | Oberfläche, Mood-Modus, Ablauf |
| `config.py` | Pfade, Farben, Konstanten (portabler `APP_ROOT`) |
| `database.py` | SQLite (Darsteller, Medien, Sessions) |
| `crypto_vault.py` | Passwort, AES-Verschlüsselung, Sperre |
| `converter.py` | Bild-/Video-Konvertierung (parallel) |
| `thumbnails.py` | Thumbnail-Erzeugung + Cache |
| `settings_store.py` | Einstellungen (JSON) |
| `logger.py` | Logging in Datei + Konsole |
