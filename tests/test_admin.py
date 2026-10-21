import pytest
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


def test_admin_login_logout_flow(client):
    # GET admin login
    res = client.get("/admin/login")
    assert res.status_code == 200

    # Failed login
    res_fail = client.post("/admin/login", data={"password": "wrongpassword"}, follow_redirects=True)
    assert b"Invalid password." in res_fail.data

    # Successful login
    res_success = client.post("/admin/login", data={"password": "admin"}, follow_redirects=True)
    assert b"Logged in as admin." in res_success.data

    # Access admin panel
    res_panel = client.get("/admin")
    assert res_panel.status_code == 200

    # Logout
    res_logout = client.get("/admin/logout", follow_redirects=True)
    assert b"Logged out." in res_logout.data

    # Unauthenticated access to admin panel redirects
    res_panel_unauth = client.get("/admin", follow_redirects=True)
    assert b"Admin login required." in res_panel_unauth.data


def test_admin_settings_update(client):
    # Login as admin
    client.post("/admin/login", data={"password": "admin"})

    # Update settings
    res = client.post("/admin/settings", data={
        "site_name": "My Custom Wiki",
        "site_footer": "Custom Footer Text",
        "allow_anonymous": "on"
    }, follow_redirects=True)

    assert res.status_code == 200
    assert b"Settings updated." in res.data

    settings = gb.load_settings()
    assert settings["site_name"] == "My Custom Wiki"
    assert settings["site_footer"] == "Custom Footer Text"
    assert settings["allow_anonymous"] is True


def test_admin_delete_page(client):
    gb.write_page("PageToDelete", "Some content")
    assert gb.page_exists("PageToDelete")

    # Unauthenticated deletion attempt redirects to login
    res_unauth = client.post("/PageToDelete/delete", data={"author": "Hacker"}, follow_redirects=True)
    assert b"Admin login required." in res_unauth.data
    assert gb.page_exists("PageToDelete")

    # Authenticated deletion
    client.post("/admin/login", data={"password": "admin"})
    res_auth = client.post("/PageToDelete/delete", data={"author": "AdminUser"}, follow_redirects=True)
    assert b"Page &#39;PageToDelete&#39; deleted." in res_auth.data
    assert not gb.page_exists("PageToDelete")


def test_admin_remotes_routes(client, tmp_path):
    remote_path = str(tmp_path / "remote.git")
    gb._run_git("init", "--bare", remote_path)

    # Unauthenticated attempts redirect
    res_unauth = client.post("/admin/remotes/add", data={"name": "origin", "url": remote_path}, follow_redirects=True)
    assert b"Admin login required." in res_unauth.data

    # Login as admin
    client.post("/admin/login", data={"password": "admin"})

    # Add remote
    res_add = client.post("/admin/remotes/add", data={"name": "origin", "url": remote_path}, follow_redirects=True)
    assert b"Remote &#39;origin&#39; added successfully." in res_add.data
    assert "origin" in gb.list_remotes()

    # Admin panel should list remote
    res_panel = client.get("/admin")
    assert b"origin" in res_panel.data
    assert remote_path.encode() in res_panel.data

    # Fetch remote
    res_fetch = client.post("/admin/remotes/fetch", data={"name": "origin"}, follow_redirects=True)
    assert b"Fetched from remote &#39;origin&#39;." in res_fetch.data

    # Push remote
    res_push = client.post("/admin/remotes/push", data={"name": "origin"}, follow_redirects=True)
    assert b"Pushed to remote &#39;origin&#39;." in res_push.data

    # Pull remote
    res_pull = client.post("/admin/remotes/pull", data={"name": "origin"}, follow_redirects=True)
    assert b"Pulled from remote &#39;origin&#39;." in res_pull.data

    # Remove remote
    res_remove = client.post("/admin/remotes/remove", data={"name": "origin"}, follow_redirects=True)
    assert b"Remote &#39;origin&#39; removed successfully." in res_remove.data
    assert "origin" not in gb.list_remotes()
