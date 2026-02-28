import os
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from src.config import Settings, RSS_FEEDS, KEYWORDS
from src.ingest.rss import fetch_rss_items
from src.ingest.extract import fetch_html, extract_text
from src.enrich.embed import embed_texts
from src.enrich.dedup import cluster_by_similarity
from src.enrich.rank import score_event, classify_event
from src.report.writer import write_weekly_report
from src.report.pdf import render_pdf
from src.report.drive_upload import upload_to_drive
from src.ingest.clean import clean_text


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return ""


def _pick_canonical(members: list[dict]) -> dict:
    """
    Pick a canonical article for an event cluster.

    Previous behavior: always pick the longest article -> tends to bias toward
    a single publisher with long-form pages (e.g., Automotive World), reducing
    perceived source diversity.

    New behavior (minimal change):
    - prefer content-rich candidates (longer text)
    - but if the cluster contains multiple domains, avoid picking the same domain repeatedly
      within that cluster (pick the first unseen domain in sorted candidates)
    """
    if not members:
        return {}

    def _pub(m: dict) -> str:
        # ISO string if present; lexicographic sort works well enough here
        return m.get("published_at") or ""

    candidates = sorted(
        members,
        key=lambda m: (len(m.get("text", "")), _pub(m)),
        reverse=True,
    )

    seen_domains = set()
    for c in candidates:
        d = _domain(c.get("url", ""))
        if d and d not in seen_domains:
            return c
        seen_domains.add(d)

    return candidates[0]


def main():
    st = Settings()
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=st.days_back)

    # 1) ingest RSS
    raw = []
    for feed in RSS_FEEDS:
        raw.extend(fetch_rss_items(feed, st.max_items_per_feed))

    # 2) fetch + extract
    docs = []
    for it in raw:
        url = it.get("url")
        if not url:
            continue

        # If published date exists, filter by days_back
        pub = it.get("published_at")
        if pub:
            try:
                pub_dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                if pub_dt < cutoff:
                    continue
            except Exception:
                pass

        try:
            html = fetch_html(url)
            text = extract_text(html)
            if len(text) < 500:
                continue

            docs.append({
                "title": clean_text(it.get("title", "")),
                "url": url,
                "published_at": it.get("published_at"),
                "text": clean_text(text[:9000]),  # cap cost
            })
        except Exception:
            continue

    if not docs:
        raise RuntimeError("No documents collected. Add RSS feeds in src/config.py")

    # 3) embed for dedup
    embed_inputs = [(d["title"] + "\n" + d["text"][:1500]) for d in docs]
    vectors = embed_texts(embed_inputs, model=st.embed_model)

    # 4) cluster
    clusters_idx = cluster_by_similarity(docs, vectors, threshold=st.dedup_threshold)

    # 5) convert clusters into events
    events = []
    for idxs in clusters_idx:
        members = [docs[i] for i in idxs]

        # NEW: canonical selection with less single-source bias
        canonical = _pick_canonical(members)

        event = {
            "title": canonical.get("title", ""),
            "url": canonical.get("url", ""),
            "published_at": canonical.get("published_at"),
            "summary_seed": (canonical.get("text", "")[:800]),
            "members": [{"title": m.get("title", ""), "url": m.get("url", "")} for m in members[:6]],
        }

        event["category"] = classify_event(
            {"title": event["title"], "text": canonical.get("text", "")},
            KEYWORDS
        )
        event["score"] = score_event(
            {"title": event["title"], "text": canonical.get("text", "")},
            KEYWORDS
        )
        events.append(event)

    # 6) rank
    events.sort(key=lambda e: (e["score"], e.get("published_at") or ""), reverse=True)

    # NEW: limit per-domain to improve source diversity in final selection
    max_per_domain = getattr(st, "max_per_domain", 3)  # add to Settings/config if you want
    selected = []
    domain_counts = {}

    for e in events:
        d = _domain(e.get("url", ""))
        if d and domain_counts.get(d, 0) >= max_per_domain:
            continue
        selected.append(e)
        if d:
            domain_counts[d] = domain_counts.get(d, 0) + 1
        if len(selected) >= st.max_events_in_report:
            break

    events = selected

    week_number = now.isocalendar().week

    payload = {
        "generated_at_utc": now.isoformat(),
        "days_back": st.days_back,
        "events": events,
        "week_number": week_number,
    }

    # 7) LLM write
    report_text = write_weekly_report(st.llm_model, payload)
    report_text = clean_text(report_text)

    # 8) PDF render
    week_tag = now.strftime("%Y-%m-%d")
    out_pdf = f"weekly_auto_brief_{week_tag}.pdf"
    render_pdf(
        report_text,
        out_pdf,
        title="Weekly Global Automotive Industry Brief",
        subtitle=f"Covering the last {st.days_back} days — Generated {week_tag} (UTC)"
    )

    # 9) upload to Drive
    folder_id = os.environ["GOOGLE_DRIVE_FOLDER_ID"]
    link = upload_to_drive(out_pdf, folder_id)

    print("✅ Uploaded PDF to Google Drive:")
    print(link)


if __name__ == "__main__":
    main()
