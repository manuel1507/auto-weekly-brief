import json
from openai import OpenAI

client = OpenAI()

SYSTEM = """You are a senior automotive industry intelligence analyst writing for a global Tier-1 supplier (Operations & Industrial Strategy).

Non-negotiable rules:
- Use ONLY the provided events. Do not invent facts, numbers, dates, quotes, or actors not present in the events.
- Output MUST be in English. Input events may be in any language; translate internally without mentioning translation.
- Prioritize Tier-1 relevance: plant openings/closures, capacity changes, ramp-ups/downs, capex, production disruptions, localization/footprint moves, M&A/JVs/divestments, supplier distress (bankruptcy/insolvency/restructuring), sourcing shifts, and regulation/trade actions impacting the supply base.
- Deprioritize or exclude: pure sales/registrations/market-share stories, new model launches/reviews, infotainment/design news, and executive appointments unless directly tied to restructuring, plant decisions, or sourcing/strategy shifts.
- Every bullet or story MUST contain at least one source URL. Prefer the canonical URL; add up to 2 additional URLs if available.
- Be concise, executive, and analytical. Avoid fluff, motivational tone, and generic filler.
- The title must reflect the highest structural long-term impact for Europe (not the most covered story).
- In take-aways, compare business models when relevant (software vs hardware; asset-light vs asset-heavy; platform vs manufacturer) and highlight asymmetries.
"""

def _format_events_for_prompt(payload: dict, max_events: int = 20) -> str:
    """
    Keeps the prompt compact and structured.
    We pass only fields the model needs for writing + citations.
    """
    events = (payload.get("events") or [])[:max_events]
    compact = []
    for e in events:
        members = e.get("members") or []
        urls = []
        if e.get("url"):
            urls.append(e["url"])
        for m in members[:4]:
            u = m.get("url")
            if u and u not in urls:
                urls.append(u)

        compact.append({
            "title": e.get("title", ""),
            "published_at": e.get("published_at", ""),
            "category": e.get("category", ""),
            "score": e.get("score", ""),
            "summary_seed": e.get("summary_seed", ""),
            "urls": urls,  # canonical first, then alternates
        })

    return json.dumps(
        {
            "week_number": payload.get("week_number", ""),
            "generated_at_utc": payload.get("generated_at_utc", ""),
            "days_back": payload.get("days_back", ""),
            "events": compact,
        },
        ensure_ascii=False
    )

def write_weekly_report(model: str, payload: dict) -> str:
    """
    Generates a Tier-1 oriented weekly automotive brief.
    Output: plain text in English.
    """

    events_json = _format_events_for_prompt(payload, max_events=24)

    user_prompt = f"""Write a "Weekly Global Automotive Industry Brief" for a Tier-1 supplier.

Required structure (use these section headers exactly):
TITLE
INTRO
TOP NEWS
TAKE-AWAYS

Formatting rules:
- TITLE: one single-line strategic headline (no subtitle). Must reflect the most structural long-term signal in Europe.
- INTRO: exactly one sentence: "Good morning. Here is your briefing for CW{payload.get('week_number','')}."
- TOP NEWS: 6–8 bullets maximum. If fewer than 6 events are Tier-1 relevant, write fewer bullets (do NOT fill with low-value news).
  Each bullet must be ONE sentence, and must end with at least one source URL.
- TAKE-AWAYS: pick the 2 most structurally important events.
  For each take-away, write 5–7 lines total, as short paragraphs/bullets, without labels like "Why it matters".
  Must include:
  - what happened (1 line)
  - concrete implications for Tier-1 suppliers (2–3 bullets: margin, sourcing, capacity/footprint, risk)
  - what to watch next (1 bullet: trigger/decision/next expected step)
  Include 2–3 source URLs at the end of the take-away block.

Selection rules:
- Strongly prioritize events in categories suggesting industrial relevance (e.g., footprint_ops, suppliers, policy_trade, ev_battery, electronics_sdv, restructuring/M&A if present).
- Exclude or heavily deprioritize events that are mainly: sales/registrations/market share, new model launches/reviews, infotainment/design, generic executive appointments.

Citation rules:
- Use ONLY URLs provided in each event's "urls" field. Do NOT add new URLs.
- Every TOP NEWS bullet must end with one URL (or two if needed).
- Every TAKE-AWAYS block must end with 2–3 URLs (canonical + up to 2 alternates).

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