# Contributing to GitWiki

Thank you for your interest in contributing to GitWiki! We welcome contributions, bug reports, feature requests, and documentation improvements.

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

1. Fork the repository and clone your fork locally:
   ```bash
   git clone https://github.com/freedevgraph/gitwiki.git
   cd gitwiki
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt pytest
   ```

## Development & Testing

Before submitting your changes, ensure that all tests pass:

```bash
python -m pytest
```

If you add new features or fix bugs, please add corresponding tests in `tests/`.

## Submission Process

1. Create a descriptive topic branch for your changes:
   ```bash
   git checkout -b feature/my-new-feature
   ```
2. Commit your changes with clear and concise commit messages.
3. Push your branch to GitHub and open a Pull Request.

## Security Disclosures

If you discover a security vulnerability, please refer to our [SECURITY.md](SECURITY.md) for instructions on how to submit a security report privately.
