#!/usr/bin/env python3
"""Download a Tabnine skill by URL and save it to disk.

Usage: python get_skill.py <url> <skill-name> [--creds-file <path>] [--output-dir <dir>]

The URL is obtained from the list_skills.py output.

Credentials are resolved in order:
  1. --creds-file flag (key=value file with TABNINE_TOKEN)
  2. Environment variable TABNINE_TOKEN

Output defaults to .yuvalili/skills/<skill-name> in the current directory.
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
    parser = argparse.ArgumentParser(description="Download a Tabnine skill")
    parser.add_argument("url", help="URL to download the skill from (from list_skills.py output)")
    parser.add_argument("skill_name", help="Name of the skill (used for output file naming)")
    parser.add_argument("--creds-file", help="Path to credentials file")
    parser.add_argument("--output-dir", help="Output directory (default: .yuvalili/skills/<skill-name>)")
    args = parser.parse_args()

    token = os.environ.get("TABNINE_TOKEN", "")

    if args.creds_file:
        if not os.path.isfile(args.creds_file):
            print(f"Error: credentials file not found: {args.creds_file}", file=sys.stderr)
            sys.exit(1)
        creds = load_creds_file(args.creds_file)
        token = creds.get("TABNINE_TOKEN", token)

    if not token:
        print("Error: TABNINE_TOKEN is not set.", file=sys.stderr)
        print("Set it as an environment variable or provide a credentials file with --creds-file.", file=sys.stderr)
        sys.exit(1)

    output_dir = args.output_dir or os.path.join(".yuvalili", "skills", args.skill_name)
    os.makedirs(output_dir, exist_ok=True)

    req = urllib.request.Request(args.url, headers={"Authorization": f"Bearer {token}"})
    output_path = os.path.join(output_dir, f"{args.skill_name}.json")

    try:
        with urllib.request.urlopen(req) as resp:
            data = resp.read()
        with open(output_path, "wb") as f:
            f.write(data)
        print(f"Skill '{args.skill_name}' saved to {output_path}")
    except urllib.error.HTTPError as e:
        print(f"Error: HTTP {e.code} from {args.url}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Error: Could not connect to {args.url}: {e.reason}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
