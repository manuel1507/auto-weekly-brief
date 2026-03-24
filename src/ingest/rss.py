import socket
import urllib.error

import feedparser
from dateutil import parser as dtparser
from src.ingest.clean import clean_text


def fetch_rss_items(feed_url: str, max_items: int):
    try:
        d = feedparser.parse(feed_url)
    except (urllib.error.URLError, urllib.error.HTTPError, socket.timeout, TimeoutError, OSError) as e:
        print(f"[RSS ERROR] Failed to fetch feed {feed_url}: {e}")
        return []
    except Exception as e:
        print(f"[RSS ERROR] Unexpected error on feed {feed_url}: {e}")
        return []

    items = []

    if getattr(d, "bozo", False):
        bozo_exc = getattr(d, "bozo_exception", None)
        entries = getattr(d, "entries", []) or []

    # warning solo se il feed è malformato E non ha entry
    if not entries:
        print(f"[RSS WARNING] Malformed feed {feed_url}: {bozo_exc}")

    entries = getattr(d, "entries", [])
    if not entries:
        print(f"[RSS WARNING] No entries found in feed {feed_url}")
        return []

    for e in entries[:max_items]:
        try:
            published = None
            if getattr(e, "published", None):
                try:
                    published = dtparser.parse(e.published)
                except Exception:
                    published = None
            elif getattr(e, "updated", None):
                try:
                    published = dtparser.parse(e.updated)
                except Exception:
                    published = None

            items.append({
                "source": feed_url,
                #"title": getattr(e, "title", "").strip(),
                "title": clean_text(getattr(e, "title", "").strip()),
                "url": getattr(e, "link", "").strip(),
                "published_at": published.isoformat() if published else None,
            })
        except Exception as e_entry:
            print(f"[RSS WARNING] Skipping broken entry in {feed_url}: {e_entry}")
            continue

    return items