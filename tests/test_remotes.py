import subprocess
import pytest
import gitwiki.git_backend as gb
from gitwiki.app import create_app


@pytest.fixture
def repo_env(tmp_path, monkeypatch):
    test_pages_dir = str(tmp_path / "wiki_pages")
    monkeypatch.setattr(gb, "PAGES_DIR", test_pages_dir)
    settings_path = str(tmp_path / "gitwiki_settings.json")
    monkeypatch.setattr(gb, "SETTINGS_FILE", settings_path)
    gb.init_repo()

    # Create a bare remote repo to push/pull against
    remote_dir = str(tmp_path / "remote.git")
    subprocess.run(["git", "init", "--bare", remote_dir], check=True)

    return {"pages_dir": test_pages_dir, "remote_dir": remote_dir}


@pytest.fixture
def client(repo_env):
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_git_backend_remote_operations(repo_env):
    remote_url = repo_env["remote_dir"]

    # List initially empty remotes
    assert gb.list_remotes() == []

    # Add remote
    gb.add_remote("origin", remote_url)
    remotes = gb.list_remotes()
    assert len(remotes) == 1
    assert remotes[0]["name"] == "origin"
    assert remotes[0]["fetch_url"] == remote_url
    assert remotes[0]["push_url"] == remote_url

    # Invalid names / inputs
    with pytest.raises(ValueError):
        gb.add_remote("", remote_url)
    with pytest.raises(ValueError):
        gb.add_remote("bad name!", remote_url)
    with pytest.raises(ValueError):
        gb.remove_remote("invalid name!")

    # Push to remote
    push_res = gb.push_remote("origin")
    assert push_res == "" or push_res is not None

    # Fetch from remote
    fetch_res = gb.fetch_remote("origin")
    assert fetch_res == "" or fetch_res is not None

    # Pull from remote
    pull_res = gb.pull_remote("origin")
    assert pull_res == "" or pull_res is not None

    # Remove remote
    gb.remove_remote("origin")
    assert gb.list_remotes() == []


def test_auto_push_on_write(repo_env):
    remote_url = repo_env["remote_dir"]
    gb.add_remote("origin", remote_url)

    # Enable auto_push
    settings = gb.load_settings()
    settings["auto_push"] = True
    settings["default_remote"] = "origin"
    gb.save_settings(settings)

    # Initial push so remote has branch
    gb.push_remote("origin")

    # Writing page should auto-push without error
    gb.write_page("AutoPushedPage", "Some content", author="TestUser")

    # Verify commit exists in bare remote repo
    log = subprocess.run(
        ["git", "log", "--oneline"],
        cwd=remote_url,
        capture_output=True,
        text=True,
        check=True
    ).stdout
    assert "AutoPushedPage" in log or "Edit page" in log


def test_admin_remote_routes(client, repo_env):
    remote_url = repo_env["remote_dir"]

    # Unauthenticated requests redirect to login
    res_unauth = client.post("/admin/remotes/add", data={"name": "origin", "url": remote_url}, follow_redirects=True)
    assert b"Admin login required." in res_unauth.data

    # Login as admin
    client.post("/admin/login", data={"password": "admin"})

    # Add remote via route
    res_add = client.post("/admin/remotes/add", data={"name": "origin", "url": remote_url}, follow_redirects=True)
    assert b"Remote &#39;origin&#39; added successfully." in res_add.data
    assert b"origin" in res_add.data

    # Push via route
    res_push = client.post("/admin/remotes/push", data={"name": "origin"}, follow_redirects=True)
    assert b"Pushed to remote &#39;origin&#39;." in res_push.data

    # Fetch via route
    res_fetch = client.post("/admin/remotes/fetch", data={"name": "origin"}, follow_redirects=True)
    assert b"Fetched from remote &#39;origin&#39;." in res_fetch.data

    # Pull via route
    res_pull = client.post("/admin/remotes/pull", data={"name": "origin"}, follow_redirects=True)
    assert b"Pulled from remote &#39;origin&#39;." in res_pull.data

    # Update admin settings with auto_push and default_remote
    res_settings = client.post("/admin/settings", data={
        "site_name": "RemoteWiki",
        "site_footer": "Footer",
        "auto_push": "on",
        "default_remote": "origin"
    }, follow_redirects=True)
    assert b"Settings updated." in res_settings.data

    settings = gb.load_settings()
    assert settings["auto_push"] is True
    assert settings["default_remote"] == "origin"

    # Remove remote via route
    res_remove = client.post("/admin/remotes/remove", data={"name": "origin"}, follow_redirects=True)
    assert b"Remote &#39;origin&#39; removed successfully." in res_remove.data
