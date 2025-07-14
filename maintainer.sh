#!/bin/bash

is_docker() {
    [ -f "/.dockerenv" ] && return 0
    grep -qE '(docker|lxc)' /proc/1/cgroup 2>/dev/null
}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if is_docker; then
    APP_DIR="$SCRIPT_DIR"
else
    APP_DIR="/opt/OneShot"
fi
VENV="$APP_DIR/venv"
REPO="https://github.com/AsaTyr2018/OneShotDataSetPrep.git"

python_cmd() {
    if [ -x "$VENV/bin/python" ]; then
        echo "$VENV/bin/python"
    elif is_docker; then
        command -v python3 || command -v python
    fi
}

ensure_installed() {
    [ -d "$VENV" ] && return 0
    is_docker && return 0
    echo "Not installed" >&2
    return 1
}

install() {
    if [ -d "$APP_DIR" ]; then
        echo "Already installed at $APP_DIR" >&2
        return
    fi
    git clone "$REPO" "$APP_DIR"
    python3 -m venv "$VENV"
    "$VENV/bin/pip" install -r "$APP_DIR/requirements.txt"
    echo "Installed to $APP_DIR"

    read -r -p "Install systemd service? [y/N] " ans
    if [[ $ans =~ ^[Yy]$ ]]; then
        "$APP_DIR/install_service.sh"
    fi
}

update() {
    [ -d "$APP_DIR" ] || { echo "Not installed" >&2; return; }
    local was_active=0
    if systemctl is-active --quiet oneshot.service; then
        was_active=1
    fi
    git -C "$APP_DIR" pull
    "$VENV/bin/pip" install -r "$APP_DIR/requirements.txt"
    if [ -f "$APP_DIR/migrate_db.py" ]; then
        "$VENV/bin/python" "$APP_DIR/migrate_db.py"
    fi
    if [ $was_active -eq 1 ]; then
        systemctl restart oneshot.service
    fi
}

uninstall() {
    rm -rf "$APP_DIR"
}

start() {
    ensure_installed || return
    "$(python_cmd)" "$APP_DIR/run.py"
}

create_admin() {
    ensure_installed || return
    local user=$1
    local pass=$2
    "$(python_cmd)" - <<PY
from app.models import db, User
from app.main import app
from werkzeug.security import generate_password_hash
with app.app_context():
    u = User.query.filter_by(username='$user').first()
    if not u:
        u = User(username='$user', password_hash=generate_password_hash('$pass'), is_admin=True)
        db.session.add(u)
        db.session.commit()
PY
}

case "$1" in
    install) install ;;
    update) update ;;
    uninstall) uninstall ;;
    start) start ;;
    create-admin) shift; create_admin "$@" ;;
    *) echo "Usage: $0 {install|update|uninstall|start|create-admin <user> <pass>}" ;;
esac
