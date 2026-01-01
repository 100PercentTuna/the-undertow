#!/usr/bin/env python
"""
Local development runner script.

Starts the API server with hot reload.
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "undertow.api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=["src"],
        log_level="info",
    )

