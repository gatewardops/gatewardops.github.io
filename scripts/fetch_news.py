#!/usr/bin/env python3
"""Collect recent IT and security headlines from public RSS/Atom feeds.

Writes data/news.json, which the home page reads. Uses only the Python
standard library, so the GitHub Action needs no pip install.

Run locally:  python scripts/fetch_news.py
"""

from __future__ import annotations

import json
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path
import re

FEEDS = [
    ("The Hacker News", "https://feeds.feedburner.com/TheHackersNews"),
    ("BleepingComputer", "https://www.bleepingcomputer.com/feed/"),
    ("Krebs on Security", "https://krebsonsecurity.com/feed/"),
    ("CISA Advisories", "https://www.cisa.gov/cybersecurity-advisories/all.xml"),
    ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/technology-lab"),
    ("SANS ISC", "https://isc.sans.edu/rssfeed_full.xml"),
]

PER_SOURCE = 3          # newest items kept from each feed
MAX_ITEMS = 15          # total items on the page
MAX_AGE_DAYS = 4        # ignore anything older than this
TIMEOUT = 20            # seconds per feed
USER_AGENT = "GatewardOps-NewsBot/1.0 (+https://gatewardops.com)"

OUT = Path(__file__).resolve().parent.parent / "data" / "news.json"
ATOM = "{http://www.w3.org/2005/Atom}"


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/atom+xml, application/xml;q=0.9, */*;q=0.5"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read(5_000_000)  # 5 MB cap


def parse_date(text: str | None) -> datetime | None:
    if not text:
        return None
    text = text.strip()
    try:
        d = parsedate_to_datetime(text)  # RFC 822, used by RSS
    except (TypeError, ValueError):
        try:
            d = datetime.fromisoformat(text.replace("Z", "+00:00"))  # ISO 8601, used by Atom
        except ValueError:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)


def clean(text: str | None) -> str:
    text = unescape(re.sub(r"<[^>]+>", "", text or ""))
    return re.sub(r"\s+", " ", text).strip()


def parse_feed(source: str, data: bytes) -> list[dict]:
    root = ET.fromstring(data)
    items = []
    # RSS 2.0
    for it in root.iter("item"):
        items.append((it.findtext("title"), it.findtext("link"), it.findtext("pubDate") or it.findtext("{http://purl.org/dc/elements/1.1/}date")))
    # Atom
    for it in root.iter(ATOM + "entry"):
        link = None
        for l in it.findall(ATOM + "link"):
            if l.get("rel", "alternate") == "alternate":
                link = l.get("href")
                break
        items.append((it.findtext(ATOM + "title"), link, it.findtext(ATOM + "published") or it.findtext(ATOM + "updated")))

    out = []
    for title, link, date in items:
        title, link = clean(title), (link or "").strip()
        if not title or not link.startswith(("https://", "http://")):
            continue
        out.append({"title": title[:200], "link": link, "source": source, "published": parse_date(date)})
    return out


def main() -> int:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=MAX_AGE_DAYS)
    collected, failures = [], 0

    for source, url in FEEDS:
        try:
            entries = parse_feed(source, fetch(url))
        except Exception as exc:  # one broken feed must not stop the others
            failures += 1
            print(f"WARN {source}: {exc}", file=sys.stderr)
            continue
        fresh = [e for e in entries if e["published"] and e["published"] >= cutoff]
        fresh.sort(key=lambda e: e["published"], reverse=True)
        print(f"OK   {source}: {len(entries)} entries, {len(fresh)} recent")
        collected.extend(fresh[:PER_SOURCE])

    if failures == len(FEEDS):
        print("ERROR: every feed failed; keeping the previous news.json", file=sys.stderr)
        return 1

    # De-duplicate by link, newest first.
    seen, items = set(), []
    for e in sorted(collected, key=lambda e: e["published"], reverse=True):
        if e["link"] in seen:
            continue
        seen.add(e["link"])
        items.append({**e, "published": e["published"].strftime("%Y-%m-%dT%H:%M:%SZ")})
    items = items[:MAX_ITEMS]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"updated": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "items": items}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(items)} items to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
