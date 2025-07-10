import sys
from pathlib import Path
from io import BytesIO
from PIL import Image
from werkzeug.security import generate_password_hash
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import main


def setup_env(tmp_path, monkeypatch):
    monkeypatch.setattr(main, 'ARCHIVE_DIR', tmp_path)
    main.app.config['TESTING'] = True
    main.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with main.app.app_context():
        main.models_db.drop_all()
        main.models_db.create_all()


def create_image():
    img = Image.new('RGB', (10, 10), color='red')
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf


def test_preview_stored_on_upload(tmp_path, monkeypatch):
    setup_env(tmp_path, monkeypatch)
    with main.app.app_context():
        user = main.User(username='u', password_hash=generate_password_hash('a'))
        main.models_db.session.add(user)
        main.models_db.session.commit()
        uid = user.id
    client = main.app.test_client()
    client.post('/login', data={'username': 'u', 'password': 'a'})
    buf = create_image()
    resp = client.post('/upload', data={'image': (buf, 'a.png')}, content_type='multipart/form-data')
    assert resp.status_code == 302
    with main.app.app_context():
        ds = main.Dataset.query.filter_by(owner_id=uid).first()
        preview = tmp_path / f'user_{uid}' / ds.filename[:-4]
        assert preview.exists()
        assert len(list(preview.iterdir())) == 14


def test_team_preview_accessible(tmp_path, monkeypatch):
    setup_env(tmp_path, monkeypatch)
    with main.app.app_context():
        owner = main.User(username='o', password_hash=generate_password_hash('x'))
        member = main.User(username='m', password_hash=generate_password_hash('y'))
        main.models_db.session.add_all([owner, member])
        main.models_db.session.commit()
        team = main.Team(name='t', owner_id=owner.id)
        main.models_db.session.add(team)
        main.models_db.session.commit()
        main.models_db.session.add_all([
            main.TeamMember(team_id=team.id, user_id=owner.id),
            main.TeamMember(team_id=team.id, user_id=member.id),
        ])
        main.models_db.session.commit()
        team_id = team.id
    client = main.app.test_client()
    client.post('/login', data={'username': 'o', 'password': 'x'})
    buf = create_image()
    client.post('/upload', data={'image': (buf, 'a.png'), 'team_id': team_id}, content_type='multipart/form-data')
    with main.app.app_context():
        ds = main.Dataset.query.filter_by(team_id=team_id).first()
        ds_id = ds.id
    client.post('/login', data={'username': 'm', 'password': 'y'})
    resp = client.get(f'/preview/{ds_id}')
    assert resp.status_code == 200


def test_preview_removed_on_delete(tmp_path, monkeypatch):
    setup_env(tmp_path, monkeypatch)
    with main.app.app_context():
        user = main.User(username='u', password_hash=generate_password_hash('a'))
        main.models_db.session.add(user)
        main.models_db.session.commit()
        uid = user.id
    client = main.app.test_client()
    client.post('/login', data={'username': 'u', 'password': 'a'})
    buf = create_image()
    client.post('/upload', data={'image': (buf, 'a.png')}, content_type='multipart/form-data')
    with main.app.app_context():
        ds = main.Dataset.query.filter_by(owner_id=uid).first()
        preview = tmp_path / f'user_{uid}' / ds.filename[:-4]
        assert preview.exists()
        did = ds.id
    resp = client.post(f'/delete/{did}')
    assert resp.status_code == 302
    assert not preview.exists()
