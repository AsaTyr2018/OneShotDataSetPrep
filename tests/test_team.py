from flask import Flask
from app.models import db, User, Team, TeamMember, Dataset


def setup_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    with app.app_context():
        db.create_all()
    return app


def test_team_creation_and_dataset():
    app = setup_app()
    with app.app_context():
        user = User(username='u', password_hash='x')
        db.session.add(user)
        db.session.commit()
        team = Team(name='t', owner_id=user.id)
        db.session.add(team)
        db.session.commit()
        member = TeamMember(team_id=team.id, user_id=user.id)
        db.session.add(member)
        ds = Dataset(filename='a.zip', owner_id=user.id, team_id=team.id)
        db.session.add(ds)
        db.session.commit()
        assert Team.query.count() == 1
        assert TeamMember.query.count() == 1
        assert Dataset.query.filter_by(team_id=team.id).first() is not None
