import os
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from src.config import Settings, RSS_FEEDS, KEYWORDS
from src.ingest.rss import fetch_rss_items
from src.ingest.extract import fetch_html, extract_text
from src.ingest.clean import clean_text
from src.enrich.embed import embed_texts
from src.enrich.dedup import cluster_by_similarity
from src.enrich.rank import score_event, classify_event
from src.enrich.select import select_events
from src.report.writer import write_weekly_report
from src.report.pdf import render_pdf
from src.report.drive_upload import upload_to_drive


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return ""


def _pick_canonical(members: list[dict]) -> dict:
    """
    Pick a canonical article for a deduplicated event cluster.

    Logic:
    - Prefer richer articles (longer extracted text)
    - But avoid always selecting the same domain if the cluster has alternatives
    """
    if not members:
        return {}

    def _pub(m: dict) -> str:
        return m.get("published_at") or ""

    candidates = sorted(
        members,
        key=lambda m: (len(m.get("text", "")), _pub(m)),
        reverse=True,
    )

    seen_domains = set()
    for candidate in candidates:
        d = _domain(candidate.get("url", ""))
        if d and d not in seen_domains:
            return candidate
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
    for item in raw:
        url = item.get("url")
        if not url:
            continue

        pub = item.get("published_at")
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
            if len(text) < 150:
                continue
            
            docs.append({
                "title": clean_text(item.get("title", "")),
                "url": url,
                "published_at": item.get("published_at"),
                "text": clean_text(text[:9000]),
            }     
            )
            print(clean_text(item.get("title", "")) + url)
            
        except Exception:
            continue

    if not docs:
        raise RuntimeError("No documents collected. Add RSS feeds in src/config.py")

    # 3) embeddings for dedup
    embed_inputs = [(d["title"] + "\n" + d["text"][:1500]) for d in docs]
    vectors = embed_texts(embed_inputs, model=st.embed_model)

    # 4) dedup clustering
    clusters_idx = cluster_by_similarity(docs, vectors, threshold=st.dedup_threshold)

    # 5) clusters -> events
    events = []
    for idxs in clusters_idx:
        members = [docs[i] for i in idxs]
        canonical = _pick_canonical(members)

        event = {
            "title": canonical.get("title", ""),
            "url": canonical.get("url", ""),
            "published_at": canonical.get("published_at"),
            "summary_seed": canonical.get("text", "")[:800],
            "members": [{"title": m.get("title", ""), "url": m.get("url", "")} for m in members[:6]],
        }

        event["category"] = classify_event(
            {"title": event["title"], "text": canonical.get("text", "")},
            KEYWORDS,
        )
        event["score"] = score_event(
            {"title": event["title"], "text": canonical.get("text", "")},
            KEYWORDS,
        )
        events.append(event)
        

    # 6) rank events globally
    events.sort(key=lambda e: (e["score"], e.get("published_at") or ""), reverse=True)
    print(events)

    # 7) select top supplier-relevant events only
    selected_events = select_events(
        events,
        max_total=10,
        max_per_domain=getattr(st, "max_per_domain", 3),
    )

    print("\n===== SELECTED EVENTS =====\n")
    for i, e in enumerate(selected_events):
        print(f"{i+1}. {e.get('title','NO TITLE')}")

    print("\n===== END SELECTED =====\n")
    

    week_number = now.isocalendar().week
    payload = {
        "generated_at_utc": now.isoformat(),
        "days_back": st.days_back,
        "week_number": week_number,
        "events": selected_events,
    }

    # 8) write LinkedIn-style brief
    report_text = write_weekly_report(st.llm_model, payload)
    report_text = clean_text(report_text)

    # 9) render PDF
    week_tag = now.strftime("%Y-%m-%d")
    out_pdf = f"weekly_auto_brief_{week_tag}.pdf"
    render_pdf(
        report_text,
        out_pdf,
        title="Automotive Supply Base Brief",
        subtitle=f"Covering the last {st.days_back} days — Generated {week_tag} (UTC)",
    )

    # 10) upload to Drive
    folder_id = os.environ["GOOGLE_DRIVE_FOLDER_ID"]
    link = upload_to_drive(out_pdf, folder_id)

    print("✅ Uploaded PDF to Google Drive:")
    print(link)


if __name__ == "__main__":
    main()