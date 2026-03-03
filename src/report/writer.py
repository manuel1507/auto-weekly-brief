import json
from openai import OpenAI

client = OpenAI()

SYSTEM = """You are a senior automotive supply-base analyst writing a concise weekly brief for Tier-1/Tier-2 professionals (operations, purchasing, strategy).

Hard rules:
- Use ONLY the provided events JSON. Do not invent facts, numbers, dates, quotes, or actors not present in the events.
- Output MUST be in English. Input may be in any language; translate internally without mentioning translation.
- Style: crisp, analytical, supply-base oriented. Not journalism. Not motivational.
- Prioritize supplier-relevant topics: footprint/capacity, capex, ramp-ups/downs, disruptions, M&A/JVs/divestments, distress, sourcing shifts, trade/regulation impacting supply base, automation/manufacturing shifts.
- Deprioritize: pure sales/registrations/market share, model launches/reviews, infotainment/design, exec appointments unless directly tied to restructuring, plant actions, or sourcing shifts.
- 100'%' citations: EVERY line that makes a factual claim must end with at least one source URL.
- Citation discipline: For each item, cite ONLY URLs from that event's provided 'urls'. Never cite a URL from a different event. Never introduce new URLs.
"""

def _compact_payload(payload: dict, max_events: int = 30) -> dict:
    events = (payload.get("events") or [])[:max_events]
    compact = []
    for e in events:
        urls = []
        if e.get("url"):
            urls.append(e["url"])
        for m in (e.get("members") or [])[:6]:
            u = (m or {}).get("url")
            if u and u not in urls:
                urls.append(u)

        compact.append({
            "id": len(compact) + 1,
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
        "events": compact,
    }

def write_weekly_report(model: str, payload: dict) -> str:
    data = _compact_payload(payload, max_events=30)
    events_json = json.dumps(data, ensure_ascii=False)

    user_prompt = f"""Write a weekly brief that matches THIS structure and tone:

Automotive Supply Base Brief - CW{data.get('week_number','')}
<One-line headline>

Good morning. Here is your supply base briefing for CW{data.get('week_number','')}.

This week signals a structural shift in European automotive power dynamics:
<5-7 short signal statements, each on its own line>

Strategic Take
<8-14 short lines total, analytical, no hype. Explain the unifying pattern across the most structural events. No speculation beyond events.>

Industrial Developments
Battery & Powertrain
<2-4 bullets>

Ownership & M&A
<2-4 bullets>

Trade & Policy
<2-4 bullets>

Automation & Manufacturing
<2-4 bullets>

What This Means for Tier-1 & Tier-2 Suppliers
Margin Structure
<2-4 bullets>

Footprint
<2-4 bullets>

Ownership Risk
<2-4 bullets>

Capital Allocation
<2-4 bullets>

STRICT rules:
- 100% cited: EVERY signal statement and EVERY bullet must end with 1-2 URLs.
- Use ONLY URLs from the event you are referencing (use that event’s 'urls' list).
- Do NOT write "Source:" labels. Just append the URL(s) at the end.
- Do NOT invent facts. No numbers unless present in the event seed/title.
- Keep it brief: target 2-3 pages in PDF.
- Select content that is supplier-relevant; exclude low-value items.
- Prefer Europe lens, but include global items only if they materially affect the supply base.

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