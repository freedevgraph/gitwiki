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
python run_development.py
```

To start the server in production mode:

```bash
python run_production.py
```

By default, the application runs on `http://127.0.0.1:5000` in development mode.

### Admin Credentials

Default admin password can be set via environment variable:
```bash
export GITWIKI_ADMIN_PASSWORD="your_secure_password"
```
If unset, the default password is `admin`.

## Production Deployment

For production environments, running the built-in Flask development server directly is not recommended. Instead, use a production-grade WSGI HTTP server (such as Gunicorn, uWSGI, or Waitress) sitting behind a reverse proxy (such as Nginx or Caddy).

### WSGI Server Configuration

GitWiki exposes WSGI application entry points via `run_production:app` or factory `gitwiki.app:create_app()`.

#### 1. Gunicorn (Linux/macOS)

Install Gunicorn (`pip install gunicorn`) and run:

```bash
gunicorn --workers 4 --bind 127.0.0.1:8000 "gitwiki.app:create_app()"
# or using the production script entry point:
gunicorn --workers 4 --bind 127.0.0.1:8000 run_production:app
```

#### 2. uWSGI (Linux/macOS)

Install uWSGI (`pip install uwsgi`) and run:

```bash
uwsgi --http 127.0.0.1:8000 --wsgi-file run_production.py --callable app --processes 4 --threads 2
```

#### 3. Waitress (Windows/Cross-platform)

Install Waitress (`pip install waitress`) and run:

```bash
waitress-serve --listen=127.0.0.1:8000 run_production:app
```

### Security & Production Best Practices

1. **Reverse Proxy & TLS/SSL Termination**
   - Always run WSGI servers bound to localhost (`127.0.0.1`) or a UNIX socket, and proxy requests through Nginx or Caddy.
   - Configure HTTPS/TLS on the reverse proxy to encrypt traffic in transit.

2. **Handling Reverse Proxy Headers (`ProxyFix`)**
   - When running behind a reverse proxy, configure Flask to respect proxy headers (`X-Forwarded-For`, `X-Forwarded-Proto`) using Werkzeug's `ProxyFix` middleware if needed:
     ```python
     from werkzeug.middleware.proxy_fix import ProxyFix
     app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
     ```

3. **Environment Security**
   - **Admin Password**: Always set a strong, secret value for `GITWIKI_ADMIN_PASSWORD` in your production environment.
   - **Process Isolation**: Run the WSGI server process under an unprivileged, non-root user account (e.g., `gitwiki` service user).

4. **Process Management (systemd example)**
   Create a systemd unit file (e.g., `/etc/systemd/system/gitwiki.service`):
   ```ini
   [Unit]
   Description=GitWiki WSGI Application
   After=network.target

   [Service]
   User=gitwiki
   Group=gitwiki
   WorkingDirectory=/var/www/gitwiki
   Environment="GITWIKI_ADMIN_PASSWORD=change_this_to_a_strong_password"
   ExecStart=/var/www/gitwiki/venv/bin/gunicorn --workers 4 --bind 127.0.0.1:8000 "gitwiki.app:create_app()"
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

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
