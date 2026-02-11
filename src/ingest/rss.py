import feedparser
from dateutil import parser as dtparser
from src.ingest.clean import clean_text

def fetch_rss_items(feed_url: str, max_items: int):
    d = feedparser.parse(feed_url)
    items = []
    for e in d.entries[:max_items]:
        published = None
        if getattr(e, "published", None):
            try:
                published = dtparser.parse(e.published)
            except Exception:
                published = None

        items.append({
            "source": feed_url,
            #"title": getattr(e, "title", "").strip(),
            "title": clean_text(getattr(e, "title", "").strip()),
            "url": getattr(e, "link", "").strip(),
            "published_at": published.isoformat() if published else None,
        })
    return items