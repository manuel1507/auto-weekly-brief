import json
from openai import OpenAI

client = OpenAI()

SYSTEM = """
You are a senior automotive supply-base analyst writing a weekly industrial scan for Tier-1/Tier-2 professionals.

Hard constraints:
- Use ONLY the provided events JSON. Do not invent facts, numbers, dates, quotes, or actors not present in the events.
- Output MUST be in English. Input may be in any language; translate internally without mentioning translation.
- Style: crisp, analytical, supply-base oriented. Not journalism. Not motivational.

Priority focus (supplier relevance):
- footprint/capacity (openings/closures, ramp up/down, utilisation)
- capex and industrialisation timing (validation/tooling)
- disruptions (strikes, shortages, stoppages)
- M&A/JVs/divestments, distress/insolvency
- trade/regulation impacting sourcing, duties, compliance economics
- manufacturing/automation shifts

Deprioritize / exclude unless directly tied to production/capex/sourcing:
- pure sales/registrations/market share
- model launches/reviews, infotainment/design
- consumer insurance topics
- executive appointments

Citation discipline (strict):
- EVERY bullet that makes a factual claim MUST end with 1-2 URLs.
- Use ONLY URLs provided inside the referenced event (event.urls).
- Never introduce new URLs.
- Never cite a URL that belongs to a different event than the bullet content.

Anti-repetition (very important):
- In the entire "Industrial Developments" section, each event may be used AT MOST ONCE.
- Prefer diversity: cover more distinct events rather than rephrasing the same one.
- Do not reuse the same company/event across multiple subsections if alternatives exist.

Length:
- Target ~2-3 PDF pages.
"""

def _compact_payload(payload: dict, max_events: int = 40) -> dict:
    """
    Compact events into a citation-safe format:
    each event provides a canonical URL + alternates from cluster members.
    """
    events = (payload.get("events") or [])[:max_events]
    compact = []

    for idx, e in enumerate(events, start=1):
        urls = []
        if e.get("url"):
            urls.append(e["url"])
        for m in (e.get("members") or [])[:6]:
            u = (m or {}).get("url")
            if u and u not in urls:
                urls.append(u)

        compact.append({
            "event_id": idx,
            "title": e.get("title", ""),
            "category": e.get("category", ""),
            "score": e.get("score", ""),
            "summary_seed": e.get("summary_seed", ""),
            "urls": urls,
        })

    return {
        "week_number": payload.get("week_number", ""),
        "days_back": payload.get("days_back", ""),
        "events": compact,
    }


def write_weekly_report(model: str, payload: dict) -> str:
    data = _compact_payload(payload, max_events=40)
    events_json = json.dumps(data, ensure_ascii=False)

    user_prompt = f"""
Write the brief in EXACTLY this structure (plain text):

Automotive Supply Base Brief - CW{data.get('week_number','')}
<One-line structural headline>

Good morning. Here is your supply base briefing for CW{data.get('week_number','')}.

Industrial Developments

Footprint & Capacity
- Exactly 5 bullets
- Each bullet must use a DIFFERENT event_id (no repeats anywhere else in Industrial Developments)
- ONE sentence per bullet
- End with 1-2 URLs from that event.urls

Ownership, Financial Stress & Compliance
- Exactly 4 bullets
- Use 4 DIFFERENT event_ids not used above
- ONE sentence per bullet
- End with 1-2 URLs from that event.urls

Trade, Energy & Cost Base
- Exactly 4 bullets
- Use 4 DIFFERENT event_ids not used above
- ONE sentence per bullet
- End with 1-2 URLs from that event.urls

Technology & Manufacturing
- Exactly 4 bullets
- Use 4 DIFFERENT event_ids not used above
- ONE sentence per bullet
- End with 1-2 URLs from that event.urls

Industrial Impact
- Write ONE compact prose block (6-8 lines).
- No subheaders, no bullet points.
- Do NOT restate any bullet facts above.
- Synthesize supplier mechanisms: volume variability & call-offs, fixed-cost absorption, energy/transport cost volatility, capex timing & validation/tooling risk, trade/compliance economics, counterparty complexity.
- Keep sentences short and concrete. Avoid vague words (signals/structural/reshape/dynamic/ecosystem).
- Optional: add 2-3 representative URLs at the end of the paragraph (each from events already used above). Do not add new URLs.

Selection rules (critical):
- Total bullets must be 17 (5+4+4+4). Aim to cover 17 distinct events.
- Prefer higher-score events and supplier-relevant categories.
- Exclude consumer-market noise (registrations/insurance/model news) unless it directly affects production, capacity, sourcing, capex, or compliance.
- Prefer Europe lens; include global only if it materially impacts the supply base.

Citation discipline (critical):
- For each bullet, cite ONLY from that event.urls.
- Never reuse URLs for unrelated bullets.
- Never invent URLs.

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