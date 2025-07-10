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


def test_team_member_can_download(tmp_path, monkeypatch):
    from werkzeug.security import generate_password_hash
    from app import main

    monkeypatch.setattr(main, 'ARCHIVE_DIR', tmp_path)
    main.app.config['TESTING'] = True
    main.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with main.app.app_context():
        main.models_db.drop_all()
        main.models_db.create_all()

        owner = main.User(username='owner', password_hash=generate_password_hash('a'))
        member = main.User(username='member', password_hash=generate_password_hash('b'))
        main.models_db.session.add_all([owner, member])
        main.models_db.session.commit()

        team = main.Team(name='t', owner_id=owner.id)
        main.models_db.session.add(team)
        main.models_db.session.commit()

        main.models_db.session.add_all([
            main.TeamMember(team_id=team.id, user_id=owner.id),
            main.TeamMember(team_id=team.id, user_id=member.id),
        ])
        ds = main.Dataset(filename='x.zip', owner_id=owner.id, team_id=team.id)
        main.models_db.session.add(ds)
        main.models_db.session.commit()
        team_id = team.id
        filename = ds.filename

    team_dir = tmp_path / f'team_{team_id}'
    team_dir.mkdir(parents=True, exist_ok=True)
    (team_dir / filename).write_bytes(b'data')

    client = main.app.test_client()
    client.post('/login', data={'username': 'member', 'password': 'b'})
    resp = client.get(f'/download/{filename}')
    assert resp.status_code == 200
