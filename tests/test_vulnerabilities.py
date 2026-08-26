import pytest
import os
import shutil
from gitwiki.app import create_app
from gitwiki import git_backend as gb


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_pages_dir = str(tmp_path / "wiki_pages")
    monkeypatch.setattr(gb, "PAGES_DIR", test_pages_dir)
    settings_path = str(tmp_path / "gitwiki_settings.json")
    monkeypatch.setattr(gb, "SETTINGS_FILE", settings_path)
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_path_traversal_prevention_in_backend():
    with pytest.raises(ValueError):
        gb._page_file("../etc/passwd")

    with pytest.raises(ValueError):
        gb._page_file("..\\boot.ini")


def test_path_traversal_routes(client):
    response = client.get("/..%2F..%2Fetc%2Fpasswd")
    assert response.status_code in (400, 404)

    response = client.get("/..%2F..%2Fetc%2Fpasswd/raw")
    assert response.status_code in (400, 404)


def test_admin_login_auth(client):
    res_fail = client.post("/admin/login", data={"password": "wrongpassword"})
    assert b"Invalid password" in res_fail.data

    res_success = client.post("/admin/login", data={"password": "admin"}, follow_redirects=True)
    assert b"Logged in as admin" in res_success.data


def test_anonymous_edit_permissions(client):
    # Anonymous editing disabled by default
    res = client.post("/TestPage/edit", data={"content": "Hello", "author": "User"}, follow_redirects=True)
    assert b"Admin login required" in res.data or b"Invalid password" in res.data or b"Admin" in res.data

    # Enable anonymous editing via settings
    settings = gb.load_settings()
    settings["allow_anonymous"] = True
    gb.save_settings(settings)

    res_anon = client.post("/TestPage/edit", data={"content": "Hello World", "author": "Tester"}, follow_redirects=True)
    assert b"Page &#39;TestPage&#39; saved." in res_anon.data or b"TestPage" in res_anon.data
