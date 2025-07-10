from io import BytesIO
from PIL import Image
from werkzeug.security import generate_password_hash
from app import main


def setup_user(tmp_path, monkeypatch):
    monkeypatch.setattr(main, 'ARCHIVE_DIR', tmp_path)
    monkeypatch.setattr(main, 'ARCHIVE_LIMIT_USER', 1)
    main.app.config['TESTING'] = True
    main.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with main.app.app_context():
        main.models_db.drop_all()
        main.models_db.create_all()
        user = main.User(username='u', password_hash=generate_password_hash('a'))
        main.models_db.session.add(user)
        main.models_db.session.commit()
        return user.id


def test_user_directory_and_quota(tmp_path, monkeypatch):
    user_id = setup_user(tmp_path, monkeypatch)
    client = main.app.test_client()
    client.post('/login', data={'username': 'u', 'password': 'a'})

    img = Image.new('RGB', (10, 10), color='red')
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)

    resp1 = client.post('/upload', data={'image': (buf, 'a.png')}, content_type='multipart/form-data')
    assert resp1.status_code == 302
    buf2 = BytesIO()
    img.save(buf2, format='PNG')
    buf2.seek(0)
    resp2 = client.post('/upload', data={'image': (buf2, 'b.png')}, content_type='multipart/form-data')
    assert resp2.status_code == 400
    user_dir = tmp_path / f'user_{user_id}'
    assert any(user_dir.iterdir())
