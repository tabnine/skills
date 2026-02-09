#!/usr/bin/env python3
"""List available Tabnine skills from the remote endpoint.

Usage: python list_skills.py [--creds-file <path>]

Credentials are resolved in order:
  1. --creds-file flag (key=value file with TABNINE_HOST and TABNINE_TOKEN)
  2. Environment variables TABNINE_HOST and TABNINE_TOKEN
"""

import argparse
import os
import sys
import urllib.request


def load_creds_file(path):
    creds = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                creds[key.strip()] = value.strip()
    return creds


def main():
    parser = argparse.ArgumentParser(description="List available Tabnine skills")
    parser.add_argument("--creds-file", help="Path to credentials file")
    args = parser.parse_args()

    host = os.environ.get("TABNINE_HOST", "")
    token = os.environ.get("TABNINE_TOKEN", "")

    if args.creds_file:
        if not os.path.isfile(args.creds_file):
            print(f"Error: credentials file not found: {args.creds_file}", file=sys.stderr)
            sys.exit(1)
        creds = load_creds_file(args.creds_file)
        host = creds.get("TABNINE_HOST", host)
        token = creds.get("TABNINE_TOKEN", token)

    if not host:
        print("Error: TABNINE_HOST is not set.", file=sys.stderr)
        print("Set it as an environment variable or provide a credentials file with --creds-file.", file=sys.stderr)
        sys.exit(1)

    if not token:
        print("Error: TABNINE_TOKEN is not set.", file=sys.stderr)
        print("Set it as an environment variable or provide a credentials file with --creds-file.", file=sys.stderr)
        sys.exit(1)

    url = f"https://{host}/indexer/skills"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})

    try:
        with urllib.request.urlopen(req) as resp:
            print(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"Error: HTTP {e.code} from {url}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Error: Could not connect to {url}: {e.reason}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
