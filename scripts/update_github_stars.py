"""Refresh the static star badges; run daily by GitHub Actions."""

import json
import os
from pathlib import Path
import re
from urllib.request import Request, urlopen


BADGE = re.compile(
    r'(<span class="github-stars" data-github-repo="([\w.-]+/[\w.-]+)">'
    r'<i class="fas fa-star"></i> )[^<]*(</span>)'
)


def format_stars(count):
    if count < 1000:
        return str(count)
    if count < 10000:
        return f"{count / 1000:.1f}k"
    return f"{(count + 500) // 1000}k"


def fetch_stars(repo):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "github-stars-updater"}
    if token := os.environ.get("GH_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"https://api.github.com/repos/{repo}", headers=headers)
    with urlopen(request, timeout=30) as response:
        count = json.load(response)["stargazers_count"]
    if type(count) is not int or count < 0:
        raise ValueError(f"Invalid star count for {repo}")
    return count


def update_page(path):
    original = path.read_text(encoding="utf-8")
    repos = sorted({match[2] for match in BADGE.finditer(original)})
    if not repos:
        raise ValueError("No GitHub star badges found")
    # Fetch every repository before writing, so a failed request preserves the page.
    counts = {repo: fetch_stars(repo) for repo in repos}
    updated = BADGE.sub(
        lambda match: match[1] + format_stars(counts[match[2]]) + match[3], original
    )
    if updated != original:
        path.write_text(updated, encoding="utf-8")
    for repo, count in counts.items():
        print(f"{repo}: {count}")


if __name__ == "__main__":
    update_page(Path(__file__).resolve().parents[1] / "index.html")
