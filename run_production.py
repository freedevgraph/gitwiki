#!/usr/bin/env python3
"""GitWiki production entry point."""
from gitwiki.app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
