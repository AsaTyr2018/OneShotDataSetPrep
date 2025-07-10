from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime


db = SQLAlchemy()


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    can_create_team = db.Column(db.Boolean, default=False)


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    owner = db.relationship("User", backref="owned_teams")


class TeamMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


class Dataset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(120), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    owner = db.relationship("User", backref="datasets")
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"))
    team = db.relationship("Team", backref="datasets")


class DatasetShare(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey("dataset.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


class Setting(db.Model):
    """Key/value store for simple configuration flags."""

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(80), unique=True, nullable=False)
    bool_value = db.Column(db.Boolean, default=True)

    @classmethod
    def get_bool(cls, key: str, default: bool = True) -> bool:
        setting = cls.query.filter_by(key=key).first()
        if setting is None:
            setting = cls(key=key, bool_value=default)
            db.session.add(setting)
            db.session.commit()
        return bool(setting.bool_value)

    @classmethod
    def set_bool(cls, key: str, value: bool) -> None:
        setting = cls.query.filter_by(key=key).first()
        if setting is None:
            setting = cls(key=key, bool_value=value)
            db.session.add(setting)
        else:
            setting.bool_value = value
        db.session.commit()

