#!/usr/bin/env python3
"""List available Tabnine skills from the remote endpoint.

Usage: python list_skills.py

Requires environment variables TABNINE_HOST and TABNINE_TOKEN.
"""

import json
import os
import sys
import urllib.request


def main():
    host = os.environ.get("TABNINE_HOST", "")
    token = os.environ.get("TABNINE_TOKEN", "")

    if not host:
        print("Error: TABNINE_HOST environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    if not token:
        print("Error: TABNINE_TOKEN environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    url = f"https://{host}/update/skills"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"Error: HTTP {e.code} from {url}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Error: Could not connect to {url}: {e.reason}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data, list):
        print(f"Error: unexpected response format from {url}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
