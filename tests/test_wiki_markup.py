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


def test_wiki_markup_internal_links(client):
    gb.write_page("LinkPage", "See [[OtherPage]] and [[TargetPage|Custom Label]].")
    res = client.get("/LinkPage")
    assert res.status_code == 200
    assert b'<a href="/OtherPage">OtherPage</a>' in res.data
    assert b'<a href="/TargetPage">Custom Label</a>' in res.data


def test_wiki_markup_extensions(client):
    content = """[TOC]

# Heading 1

| Col 1 | Col 2 |
| --- | --- |
| Val 1 | Val 2 |

```python
def hello():
    return "world"
```
Line 1
Line 2
"""
    gb.write_page("MarkupTest", content)
    res = client.get("/MarkupTest")
    assert res.status_code == 200
    # Tables
    assert b'<table>' in res.data or b'<th>' in res.data or b'<td>Val 1</td>' in res.data
    # Fenced code / codehilite
    assert b'<code' in res.data or b'class="codehilite"' in res.data or b'hello()' in res.data
    # TOC
    assert b'class="toc"' in res.data or b'Heading 1' in res.data
    # nl2br
    assert b'<br' in res.data
