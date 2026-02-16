#!/usr/bin/env python3
"""Download a Tabnine skill by URL and save it to disk.

Usage: python get_skill.py <url> --scope <project|user> [--output-dir <dir>]

The URL is obtained from the list_skills.py output. The skill name is derived
from the last path segment of the URL.

The downloaded zip is extracted into the output directory and the archive is
deleted. Symlinks are created pointing to the extracted directory.

Scope determines where skills are stored:
  project — ./.agents/skills/<name>, symlinked from ./.claude/skills/<name>
  user    — ~/.agents/skills/<name>, symlinked from ~/.claude/skills/<name>

Requires environment variable TABNINE_TOKEN.
"""

import argparse
import os
import sys
import urllib.request
import zipfile
import tempfile


def resolve_paths(scope, output_dir_override=None):
    """Return (base_dir, symlink_parents) based on scope."""
    if scope == "user":
        home = os.path.expanduser("~")
        base_dir = output_dir_override or os.path.join(home, ".agents", "skills")
        symlink_parents = [
            os.path.join(home, ".claude", "skills"),
            os.path.join(home, ".cursor", "skills"),
        ]
    else:
        base_dir = output_dir_override or os.path.join(".agents", "skills")
        symlink_parents = [
            os.path.join(".claude", "skills"),
            os.path.join(".cursor", "skills"),
        ]
    return base_dir, symlink_parents


def main():
    parser = argparse.ArgumentParser(description="Download a Tabnine skill")
    parser.add_argument("url", help="URL to download the skill from (from list_skills.py output)")
    parser.add_argument(
        "--scope",
        choices=["project", "user"],
        required=True,
        help="Install scope: 'project' (current project) or 'user' (home directory)",
    )
    parser.add_argument("--output-dir", help="Override base directory for extracted skills")
    args = parser.parse_args()

    token = os.environ.get("TABNINE_TOKEN", "")

    if not token:
        print("Error: TABNINE_TOKEN environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    skill_name = args.url.rstrip("/").rsplit("/", 1)[-1]
    base_dir, symlink_parents = resolve_paths(args.scope, args.output_dir)
    os.makedirs(base_dir, exist_ok=True)

    req = urllib.request.Request(args.url, headers={"Authorization": f"Bearer {token}"})

    try:
        with urllib.request.urlopen(req) as resp:
            data = resp.read()
    except urllib.error.HTTPError as e:
        print(f"Error: HTTP {e.code} from {args.url}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Error: Could not connect to {args.url}: {e.reason}", file=sys.stderr)
        sys.exit(1)

    # Write to a temp file, extract, then clean up the zip
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        tmp.write(data)
        zip_path = tmp.name

    output_dir = os.path.join(base_dir, skill_name)

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(base_dir)
        print(f"Skill '{skill_name}' extracted to {output_dir} (scope: {args.scope})")
    except zipfile.BadZipFile:
        print(f"Error: downloaded file from {args.url} is not a valid zip archive", file=sys.stderr)
        os.unlink(zip_path)
        sys.exit(1)

    os.unlink(zip_path)

    # Create symlinks for agent integrations
    abs_output = os.path.abspath(output_dir)
    for link_parent in symlink_parents:
        os.makedirs(link_parent, exist_ok=True)
        link_path = os.path.join(link_parent, skill_name)
        if os.path.islink(link_path):
            os.unlink(link_path)
        elif os.path.exists(link_path):
            print(f"Warning: {link_path} already exists and is not a symlink, skipping", file=sys.stderr)
            continue
        os.symlink(abs_output, link_path)
        print(f"Symlinked {link_path} -> {abs_output}")


if __name__ == "__main__":
    main()
