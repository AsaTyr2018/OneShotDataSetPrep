from flask import Flask, request, send_file, render_template
from PIL import Image
from io import BytesIO
import zipfile
from pathlib import Path

from .processing import crop_and_flip


app = Flask(
    __name__,
    template_folder=str(Path(__file__).resolve().parent.parent / "templates"),
    static_folder=str(Path(__file__).resolve().parent.parent / "static"),
)


@app.route("/", methods=["GET"])
def index():
    """Render upload form page."""
    return render_template("index.html")

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
    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"{base_name}_dataset.zip",
    )


