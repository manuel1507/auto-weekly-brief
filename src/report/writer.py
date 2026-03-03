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
- capex & industrialisation timing (validation/tooling)
- disruptions (strikes, shortages, stoppages)
- M&A/JVs/divestments, distress/insolvency
- trade/regulation impacting sourcing, duties, compliance economics
- manufacturing/automation shifts

Hard exclude unless DIRECT production/capex/sourcing impact is explicitly stated in the event:
- registrations/market-share stories
- consumer insurance topics
- model launches/reviews, infotainment/design
- generic fleet “PR” deliveries without operational impact

Citation discipline (strict):
- EVERY bullet must end with 1-2 URLs, and URLs must be taken ONLY from that event.urls.
- Never introduce new URLs.
- Never cite a URL that belongs to a different event than the bullet content.

Anti-repetition (enforced via Event IDs):
- Each event_id may be used AT MOST ONCE across ALL factual bullets in Industrial Developments.
- Every factual bullet MUST start with its event tag like [E7]. Never reuse an event_id tag.
"""

def _compact_payload(payload: dict, max_events: int = 60) -> dict:
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
    data = _compact_payload(payload, max_events=60)
    events_json = json.dumps(data, ensure_ascii=False)

    user_prompt = f"""
Write the brief in EXACTLY this structure (plain text). Enforce event uniqueness using event_id tags.

Automotive Supply Base Brief - CW{data.get('week_number','')}
<One-line structural headline>

Good morning. Here is your supply base briefing for CW{data.get('week_number','')}.

Industrial Developments

Footprint & Capacity
- Exactly 5 bullets
- Each bullet MUST start with [E#] where # is the event_id
- Use 5 DIFFERENT event_ids
- ONE sentence per bullet
- End with 1-2 URLs from that SAME event.urls

Ownership, Financial Stress & Compliance
- Exactly 4 bullets
- Use 4 DIFFERENT event_ids NOT used above
- Each bullet starts with [E#]
- ONE sentence per bullet
- End with 1-2 URLs from that SAME event.urls

Trade, Energy & Cost Base
- Exactly 4 bullets
- Use 4 DIFFERENT event_ids NOT used above
- Each bullet starts with [E#]
- ONE sentence per bullet
- End with 1-2 URLs from that SAME event.urls

Technology & Manufacturing
- Exactly 4 bullets
- Use 4 DIFFERENT event_ids NOT used above
- Each bullet starts with [E#]
- ONE sentence per bullet
- End with 1-2 URLs from that SAME event.urls

Industrial Impact
- ONE compact prose block (6-8 lines).
- No bullets, no subheaders.
- Do NOT restate any bullet facts above.
- Concrete mechanisms only: call-offs, fixed-cost absorption, freight/energy cost volatility, validation/tooling capacity, compliance cost allocation, counterparty risk.
- OPTIONAL: append 2-3 representative URLs at the end (each must come from events already used above).

Hard selection rules:
- Do NOT select registrations/market-share events.
- Do NOT select consumer insurance events.
- Do NOT select “model news”.
- Only include fleet stories if they explicitly change capacity planning, sourcing, or maintenance/call-off schedules.

Citation discipline:
- For each bullet, cite ONLY from that event.urls.
- Never reuse an event_id across bullets.
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