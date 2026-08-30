#!/usr/bin/env python3
"""GitWiki development entry point."""
from gitwiki.app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
