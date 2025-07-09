#!/bin/bash

APP_DIR="/opt/OneShot"
SERVICE_FILE="/etc/systemd/system/oneshot.service"
VENV="$APP_DIR/venv"

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root" >&2
    exit 1
fi

cat > "$SERVICE_FILE" <<SERVICE
[Unit]
Description=OneShot Dataset Prep Service
After=network.target

[Service]
Type=simple
WorkingDirectory=$APP_DIR
ExecStart=$VENV/bin/python $APP_DIR/run.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable --now oneshot.service

echo "Service installed and started"
