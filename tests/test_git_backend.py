import pytest
import os
import gitwiki.git_backend as gb


@pytest.fixture
def repo_env(tmp_path, monkeypatch):
    test_pages_dir = str(tmp_path / "wiki_pages")
    monkeypatch.setattr(gb, "PAGES_DIR", test_pages_dir)
    settings_path = str(tmp_path / "gitwiki_settings.json")
    monkeypatch.setattr(gb, "SETTINGS_FILE", settings_path)
    gb.init_repo()
    return tmp_path


def test_init_repo(repo_env):
    assert gb.page_exists("Main_Page")
    assert "Welcome to GitWiki" in gb.read_page("Main_Page")


def test_settings_load_and_save(repo_env):
    settings = gb.load_settings()
    assert settings["site_name"] == "GitWiki"
    assert settings["allow_anonymous"] is False

    settings["site_name"] = "CustomWiki"
    settings["allow_anonymous"] = True
    gb.save_settings(settings)

    loaded = gb.load_settings()
    assert loaded["site_name"] == "CustomWiki"
    assert loaded["allow_anonymous"] is True


def test_page_crud_operations(repo_env):
    # Page non-existence
    assert not gb.page_exists("NonExistent")
    assert gb.read_page("NonExistent") is None

    # Write page
    gb.write_page("Test_Page", "Hello World", author="Alice", message="First commit")
    assert gb.page_exists("Test_Page")
    assert gb.read_page("Test_Page") == "Hello World"
    assert "Test_Page" in gb.list_pages()

    # Delete non-existent page
    assert not gb.delete_page("DoesNotExist")

    # Delete existent page
    assert gb.delete_page("Test_Page", author="Bob")
    assert not gb.page_exists("Test_Page")
    assert "Test_Page" not in gb.list_pages()


def test_history_diff_and_revert(repo_env):
    gb.write_page("History_Page", "Version 1", author="Alice", message="v1")
    gb.write_page("History_Page", "Version 2", author="Bob", message="v2")

    history = gb.get_history("History_Page")
    assert len(history) == 2
    v2_commit = history[0]
    v1_commit = history[1]

    assert v2_commit["message"] == "v2"
    assert v1_commit["message"] == "v1"

    # Get page at commit
    assert gb.get_page_at_commit("History_Page", v1_commit["hash"]) == "Version 1"
    assert gb.get_page_at_commit("History_Page", v2_commit["hash"]) == "Version 2"
    assert gb.get_page_at_commit("History_Page", "0000000000000000000000000000000000000000") is None

    # Get diff
    diff = gb.get_diff("History_Page", v2_commit["hash"])
    assert "Version 1" in diff or "Version 2" in diff
    assert gb.get_diff("History_Page", "invalid-hash!") == ""

    # Revert page
    revert_res = gb.revert_page("History_Page", v1_commit["hash"], author="Charlie")
    assert revert_res is True
    assert gb.read_page("History_Page") == "Version 1"

    # Revert to non-existent commit
    assert not gb.revert_page("History_Page", "1111111111111111111111111111111111111111")


def test_history_for_nonexistent_page(repo_env):
    history = gb.get_history("NoSuchPage")
    assert history == []
