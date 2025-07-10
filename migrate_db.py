#!/usr/bin/env python3
from app.models import db
from app.main import app
from sqlalchemy import inspect, text


def run_migrations() -> None:
    """Apply pending SQLite schema updates."""
    with app.app_context():
        inspector = inspect(db.engine)
        cols = [c["name"] for c in inspector.get_columns("dataset")]
        if "team_id" not in cols:
            db.session.execute(
                text("ALTER TABLE dataset ADD COLUMN team_id INTEGER")
            )
            db.session.commit()
        cols = [c["name"] for c in inspector.get_columns("user")]
        if "can_create_team" not in cols:
            db.session.execute(
                text("ALTER TABLE user ADD COLUMN can_create_team BOOLEAN DEFAULT 0")
            )
            db.session.commit()
        db.create_all()


if __name__ == "__main__":
    run_migrations()
