from flask import Flask, request, send_file, render_template, send_from_directory, redirect, url_for
from PIL import Image
from io import BytesIO
import zipfile
from pathlib import Path
import os
import time

from .processing import crop_and_flip


app = Flask(
    __name__,
    template_folder=str(Path(__file__).resolve().parent.parent / "templates"),
    static_folder=str(Path(__file__).resolve().parent.parent / "static"),
)

ARCHIVE_DIR = Path(__file__).resolve().parent.parent / "archives"
ARCHIVE_DIR.mkdir(exist_ok=True)


@app.route("/", methods=["GET"])
def index():
    """Render upload form page with archive list."""
    archive_files = sorted(
        ARCHIVE_DIR.glob("*.zip"), key=os.path.getmtime, reverse=True
    )
    filenames = [f.name for f in archive_files][:10]
    return render_template("index.html", archives=filenames)

@app.route("/upload", methods=["POST"])
def upload():
    """Receive an image via form-data and return a ZIP of processed images."""
    file = request.files.get("image")
    if not file or file.filename == "":
        return "No file provided", 400

    img = Image.open(file.stream)
    base_name = Path(file.filename).stem
    ext = file.filename.split(".")[-1]

    result_images = crop_and_flip(img, base_name, ext)

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for filename, img_buffer in result_images:
            zipf.writestr(filename, img_buffer.read())

    zip_buffer.seek(0)

    archive_name = f"{base_name}_{int(time.time())}.zip"
    archive_path = ARCHIVE_DIR / archive_name
    with open(archive_path, "wb") as f:
        f.write(zip_buffer.getvalue())

    archives = sorted(ARCHIVE_DIR.glob("*.zip"), key=os.path.getmtime, reverse=True)
    for old in archives[10:]:
        old.unlink(missing_ok=True)

    return redirect(url_for("index"))


@app.route("/download/<path:filename>", methods=["GET"])
def download(filename: str):
    """Download a dataset from the archive."""
    return send_from_directory(ARCHIVE_DIR, filename, as_attachment=True)


