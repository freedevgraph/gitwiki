"""Flask application for GitWiki."""
import hmac
import os
import secrets
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, abort, session, g
)
import markdown

from . import git_backend as gb


def create_app():
    app = Flask(__name__)
    app.secret_key = secrets.token_hex(32)

    gb.init_repo()

    # --- Admin auth ---
    ADMIN_PASSWORD = os.environ.get("GITWIKI_ADMIN_PASSWORD", "admin")

    def login_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not session.get("is_admin"):
                flash("Admin login required.", "error")
                return redirect(url_for("admin_login"))
            return f(*args, **kwargs)
        return decorated

    def get_settings():
        return gb.load_settings()

    @app.context_processor
    def inject_settings():
        return dict(settings=get_settings())

    # --- Markdown rendering ---
    def render_wiki_markup(text):
        """Convert wiki-style markup to HTML."""
        import re
        text = re.sub(r'\[\[([^|\]]+)\|([^\]]+)\]\]', r'[\2](/\1)', text)
        text = re.sub(r'\[\[([^\]]+)\]\]', r'[\1](/\1)', text)
        extensions = ['tables', 'fenced_code', 'codehilite', 'toc', 'nl2br']
        return markdown.markdown(text, extensions=extensions)

    # ========================
    #  PUBLIC ROUTES
    # ========================

    @app.route("/")
    def index():
        settings = get_settings()
        pages = gb.list_pages()
        return render_template("index.html", pages=pages, settings=settings)

    @app.route("/<name>")
    def view_page(name):
        settings = get_settings()
        try:
            if not gb.page_exists(name):
                if request.args.get("action") == "edit":
                    return render_template("edit.html", name=name, content="",
                                           settings=settings, new_page=True)
                flash(f"Page '{name}' does not exist. Would you like to create it?", "info")
                return render_template("not_found.html", name=name, settings=settings)
            content = gb.read_page(name)
            html_content = render_wiki_markup(content)
            return render_template("page.html", name=name, content=html_content,
                                   raw=content, settings=settings)
        except ValueError:
            abort(400)

    @app.route("/<name>/edit", methods=["GET", "POST"])
    def edit_page(name):
        settings = get_settings()
        if not settings.get("allow_anonymous") and not session.get("is_admin"):
            flash("Anonymous editing is disabled. Admin login required.", "error")
            return redirect(url_for("admin_login"))
        try:
            if request.method == "POST":
                content = request.form.get("content", "")
                author = request.form.get("author", "Anonymous").strip() or "Anonymous"
                message = request.form.get("message", "").strip()
                gb.write_page(name, content, author=author, message=message)
                flash(f"Page '{name}' saved.", "success")
                return redirect(url_for("view_page", name=name))
            content = gb.read_page(name) or ""
            return render_template("edit.html", name=name, content=content,
                                   settings=settings, new_page=not gb.page_exists(name))
        except ValueError:
            abort(400)

    @app.route("/<name>/history")
    def page_history(name):
        settings = get_settings()
        try:
            if not gb.page_exists(name):
                abort(404)
            history = gb.get_history(name)
            return render_template("history.html", name=name, history=history,
                                   settings=settings)
        except ValueError:
            abort(400)

    @app.route("/<name>/diff/<commit_hash>")
    def page_diff(name, commit_hash):
        settings = get_settings()
        try:
            diff = gb.get_diff(name, commit_hash)
            return render_template("diff.html", name=name, diff=diff,
                                   commit_hash=commit_hash, settings=settings)
        except ValueError:
            abort(400)

    @app.route("/<name>/revert/<commit_hash>", methods=["POST"])
    def revert_page(name, commit_hash):
        settings = get_settings()
        if not settings.get("allow_anonymous") and not session.get("is_admin"):
            flash("Admin login required to revert.", "error")
            return redirect(url_for("admin_login"))
        try:
            author = request.form.get("author", "Anonymous").strip() or "Anonymous"
            if gb.revert_page(name, commit_hash, author=author):
                flash(f"Page '{name}' reverted to {commit_hash[:8]}.", "success")
            else:
                flash("Revert failed.", "error")
            return redirect(url_for("view_page", name=name))
        except ValueError:
            abort(400)

    @app.route("/<name>/raw")
    def raw_page(name):
        try:
            content = gb.read_page(name)
            if content is None:
                abort(404)
            return content, 200, {"Content-Type": "text/plain; charset=utf-8"}
        except ValueError:
            abort(400)

    @app.route("/<name>/delete", methods=["POST"])
    def delete_page(name):
        if not session.get("is_admin"):
            flash("Admin login required.", "error")
            return redirect(url_for("admin_login"))
        try:
            author = request.form.get("author", "Admin").strip() or "Admin"
            gb.delete_page(name, author=author)
            flash(f"Page '{name}' deleted.", "success")
            return redirect(url_for("index"))
        except ValueError:
            abort(400)

    @app.route("/all-pages")
    def all_pages():
        settings = get_settings()
        pages = gb.list_pages()
        return render_template("all_pages.html", pages=pages, settings=settings)

    @app.route("/search")
    def search():
        settings = get_settings()
        query = request.args.get("q", "").strip()
        results = []
        if query:
            for name in gb.list_pages():
                content = gb.read_page(name)
                if content and query.lower() in content.lower():
                    results.append(name)
        return render_template("search.html", query=query, results=results,
                               settings=settings)

    # ========================
    #  ADMIN ROUTES
    # ========================

    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login():
        settings = get_settings()
        if request.method == "POST":
            password = request.form.get("password", "")
            if hmac.compare_digest(password, ADMIN_PASSWORD):
                session["is_admin"] = True
                flash("Logged in as admin.", "success")
                return redirect(url_for("admin_panel"))
            flash("Invalid password.", "error")
        return render_template("admin_login.html", settings=settings)

    @app.route("/admin/logout")
    def admin_logout():
        session.pop("is_admin", None)
        flash("Logged out.", "info")
        return redirect(url_for("index"))

    @app.route("/admin")
    @login_required
    def admin_panel():
        settings = get_settings()
        pages = gb.list_pages()
        return render_template("admin.html", pages=pages, settings=settings)

    @app.route("/admin/settings", methods=["POST"])
    @login_required
    def admin_settings():
        settings = gb.load_settings()
        settings["site_name"] = request.form.get("site_name", settings["site_name"])
        settings["site_footer"] = request.form.get("site_footer", settings["site_footer"])
        settings["allow_anonymous"] = request.form.get("allow_anonymous") == "on"
        gb.save_settings(settings)
        flash("Settings updated.", "success")
        return redirect(url_for("admin_panel"))

    # --- Error handlers ---
    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html", settings=get_settings()), 404

    return app
