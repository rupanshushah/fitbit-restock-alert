#!/usr/bin/env python3
"""
Google Store India restock checker -> ntfy push alert on your phone.

Reads the schema.org "availability" tag the store renders for each colour
of the product, e.g.
    <meta itemprop="description" content="Google Fitbit Air (Obsidian)">
    ... <link href="https://schema.org/OutOfStock" itemprop="availability">

Environment variables (or edit the defaults below):
    NTFY_TOPIC   required  your private ntfy topic name (make it long and random)
    COLOURS      optional  comma-separated colours to watch   (default: Obsidian)
    NTFY_SERVER  optional  default https://ntfy.sh

Usage:
    python3 check_stock.py              # check once (what GitHub Actions runs)
    python3 check_stock.py --loop 60    # keep checking every 60 s (laptop / Termux)
    python3 check_stock.py --test       # send a test alert to your phone
"""
import os
import re
import sys
import time
import urllib.request

PRODUCT_URL = "https://store.google.com/in/config/google_fitbit_air?hl=en-IN"
PRODUCT_NAME = "Google Fitbit Air"
NTFY_SERVER = os.environ.get("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "").strip()
COLOURS = [c.strip().lower() for c in os.environ.get("COLOURS", "Obsidian").split(",") if c.strip()]

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")

OFFER_RE = re.compile(
    r'content="' + re.escape(PRODUCT_NAME) + r'\s*\(([^)]+)\)"'   # colour name
    r'.{0,600}?'                                                   # price/currency metas
    r'schema\.org/(\w+)"\s+itemprop="availability"',               # InStock / OutOfStock / ...
    re.S,
)


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept-Language": "en-IN,en;q=0.9",
        "Cache-Control": "no-cache",
    })
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read().decode("utf-8", "replace")


def parse(html: str) -> dict:
    """Return {colour_lower: (DisplayName, availability)}."""
    out = {}
    for name, avail in OFFER_RE.findall(html):
        out.setdefault(name.strip().lower(), (name.strip(), avail))
    return out


def notify(title: str, message: str, priority: str = "urgent", tags: str = "rotating_light,watch") -> None:
    if not NTFY_TOPIC:
        print("!! NTFY_TOPIC not set - would have sent:", title, "|", message)
        return
    req = urllib.request.Request(
        f"{NTFY_SERVER}/{NTFY_TOPIC}",
        data=message.encode("utf-8"),
        method="POST",
        headers={
            "Title": title,
            "Priority": priority,          # urgent = 5 = max -> rings until dismissed (see README)
            "Tags": tags,
            "Click": PRODUCT_URL,          # tapping the notification opens the store page
            "Actions": f"view, Open Google Store, {PRODUCT_URL}",
        },
    )
    urllib.request.urlopen(req, timeout=30).read()
    print("-> alert sent:", title)


def check_once() -> int:
    """Returns 0 = all out of stock, 1 = in stock (alert sent), 2 = checker broken."""
    try:
        html = fetch(PRODUCT_URL)
    except Exception as e:  # network hiccup: just log, try again next run
        print("fetch failed:", e)
        return 0

    stock = parse(html)
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(stamp, {v[0]: v[1] for v in stock.values()})

    missing = [c for c in COLOURS if c not in stock]
    if not stock or missing:
        notify(
            "Fitbit restock checker needs fixing",
            f"Couldn't find availability for {', '.join(missing) or 'any colour'} on the page. "
            "Google may have changed the page layout.",
            priority="default", tags="warning",
        )
        return 2

    available = [stock[c][0] for c in COLOURS
                 if stock[c][1] in ("InStock", "LimitedAvailability", "OnlineOnly", "PreOrder")]
    if available:
        notify(
            f"{PRODUCT_NAME} {', '.join(available)} is IN STOCK",
            f"{', '.join(available)} is available on the Google Store India now. Tap to open.",
        )
        return 1
    return 0


def main() -> None:
    args = sys.argv[1:]
    if "--test" in args:
        notify("Test: restock alert works", "If this keeps ringing until you swipe it away, you're all set.")
        return
    if "--loop" in args:
        i = args.index("--loop")
        interval = int(args[i + 1]) if i + 1 < len(args) else 60
        while True:
            rc = check_once()
            # once in stock, re-alert every 5 min instead of every interval
            time.sleep(300 if rc == 1 else interval)
    else:
        rc = check_once()
        sys.exit(1 if rc == 2 else 0)


if __name__ == "__main__":
    main()
