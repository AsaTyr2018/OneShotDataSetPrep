## 💻 Development Phases for `OneShotDataSetPrep`

### 🔨 PHASE 1: Core Image Processing (Backend Only)

**Ziel:** Erstmal sicherstellen, dass die Bildverarbeitung korrekt funktioniert – unabhängig von UI oder Webserver.

#### Tasks:

* [ ] Setup Projektstruktur (z. B. `src/`, `tests/`, `main.py`)
* [ ] Implementiere `crop_and_flip(img: PIL.Image)` als Funktion

  * Rückgabe: Liste von `(filename, PIL.Image)`-Tuples
* [ ] Schreibe Tests mit Beispielbild (aus Datei)

  * Erwartet: exakt **14** Bilder, korrekt benannt

✅ **Ergebnis:** Ein konsolengestütztes Skript, das aus einem Bild ein Dataset erzeugt.

---

### 🌐 PHASE 2: Minimal Webserver (API-Schnittstelle)

**Ziel:** Ein Webserver (Flask oder FastAPI), der ein Bild empfängt und ZIP zurückliefert.

#### Tasks:

* [ ] Starte einen einfachen Flask-Server mit Route `/upload`
* [ ] Form-Data Upload akzeptieren (`POST`)
* [ ] Führe `crop_and_flip()` aus
* [ ] Speichere alle Ergebnisse in einem temporären Ordner oder `io.BytesIO`
* [ ] Erstelle ZIP-Datei dynamisch mit `zipfile`
* [ ] Sende ZIP als `application/zip`-Download

✅ **Ergebnis:** Funktionierende API ohne Frontend – testbar per Postman oder cURL.

---

### 🎨 PHASE 3: Frontend Upload Page (UX Shell)

**Ziel:** Eine HTML-Seite mit einfachem Upload-Interface und Ergebnis-Download.

#### Tasks:

* [ ] Baue einfache HTML5-Seite mit Tailwind CSS
* [ ] Form mit File-Input, Upload-Button, Status-Text
* [ ] POST an `/upload`, Antwort ist ZIP
* [ ] Lade ZIP direkt herunter oder biete Button zum Speichern

✅ **Ergebnis:** Ein funktionierender UX-Prototyp mit grundlegender UI.

---
