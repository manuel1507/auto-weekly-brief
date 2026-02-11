import os
from datetime import datetime, timedelta, timezone

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
                #"title": it.get("title", ""),
                "title": clean_text(it.get("title", "")),
                "url": url,
                "published_at": it.get("published_at"),
                #"text": text[:9000],  # cap cost
                "text": clean_text(text[:9000]),
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
        canonical = max(members, key=lambda m: len(m["text"]))
        event = {
            "title": canonical["title"],
            "url": canonical["url"],
            "published_at": canonical["published_at"],
            "summary_seed": canonical["text"][:800],  # seed for LLM
            "members": [{"title": m["title"], "url": m["url"]} for m in members[:6]],
        }
        event["category"] = classify_event(
            {"title": event["title"], "text": canonical["text"]},
            KEYWORDS
        )
        event["score"] = score_event(
            {"title": event["title"], "text": canonical["text"]},
            KEYWORDS
        )
        events.append(event)

    # 6) rank + select
    events.sort(key=lambda e: (e["score"], e.get("published_at") or ""), reverse=True)
    events = events[:st.max_events_in_report]

    payload = {
        "generated_at_utc": now.isoformat(),
        "days_back": st.days_back,
        "events": events,
    }

    # 7) LLM write
    report_text = write_weekly_report(st.llm_model, payload)
    report_text = clean_text(report_text)   # <<< IMPORTANT

    # 8) PDF render
    week_tag = now.strftime("%Y-%m-%d")
    out_pdf = f"weekly_auto_brief_{week_tag}.pdf"
    render_pdf(
        report_text,
        out_pdf,
        title="Weekly Global Automotive Industry Brief (Tier-1 Lens)",
        subtitle=f"Covering the last {st.days_back} days — Generated {week_tag} (UTC)"
    )

    # 9) upload to Drive
    folder_id = os.environ["GOOGLE_DRIVE_FOLDER_ID"]
    link = upload_to_drive(out_pdf, folder_id)

    print("✅ Uploaded PDF to Google Drive:")
    print(link)

if __name__ == "__main__":
    main()

