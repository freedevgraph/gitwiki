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


def test_dark_mode_button_in_base_template(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b'id="theme-toggle"' in response.data
    assert b'aria-label="Toggle dark mode"' in response.data
    assert b'localStorage.getItem(\'theme\')' in response.data
    assert b'data-theme' in response.data


def test_dark_mode_css_present(client):
    response = client.get("/static/css/style.css")
    assert response.status_code == 200
    assert b'[data-theme="dark"]' in response.data
    assert b'--bg: #121212;' in response.data
    assert b'--surface: #1e1e1e;' in response.data
