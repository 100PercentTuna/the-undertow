#!/usr/bin/env python3
"""
Export OpenAPI schema from the FastAPI application.

Usage:
    python scripts/export_openapi.py > openapi.json
    python scripts/export_openapi.py --yaml > openapi.yaml
"""

import argparse
import json
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Export OpenAPI schema")
    parser.add_argument(
        "--yaml",
        action="store_true",
        help="Output in YAML format instead of JSON",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output file (default: stdout)",
    )
    args = parser.parse_args()

    # Import app to get schema
    from undertow.api.main import app

    schema = app.openapi()

    if args.yaml:
        try:
            import yaml

            output = yaml.dump(schema, default_flow_style=False, allow_unicode=True)
        except ImportError:
            print("PyYAML not installed. Install with: pip install pyyaml", file=sys.stderr)
            return 1
    else:
        output = json.dumps(schema, indent=2)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Schema written to {args.output}", file=sys.stderr)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())

