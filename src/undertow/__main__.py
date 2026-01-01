"""
Entry point for running The Undertow as a module.

Usage:
    python -m undertow <command> [options]
"""

from undertow.cli import main

if __name__ == "__main__":
    exit(main())

