#!/usr/bin/env python3
"""Regenerate the open source contributions section of README.md."""

import json
import os
import re
import sys
import urllib.request

USER = "aakashsbhatia2"
MAX_ITEMS = 5
README = os.path.join(os.path.dirname(__file__), "..", "README.md")
START = "<!-- OSS:START -->"
END = "<!-- OSS:END -->"


def api(url):
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": USER,
    })
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def main():
    query = f"author:{USER}+type:pr+-user:{USER}"
    data = api(f"https://api.github.com/search/issues?q={query}"
               "&sort=updated&order=desc&per_page=30")

    rows = []
    for item in data["items"]:
        merged = bool(item.get("pull_request", {}).get("merged_at"))
        if not merged and item["state"] != "open":
            continue  # closed without merging
        owner, name = item["repository_url"].split("/")[-2:]
        title = item["title"].split(":", 1)[-1].strip()
        title = title[0].upper() + title[1:] if title else item["title"]
        repo_link = f"[{owner}/{name}](https://github.com/{owner}/{name})"
        pr_link = f"[#{item['number']}]({item['html_url']})"
        status = "✅ Merged" if merged else "🚧 Open"
        rows.append(f"| {repo_link} | {pr_link} | {title} | {status} |")
        if len(rows) == MAX_ITEMS:
            break

    if rows:
        lines = [
            "| Project | PR | What it does | Status |",
            "| --- | --- | --- | --- |",
        ] + rows
    else:
        lines = ["_No contributions to show yet._"]

    with open(README, encoding="utf-8") as f:
        content = f.read()

    block = f"{START}\n" + "\n".join(lines) + f"\n{END}"
    updated, count = re.subn(
        re.escape(START) + r".*?" + re.escape(END), lambda _: block, content,
        flags=re.DOTALL,
    )
    if count == 0:
        sys.exit(f"markers {START} / {END} not found in README.md")

    if updated != content:
        with open(README, "w", encoding="utf-8") as f:
            f.write(updated)
        print("README.md updated")
    else:
        print("no change")


if __name__ == "__main__":
    main()
