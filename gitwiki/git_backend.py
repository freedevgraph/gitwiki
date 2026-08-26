"""Git-backed storage for wiki pages."""
import os
import subprocess
import json
import re
from datetime import datetime, timezone
from pathlib import Path

PAGES_DIR = "wiki_pages"
SETTINGS_FILE = "gitwiki_settings.json"

DEFAULT_SETTINGS = {
    "site_name": "GitWiki",
    "allow_anonymous": False,
    "site_footer": "Powered by GitWiki",
}


def _run_git(*args, cwd=None):
    """Run a git command and return stdout."""
    result = subprocess.run(
        ["git"] + list(args),
        capture_output=True, text=True, cwd=cwd or _repo_root()
    )
    if result.returncode != 0:
        raise RuntimeError(f"git error: {result.stderr.strip()}")
    return result.stdout.strip()


def _repo_root():
    """Return the wiki pages repo root."""
    return os.path.abspath(PAGES_DIR)


def _page_file(name):
    """Return the file path for a wiki page."""
    if ".." in name or "/" in name or "\\" in name:
        raise ValueError("Invalid page name: path traversal attempt detected.")
    safe = re.sub(r'[^\w\-]', '_', name)
    root = Path(_repo_root()).resolve()
    target_path = (root / f"{safe}.md").resolve()
    if not str(target_path).startswith(str(root)):
        raise ValueError("Invalid page name: path traversal attempt detected.")
    return str(target_path)


def _page_name_from_file(filepath):
    """Extract the page name from a file path."""
    base = os.path.basename(filepath)
    return base.rsplit(".", 1)[0]


def init_repo():
    """Initialize the git repository for wiki pages."""
    root = _repo_root()
    if not os.path.isdir(root):
        os.makedirs(root, exist_ok=True)
        _run_git("init", cwd=root)
        _run_git("config", "user.email", "gitwiki@local", cwd=root)
        _run_git("config", "user.name", "GitWiki", cwd=root)
        readme = os.path.join(root, "Main_Page.md")
        with open(readme, "w", encoding="utf-8") as f:
            f.write("# Welcome to GitWiki\n\nThis is the main page. Edit away!\n")
        _run_git("add", ".", cwd=root)
        _run_git("commit", "-m", "Initial commit", cwd=root)


def load_settings():
    """Load settings from disk."""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_SETTINGS.copy()


def save_settings(settings):
    """Persist settings to disk."""
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)


def list_pages():
    """Return a sorted list of all page names."""
    root = _repo_root()
    if not os.path.isdir(root):
        return []
    pages = []
    for fn in os.listdir(root):
        if fn.endswith(".md"):
            pages.append(fn.rsplit(".", 1)[0])
    return sorted(pages)


def page_exists(name):
    """Check if a page exists."""
    return os.path.isfile(_page_file(name))


def read_page(name):
    """Read the current content of a page."""
    path = _page_file(name)
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_page(name, content, author="Anonymous", message=None):
    """Write content to a page and commit to git."""
    path = _page_file(name)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    root = _repo_root()
    _run_git("add", ".", cwd=root)
    msg = message or f"Edit page '{name}'"
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = author
    env["GIT_AUTHOR_EMAIL"] = f"{author.lower().replace(' ', '')}@gitwiki.local"
    env["GIT_COMMITTER_NAME"] = author
    env["GIT_COMMITTER_EMAIL"] = f"{author.lower().replace(' ', '')}@gitwiki.local"
    subprocess.run(
        ["git", "commit", "-m", msg],
        capture_output=True, text=True, cwd=root, env=env
    )


def get_history(name, limit=50):
    """Return commit history for a page."""
    root = _repo_root()
    safe = re.sub(r'[^\w\-]', '_', name)
    filepath = f"{safe}.md"
    try:
        log = _run_git(
            "log", "--format=%H|%an|%ae|%ai|%s", f"-{limit}", "--", filepath,
            cwd=root
        )
    except RuntimeError:
        return []
    entries = []
    for line in log.splitlines():
        parts = line.split("|", 4)
        if len(parts) == 5:
            entries.append({
                "hash": parts[0],
                "author": parts[1],
                "email": parts[2],
                "date": parts[3],
                "message": parts[4],
            })
    return entries


def get_page_at_commit(name, commit_hash):
    """Retrieve page content at a specific commit."""
    root = _repo_root()
    safe = re.sub(r'[^\w\-]', '_', name)
    filepath = f"{safe}.md"
    try:
        content = _run_git("show", f"{commit_hash}:{filepath}", cwd=root)
        return content
    except RuntimeError:
        return None


def revert_page(name, commit_hash, author="Anonymous"):
    """Revert a page to a previous commit."""
    content = get_page_at_commit(name, commit_hash)
    if content is None:
        return False
    write_page(name, content, author=author, message=f"Revert '{name}' to {commit_hash[:8]}")
    return True


def get_diff(name, commit_hash):
    """Get diff for a specific commit."""
    if not re.match(r'^[a-fA-F0-9]+$', commit_hash):
        return ""
    root = _repo_root()
    safe = re.sub(r'[^\w\-]', '_', name)
    filepath = f"{safe}.md"
    try:
        diff = _run_git("diff", f"{commit_hash}^..{commit_hash}", "--", filepath, cwd=root)
        return diff
    except RuntimeError:
        return ""


def delete_page(name, author="Anonymous"):
    """Delete a page and commit."""
    path = _page_file(name)
    if not os.path.isfile(path):
        return False
    os.remove(path)
    root = _repo_root()
    _run_git("add", ".", cwd=root)
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = author
    env["GIT_AUTHOR_EMAIL"] = f"{author.lower().replace(' ', '')}@gitwiki.local"
    env["GIT_COMMITTER_NAME"] = author
    env["GIT_COMMITTER_EMAIL"] = f"{author.lower().replace(' ', '')}@gitwiki.local"
    subprocess.run(
        ["git", "commit", "-m", f"Delete page '{name}'"],
        capture_output=True, text=True, cwd=root, env=env
    )
    return True
