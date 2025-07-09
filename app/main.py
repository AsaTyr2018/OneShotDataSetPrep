from flask import (
    Flask,
    request,
    render_template,
    send_from_directory,
    redirect,
    url_for,
)
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
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
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "replace-me"
login_manager = LoginManager(app)
login_manager.login_view = "login"

from .models import db as models_db, User, Dataset, DatasetShare

models_db.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    with app.app_context():
        return User.query.get(int(user_id))

ARCHIVE_DIR = Path(__file__).resolve().parent.parent / "archives"
ARCHIVE_DIR.mkdir(exist_ok=True)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if User.query.filter_by(username=username).first():
            return "User exists", 400
        user = User(username=username, password_hash=generate_password_hash(password))
        models_db.session.add(user)
        models_db.session.commit()
        login_user(user)
        return redirect(url_for("index"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("index"))
        return "Invalid credentials", 400
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/", methods=["GET"])
@login_required
def index():
    """Render upload form page with archive list."""
    owned = Dataset.query.filter_by(owner_id=current_user.id)
    shared_ids = [s.dataset_id for s in DatasetShare.query.filter_by(user_id=current_user.id)]
    shared = Dataset.query.filter(Dataset.id.in_(shared_ids)) if shared_ids else []
    datasets = list(owned) + list(shared)
    datasets = datasets[-10:]
    return render_template("index.html", datasets=datasets)

@app.route("/upload", methods=["POST"])
@login_required
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

    dataset = Dataset(filename=archive_name, owner_id=current_user.id)
    models_db.session.add(dataset)
    models_db.session.commit()

    archives = sorted(ARCHIVE_DIR.glob("*.zip"), key=os.path.getmtime, reverse=True)
    for old in archives[10:]:
        dataset = Dataset.query.filter_by(filename=old.name).first()
        if dataset:
            DatasetShare.query.filter_by(dataset_id=dataset.id).delete()
            models_db.session.delete(dataset)
            models_db.session.commit()
        old.unlink(missing_ok=True)

    return redirect(url_for("index"))


@app.route("/download/<path:filename>", methods=["GET"])
@login_required
def download(filename: str):
    """Download a dataset from the archive if permitted."""
    dataset = Dataset.query.filter_by(filename=filename).first()
    allowed = dataset and (
        dataset.owner_id == current_user.id
        or DatasetShare.query.filter_by(dataset_id=dataset.id, user_id=current_user.id).first()
    )
    if not allowed:
        return "Forbidden", 403
    return send_from_directory(ARCHIVE_DIR, filename, as_attachment=True)


@app.route("/share/<int:dataset_id>", methods=["POST"])
@login_required
def share(dataset_id: int):
    username = request.form.get("username")
    user = User.query.filter_by(username=username).first()
    dataset = Dataset.query.get(dataset_id)
    if not user or not dataset or dataset.owner_id != current_user.id:
        return "Not allowed", 400
    if not DatasetShare.query.filter_by(dataset_id=dataset_id, user_id=user.id).first():
        models_db.session.add(DatasetShare(dataset_id=dataset_id, user_id=user.id))
        models_db.session.commit()
    return redirect(url_for("index"))


@app.route("/delete/<int:dataset_id>", methods=["POST"])
@login_required
def delete_dataset(dataset_id: int):
    """Remove a dataset if the current user is the owner."""
    dataset = Dataset.query.get(dataset_id)
    if not dataset or dataset.owner_id != current_user.id:
        return "Forbidden", 403

    path = ARCHIVE_DIR / dataset.filename
    path.unlink(missing_ok=True)
    DatasetShare.query.filter_by(dataset_id=dataset_id).delete()
    models_db.session.delete(dataset)
    models_db.session.commit()
    return redirect(url_for("index"))


@app.route("/admin/users", methods=["GET", "POST"])
@login_required
def admin_users():
    if not current_user.is_admin:
        return "Forbidden", 403
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not username or not password:
            return "Invalid", 400
        if User.query.filter_by(username=username).first():
            return "User exists", 400
        user = User(username=username, password_hash=generate_password_hash(password))
        models_db.session.add(user)
        models_db.session.commit()
        return redirect(url_for("admin_users"))
    users = User.query.all()
    return render_template("admin_users.html", users=users)


@app.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@login_required
def admin_delete_user(user_id: int):
    if not current_user.is_admin:
        return "Forbidden", 403
    user = User.query.get(user_id)
    if user:
        DatasetShare.query.filter_by(user_id=user.id).delete()
        Dataset.query.filter_by(owner_id=user.id).delete()
        models_db.session.delete(user)
        models_db.session.commit()
    return redirect(url_for("admin_users"))


with app.app_context():
    models_db.create_all()


