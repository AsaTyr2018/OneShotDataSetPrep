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

# 📚 Technical Documentation – `OneShotDataSetPrep`

## 🧱 Stack Overview

| Komponente        | Technologie                     |
| ----------------- | ------------------------------- |
| Backend Framework | **Flask 3.x** (WSGI-kompatibel) |
| Image Processing  | **Pillow (PIL)**                |
| ZIP Packaging     | **zipfile + io.BytesIO**        |
| Frontend          | **HTML5 + Tailwind CSS**        |
| Temp Handling     | **tempfile**                    |
| Environment       | **Python 3.12**                 |

---

## 📁 Projektstruktur

```plaintext
oneshotdatasetprep/
├── app/
│   ├── __init__.py
│   ├── main.py              # Flask-Server & Routing
│   ├── processing.py        # Crop & Flip Logik
│   └── utils.py             # Save, Logging, Helpers
├── static/
│   └── tailwind.min.css     # Styling
├── templates/
│   └── index.html           # Upload-Oberfläche
├── tests/
│   └── test_processing.py   # Unittests für Bildlogik
├── requirements.txt
└── run.py                   # Einstiegspunkt (Flask App)
```

---

## ⚙️ Installation & Start

### 🧪 Lokale Umgebung:

```bash
# Python venv anlegen
python3.12 -m venv venv
source venv/bin/activate

# Abhängigkeiten installieren
pip install -r requirements.txt

# Server starten
python run.py
```

Zugriff: [http://{serverip}:7860](http://{serverip}:7860)

---

## 🖼️ Bildverarbeitung: `processing.py`

```python
from PIL import Image
from pathlib import Path
from io import BytesIO

def crop_and_flip(image: Image.Image, base_name: str, ext: str) -> list[tuple[str, BytesIO]]:
    w, h = image.size
    outputs = []

    def add(img: Image.Image, suffix: str):
        buffer = BytesIO()
        filename = f"{base_name}_{suffix}.{ext}"
        img.save(buffer, format=image.format)
        buffer.seek(0)
        outputs.append((filename, buffer))

    # Original
    add(image, "original")

    # Crops
    crops = {
        "top_half":      (0, 0, w, h // 2),
        "bottom_half":   (0, h // 2, w, h),
        "top_left":      (0, 0, w // 2, h // 2),
        "top_right":     (w // 2, 0, w, h // 2),
        "bottom_left":   (0, h // 2, w // 2, h),
        "bottom_right":  (w // 2, h // 2, w, h),
    }

    for name, box in crops.items():
        cropped = image.crop(box)
        add(cropped, name)

    # Flip all existing
    originals = outputs.copy()
    for filename, buffer in originals:
        img = Image.open(buffer)
        flipped = img.transpose(Image.FLIP_LEFT_RIGHT)
        flip_name = filename.replace(f".{ext}", "_flip." + ext)
        flip_buffer = BytesIO()
        flipped.save(flip_buffer, format=img.format)
        flip_buffer.seek(0)
        outputs.append((flip_name, flip_buffer))

    return outputs
```

---

## 🌐 Webserver: `main.py`

```python
from flask import Flask, request, render_template, send_file
from PIL import Image
from io import BytesIO
import zipfile
import tempfile
from .processing import crop_and_flip

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["image"]
    if not file or file.filename == "":
        return "No file provided", 400

    img = Image.open(file.stream)
    base_name = Path(file.filename).stem
    ext = file.filename.split('.')[-1]

    result_images = crop_and_flip(img, base_name, ext)

    # ZIP-Erstellung
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for filename, img_buffer in result_images:
            zipf.writestr(filename, img_buffer.read())

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"{base_name}_dataset.zip"
    )
```

---

## 🖥️ Frontend: `index.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>OneShot Dataset Prep</title>
    <link rel="stylesheet" href="/static/tailwind.min.css">
</head>
<body class="bg-gray-100 text-center p-8">
    <h1 class="text-3xl font-bold mb-4">OneShot Dataset Prep</h1>
    <form action="/upload" method="POST" enctype="multipart/form-data" class="bg-white p-6 rounded shadow-md inline-block">
        <input type="file" name="image" accept="image/*" required class="mb-4"><br>
        <button type="submit" class="bg-blue-600 text-white px-4 py-2 rounded">Upload & Generate ZIP</button>
    </form>
</body>
</html>
```

---

## 🧪 Tests: `test_processing.py`

```python
from app.processing import crop_and_flip
from PIL import Image
from io import BytesIO

def test_crop_and_flip():
    img = Image.new("RGB", (400, 400), color="red")
    result = crop_and_flip(img, "test", "jpg")
    assert len(result) == 14
    filenames = [name for name, _ in result]
    assert "test_top_left_flip.jpg" in filenames
```

---

## 📦 Abhängigkeiten: `requirements.txt`

```txt
flask>=3.0.0
pillow>=10.0.0
```

---

## ✅ Ergebnis nach Upload

Beispiel-Dateien im ZIP (für `input.jpg`):

```
input_original.jpg
input_original_flip.jpg
input_top_half.jpg
input_top_half_flip.jpg
input_bottom_half.jpg
input_bottom_half_flip.jpg
input_top_left.jpg
input_top_left_flip.jpg
input_top_right.jpg
input_top_right_flip.jpg
input_bottom_left.jpg
input_bottom_left_flip.jpg
input_bottom_right.jpg
input_bottom_right_flip.jpg
```

