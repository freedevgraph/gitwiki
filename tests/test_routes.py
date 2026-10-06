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


def test_index_route(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"Welcome to GitWiki" in res.data or b"Main_Page" in res.data


def test_view_page_exists_and_not_exists(client):
    # Existing page Main_Page created during init_repo
    res = client.get("/Main_Page")
    assert res.status_code == 200
    assert b"Welcome to GitWiki" in res.data

    # Non-existing page without action=edit
    res_404 = client.get("/NewUncreatedPage")
    assert res_404.status_code == 200
    assert b"does not exist" in res_404.data

    # Non-existing page with action=edit
    res_edit = client.get("/NewUncreatedPage?action=edit")
    assert res_edit.status_code == 200
    assert b"Create" in res_edit.data or b"Edit" in res_edit.data or b"NewUncreatedPage" in res_edit.data


def test_all_pages_route(client):
    gb.write_page("AlphaPage", "Content A")
    gb.write_page("BetaPage", "Content B")
    res = client.get("/all-pages")
    assert res.status_code == 200
    assert b"AlphaPage" in res.data
    assert b"BetaPage" in res.data


def test_search_route(client):
    gb.write_page("SearchableOne", "Unique keyword Python rulez")
    gb.write_page("SearchableTwo", "Other content here")

    res = client.get("/search?q=Python")
    assert res.status_code == 200
    assert b"SearchableOne" in res.data
    assert b"SearchableTwo" not in res.data

    res_empty = client.get("/search")
    assert res_empty.status_code == 200


def test_raw_page_route(client):
    gb.write_page("RawTest", "# Heading\n\nRaw body text")
    res = client.get("/RawTest/raw")
    assert res.status_code == 200
    assert res.headers["Content-Type"].startswith("text/plain")
    assert res.data.decode("utf-8") == "# Heading\n\nRaw body text"

    res_404 = client.get("/NonExistentPage/raw")
    assert res_404.status_code == 404


def test_page_history_and_diff(client):
    gb.write_page("HistoryTest", "Version 1", author="Author1", message="v1")
    gb.write_page("HistoryTest", "Version 2", author="Author2", message="v2")

    res_hist = client.get("/HistoryTest/history")
    assert res_hist.status_code == 200
    assert b"v1" in res_hist.data
    assert b"v2" in res_hist.data

    history = gb.get_history("HistoryTest")
    latest_commit = history[0]["hash"]

    res_diff = client.get(f"/HistoryTest/diff/{latest_commit}")
    assert res_diff.status_code == 200

    # 404 for page_history on non-existent page
    res_no_page = client.get("/NoSuchPage/history")
    assert res_no_page.status_code == 404


def test_edit_and_revert_page_flow(client):
    # Enable anonymous editing
    settings = gb.load_settings()
    settings["allow_anonymous"] = True
    gb.save_settings(settings)

    # GET edit page
    res_get_edit = client.get("/FlowPage/edit")
    assert res_get_edit.status_code == 200

    # POST edit page
    res_post_edit = client.post("/FlowPage/edit", data={
        "content": "Flow v1",
        "author": "Alice",
        "message": "Initial flow"
    }, follow_redirects=True)
    assert res_post_edit.status_code == 200
    assert b"Flow v1" in res_post_edit.data

    # Edit again
    client.post("/FlowPage/edit", data={
        "content": "Flow v2",
        "author": "Bob",
        "message": "Update flow"
    }, follow_redirects=True)

    history = gb.get_history("FlowPage")
    v1_hash = history[1]["hash"]

    # Revert page
    res_revert = client.post(f"/FlowPage/revert/{v1_hash}", data={"author": "Charlie"}, follow_redirects=True)
    assert res_revert.status_code == 200
    assert gb.read_page("FlowPage") == "Flow v1"


def test_revert_page_anonymous_disabled(client):
    gb.write_page("RevPage", "V1")
    gb.write_page("RevPage", "V2")
    v1_hash = gb.get_history("RevPage")[1]["hash"]

    # Anonymous edit is disabled by default
    res = client.post(f"/RevPage/revert/{v1_hash}", data={"author": "Anon"}, follow_redirects=True)
    assert b"Admin login required to revert." in res.data
