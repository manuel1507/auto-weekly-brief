import json
from openai import OpenAI

client = OpenAI()

SYSTEM = """You are a senior automotive industry intelligence analyst writing for a global Tier-1 supplier (Operations & Industrial Strategy).

Hard rules:
- Use ONLY the provided events. Do not invent facts, numbers, dates, or actors not present in the events.
- Output MUST be in English. Input may be in any language; translate internally without mentioning translation.
- Strongly prioritize Tier-1 relevance: plant openings/closures, capacity changes, capex, ramp-ups/downs, production disruptions, localization/footprint moves, M&A/JVs/divestments, supplier distress (bankruptcy/insolvency/restructuring), sourcing shifts, and regulation/trade actions impacting the supply base.
- Deprioritize: pure sales/registrations/market share, new model launches/reviews, infotainment/design news, and executive appointments unless directly tied to restructuring/plant decisions/sourcing shifts.
- Citations: Each item MUST cite sources using ONLY the URLs provided in that event's 'urls' list. Never cite a URL that belongs to a different event.
- Avoid filler, motivational tone, and generic consulting language. Be concrete and decision-relevant.
"""

def _compact_payload(payload: dict, max_events: int = 30) -> dict:
    events = (payload.get("events") or [])[:max_events]
    compact_events = []
    for e in events:
        members = e.get("members") or []
        urls = []
        if e.get("url"):
            urls.append(e["url"])
        for m in members[:6]:
            u = (m or {}).get("url")
            if u and u not in urls:
                urls.append(u)

        compact_events.append({
            "title": e.get("title", ""),
            "published_at": e.get("published_at", ""),
            "category": e.get("category", ""),
            "score": e.get("score", ""),
            "summary_seed": e.get("summary_seed", ""),
            "urls": urls,  # canonical first
        })

    return {
        "week_number": payload.get("week_number", ""),
        "generated_at_utc": payload.get("generated_at_utc", ""),
        "days_back": payload.get("days_back", ""),
        "events": compact_events,
    }

def write_weekly_report(model: str, payload: dict) -> str:
    data = _compact_payload(payload, max_events=30)
    events_json = json.dumps(data, ensure_ascii=False)

    user_prompt = f"""Create a Weekly Global Automotive Industry Brief for a Tier-1 supplier.

Use EXACTLY these section headers (verbatim):
TITLE
INTRO
TOP 10 NEWS
BUSINESS ANALYSIS
LINKEDIN POST

Requirements by section:

TITLE
- One single-line headline capturing the most structural signal for Europe (not the noisiest story).
- No subtitle.

INTRO
- Exactly one sentence: "Good morning. Here is your briefing for CW{data.get('week_number','')}."

TOP 10 NEWS
- Write exactly 10 bullets IF 10 or more events are provided. If fewer than 10 events exist, write as many as available.
- Each bullet must be ONE sentence.
- Each bullet must end with 1–2 source URLs taken ONLY from that event's 'urls' list.
- Prefer industrial / supply-base events. Avoid sales/registrations/model-launch unless they imply production cuts, plant actions, or sourcing shifts.

BUSINESS ANALYSIS
Write 4 short subsections (use these exact subheaders):
1) Footprint & capacity
2) Supply base risk / M&A
3) Policy & cost exposure
4) What Tier-1s should do next week

Rules:
- Each subsection: 3–5 bullets max.
- Bullets must be concrete (capacity, location, sourcing direction, margin pressure mechanisms, risk).
- Every bullet must end with at least one URL, and URLs must come ONLY from the relevant event(s).
- No "s: Source" artifacts. Do not write the word "Source:".

LINKEDIN POST
- Write a LinkedIn-ready post (professional tone, no hype), 1,200–1,800 characters roughly.
- Structure:
  * Hook (1–2 lines)
  * 5 bullets: the most relevant supply-base signals
  * 2 bullets: implications for Tier-1 suppliers
  * Closing line inviting discussion
  * 5–8 hashtags (automotive/supplychain/operations/footprint/mergers etc.)
- Include 3–5 URLs total at the end (each on its own line). Use ONLY URLs from the events.

CITATION DISCIPLINE (critical):
- When writing about an event, cite ONLY from that event's 'urls' list.
- Do not reuse the same URL for unrelated items.

Input events JSON (authoritative):
{events_json}
"""

    resp = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
    )
    return resp.output_text