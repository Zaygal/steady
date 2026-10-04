#!/usr/bin/env python3
"""Push DEV-POST.md to the live dev.to article. Frontmatter becomes the API fields."""
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

raw = Path("DEV-POST.md").read_text(encoding="utf-8")
m = re.match(r"^---\n(.*?)\n---\n", raw, re.S)
front, body = (m.group(1), raw[m.end():]) if m else ("", raw)


def field(name, default=""):
    hit = re.search(rf"^{name}:\s*(.*)$", front, re.M)
    return hit.group(1).strip() if hit else default


payload = {"article": {
    "title": field("title"),
    "body_markdown": body,
    "tags": [t.strip() for t in field("tags").split(",") if t.strip()],
    "published": os.environ.get("PUBLISH", "true").lower() == "true",
}}

req = urllib.request.Request(
    "https://dev.to/api/articles/" + os.environ["ARTICLE_ID"],
    data=json.dumps(payload).encode(),
    headers={"api-key": os.environ["KEY"], "Content-Type": "application/json"},
    method="PUT")
try:
    with urllib.request.urlopen(req, timeout=90) as r:
        d = json.loads(r.read())
except urllib.error.HTTPError as exc:
    raise SystemExit(f"dev.to rejected the update: {exc.code} {exc.read()[:300]!r}")

print("url   :", d.get("url"))
print("title :", d.get("title"))
print("tags  :", d.get("tag_list"))
