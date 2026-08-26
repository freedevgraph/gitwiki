# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| Main    | :white_check_mark: |

## Reporting a Vulnerability

We take the security of GitWiki seriously. If you discover a security vulnerability, please do not disclose it publicly in an issue or PR.

Instead, please report vulnerabilities by contacting the maintainers directly or emailing security reports to `security@example.com` (or creating a confidential security advisory on GitHub if applicable).

Please include:
- A description of the vulnerability and its potential impact.
- Detailed steps to reproduce the issue (including proof-of-concept code or HTTP requests where appropriate).
- Any proposed mitigation or fix if available.

We will acknowledge receipt of your report within 48 hours and provide status updates as we work to resolve the issue.

## Security Controls & Best Practices

GitWiki implements several core security measures:
- **Path Traversal Prevention**: Input page names are sanitized and verified against the root storage directory using resolve checks to prevent directory traversal attacks.
- **Timing-Attack Resistance**: Administrative authentication checks use constant-time comparison algorithms (`hmac.compare_digest`).
- **Secret Management**: Session keys are generated securely on application startup. Admin passwords should be overridden via the `GITWIKI_ADMIN_PASSWORD` environment variable in production environments.
