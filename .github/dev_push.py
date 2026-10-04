#!/usr/bin/env python3
"""Push DEV-POST.md to the live dev.to article. Frontmatter becomes the API fields."""
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

# .strip() matters: a key pasted on a phone very often carries a trailing space or newline,
# which dev.to answers with a bare 403 that tells you nothing.
KEY = os.environ["KEY"].strip()
ARTICLE_ID = os.environ["ARTICLE_ID"].strip()
HDRS = {"api-key": KEY,
        "Content-Type": "application/json",
        "Accept": "application/vnd.forem.api-v1+json",
        "User-Agent": "steady-dev-push"}


def get(url):
    req = urllib.request.Request(url, headers=HDRS)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


# 1. Prove the key works at all, before blaming the update. /articles/me only needs read.
print("key length:", len(KEY), "| leading/trailing space:", KEY != os.environ["KEY"])
try:
    me = get("https://dev.to/api/articles/me/all")
    print("key is VALID - it can read", len(me), "of your articles")
except urllib.error.HTTPError as exc:
    raise SystemExit(f"key REJECTED on a read call: {exc.code} {exc.read()[:200]!r}\n"
                     "That is the key itself, not this script. Regenerate it and re-paste it "
                     "with no leading or trailing space.")

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
    "https://dev.to/api/articles/" + ARTICLE_ID,
    data=json.dumps(payload).encode(), headers=HDRS, method="PUT")
try:
    with urllib.request.urlopen(req, timeout=90) as r:
        d = json.loads(r.read())
except urllib.error.HTTPError as exc:
    raise SystemExit(f"dev.to rejected the update: {exc.code} {exc.read()[:300]!r}")

print("url   :", d.get("url"))
print("title :", d.get("title"))
print("tags  :", d.get("tag_list"))
