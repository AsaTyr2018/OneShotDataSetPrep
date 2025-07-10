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
import random
from datetime import datetime
import shutil

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

from .models import (
    db as models_db,
    User,
    Dataset,
    DatasetShare,
    Setting,
    Team,
    TeamMember,
)

models_db.init_app(app)


@app.context_processor
def inject_settings():
    return {"registration_enabled": Setting.get_bool("registration_enabled", True)}

@login_manager.user_loader
def load_user(user_id):
    with app.app_context():
        return User.query.get(int(user_id))

ARCHIVE_DIR = Path(__file__).resolve().parent.parent / "archives"
ARCHIVE_DIR.mkdir(exist_ok=True)

ARCHIVE_LIMIT_USER = int(os.getenv("ARCHIVE_LIMIT_USER", "10"))
ARCHIVE_LIMIT_TEAM = int(os.getenv("ARCHIVE_LIMIT_TEAM", "10"))


def cleanup_archives(owner_id: int, team_id: int | None = None) -> None:
    limit = ARCHIVE_LIMIT_TEAM if team_id else ARCHIVE_LIMIT_USER
    q = Dataset.query.filter_by(owner_id=owner_id, team_id=team_id).order_by(
        Dataset.timestamp.desc()
    )
    datasets = q.all()
    base_dir = ARCHIVE_DIR / f"team_{team_id}" if team_id else ARCHIVE_DIR
    for old_ds in datasets[limit:]:
        path = base_dir / old_ds.filename
        DatasetShare.query.filter_by(dataset_id=old_ds.id).delete()
        models_db.session.delete(old_ds)
        models_db.session.commit()
        path.unlink(missing_ok=True)


@app.route("/register", methods=["GET", "POST"])
def register():
    if not Setting.get_bool("registration_enabled", True):
        return "Registration disabled", 403
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


@app.route("/teams/create", methods=["GET", "POST"])
@login_required
def create_team():
    if request.method == "POST":
        name = request.form.get("name")
        if not name:
            return "Invalid", 400
        team = Team(name=name, owner_id=current_user.id)
        models_db.session.add(team)
        models_db.session.commit()
        models_db.session.add(TeamMember(team_id=team.id, user_id=current_user.id))
        models_db.session.commit()
        return redirect(url_for("manage_team", team_id=team.id))
    return render_template("create_team.html")


@app.route("/teams/<int:team_id>", methods=["GET"])
@login_required
def manage_team(team_id: int):
    team = Team.query.get_or_404(team_id)
    if team.owner_id != current_user.id:
        return "Forbidden", 403
    members = (
        User.query.join(TeamMember, TeamMember.user_id == User.id)
        .filter(TeamMember.team_id == team_id)
        .all()
    )
    return render_template("manage_team.html", team=team, members=members)


@app.route("/teams/<int:team_id>/add", methods=["POST"])
@login_required
def add_member(team_id: int):
    team = Team.query.get_or_404(team_id)
    if team.owner_id != current_user.id:
        return "Forbidden", 403
    username = request.form.get("username")
    user = User.query.filter_by(username=username).first()
    if user and not TeamMember.query.filter_by(team_id=team_id, user_id=user.id).first():
        models_db.session.add(TeamMember(team_id=team_id, user_id=user.id))
        models_db.session.commit()
    return redirect(url_for("manage_team", team_id=team_id))


@app.route("/teams/<int:team_id>/remove/<int:user_id>", methods=["POST"])
@login_required
def remove_member(team_id: int, user_id: int):
    team = Team.query.get_or_404(team_id)
    if team.owner_id != current_user.id:
        return "Forbidden", 403
    if user_id == current_user.id:
        return "Invalid", 400
    TeamMember.query.filter_by(team_id=team_id, user_id=user_id).delete()
    models_db.session.commit()
    return redirect(url_for("manage_team", team_id=team_id))


@app.route("/teams/<int:team_id>/delete", methods=["POST"])
@login_required
def delete_team(team_id: int):
    team = Team.query.get_or_404(team_id)
    if team.owner_id != current_user.id:
        return "Forbidden", 403
    datasets = Dataset.query.filter_by(team_id=team_id).all()
    base_dir = ARCHIVE_DIR / f"team_{team_id}"
    for ds in datasets:
        (base_dir / ds.filename).unlink(missing_ok=True)
        DatasetShare.query.filter_by(dataset_id=ds.id).delete()
        models_db.session.delete(ds)
    TeamMember.query.filter_by(team_id=team_id).delete()
    models_db.session.delete(team)
    models_db.session.commit()
    shutil.rmtree(base_dir, ignore_errors=True)
    return redirect(url_for("index"))


@app.route("/teams/<int:team_id>/archive", methods=["GET"])
@login_required
def team_archive(team_id: int):
    team = Team.query.get_or_404(team_id)
    membership = TeamMember.query.filter_by(team_id=team_id, user_id=current_user.id).first()
    if not membership:
        return "Forbidden", 403
    datasets = (
        Dataset.query.filter_by(team_id=team_id)
        .order_by(Dataset.timestamp.desc())
        .all()
    )
    return render_template("team_archive.html", team=team, datasets=datasets)


@app.route("/", methods=["GET"])
@login_required
def index():
    """Render upload form page with archive list."""
    owned = Dataset.query.filter_by(owner_id=current_user.id, team_id=None)
    team_ids = [m.team_id for m in TeamMember.query.filter_by(user_id=current_user.id)]
    team_datasets = Dataset.query.filter(Dataset.team_id.in_(team_ids)) if team_ids else []
    shared_ids = [s.dataset_id for s in DatasetShare.query.filter_by(user_id=current_user.id)]
    shared = Dataset.query.filter(Dataset.id.in_(shared_ids)) if shared_ids else []
    datasets = list(owned) + list(shared) + list(team_datasets)
    datasets = datasets[-10:]
    teams = Team.query.join(TeamMember).filter(TeamMember.user_id==current_user.id).all()
    return render_template("index.html", datasets=datasets, teams=teams)

@app.route("/upload", methods=["POST"])
@login_required
def upload():
    """Receive an image via form-data and return a ZIP of processed images."""
    file = request.files.get("image")
    if not file or file.filename == "":
        return "No file provided", 400

    team_id_raw = request.form.get("team_id")
    team_id = int(team_id_raw) if team_id_raw else None
    if team_id:
        membership = TeamMember.query.filter_by(team_id=team_id, user_id=current_user.id).first()
        if not membership:
            return "Forbidden", 403
        team_dir = ARCHIVE_DIR / f"team_{team_id}"
        team_dir.mkdir(exist_ok=True)
    else:
        team_dir = ARCHIVE_DIR

    img = Image.open(file.stream)
    base_name = Path(file.filename).stem
    ext = file.filename.split(".")[-1]

    result_images = crop_and_flip(img, base_name, ext)

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for filename, img_buffer in result_images:
            zipf.writestr(filename, img_buffer.read())

    zip_buffer.seek(0)

    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    random_part = random.randint(0, 99999)
    archive_name = f"{current_user.username}_{timestamp}_{random_part:05}.zip"
    archive_path = team_dir / archive_name
    with open(archive_path, "wb") as f:
        f.write(zip_buffer.getvalue())

    dataset = Dataset(filename=archive_name, owner_id=current_user.id, team_id=team_id)
    models_db.session.add(dataset)
    models_db.session.commit()

    cleanup_archives(current_user.id, team_id)

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
    base_dir = ARCHIVE_DIR
    if dataset.team_id:
        base_dir = base_dir / f"team_{dataset.team_id}"
    return send_from_directory(base_dir, filename, as_attachment=True)


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

    base_dir = ARCHIVE_DIR / f"team_{dataset.team_id}" if dataset.team_id else ARCHIVE_DIR
    path = base_dir / dataset.filename
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
        action = request.form.get("action")
        if action == "create_user":
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
        elif action == "toggle_registration":
            enabled = request.form.get("registration_enabled") == "on"
            Setting.set_bool("registration_enabled", enabled)
            return redirect(url_for("admin_users"))
    users = User.query.all()
    reg_enabled = Setting.get_bool("registration_enabled", True)
    return render_template("admin_users.html", users=users, registration_enabled=reg_enabled)


@app.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@login_required
def admin_delete_user(user_id: int):
    if not current_user.is_admin:
        return "Forbidden", 403
    user = User.query.get(user_id)
    if user:
        DatasetShare.query.filter_by(user_id=user.id).delete()
        Dataset.query.filter_by(owner_id=user.id).delete()
        TeamMember.query.filter_by(user_id=user.id).delete()
        Team.query.filter_by(owner_id=user.id).delete()
        models_db.session.delete(user)
        models_db.session.commit()
    return redirect(url_for("admin_users"))


with app.app_context():
    models_db.create_all()


