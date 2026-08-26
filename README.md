# GitWiki

GitWiki is a lightweight, Git-backed Flask web application for managing wiki pages. All wiki page revisions are stored and version-controlled using Git, allowing for complete history tracking, diffs, and reverts.

## Features

- **Markdown Support & Wiki Links**: Render pages with Markdown syntax, including wiki-style internal links `[[PageName]]` or `[[PageName|Display Text]]`.
- **Git Revisions & History**: Page edits are saved as commits in a dedicated Git repository (`wiki_pages/`). View version history, diffs between commits, and revert pages to previous commits.
- **Search & Page Management**: Full-text search across wiki pages, view all pages list, raw page views, and page deletion.
- **Admin Panel & Settings**: Configure site name, custom footer, and toggle anonymous page editing permissions.
- **Security Features**: Input path sanitization to prevent path traversal vulnerabilities and constant-time admin password checks.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/freedevgraph/gitwiki
   cd gitwiki
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt pytest
   ```

## Running the Application

To start the Flask development server:

```bash
python run.py
```

By default, the application runs on `http://127.0.0.1:5000`.

### Admin Credentials

Default admin password can be set via environment variable:
```bash
export GITWIKI_ADMIN_PASSWORD="your_secure_password"
```
If unset, the default password is `admin`.

## Running Tests

Run the test suite using `pytest`:

```bash
python -m pytest
```

## Security & Contributing

For guidelines on security practices, reporting vulnerabilities, contributing, and our community standards, please refer to:
- [SECURITY.md](SECURITY.md) - Security Policy & Reporting Vulnerabilities
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution Guidelines
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) - Contributor Covenant Code of Conduct
- [LICENSE](LICENSE) - Project License
