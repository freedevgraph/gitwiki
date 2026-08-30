import run_development
import run_production


def test_run_development_app():
    assert run_development.app is not None
    assert run_development.app.name == "gitwiki.app"


def test_run_production_app():
    assert run_production.app is not None
    assert run_production.app.name == "gitwiki.app"
