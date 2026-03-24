import json
from openai import OpenAI

client = OpenAI()

SYSTEM = """
You are a senior automotive supply-base analyst writing a short LinkedIn-ready post for professionals in the automotive industry.

Audience:
- Tier-1 and Tier-2 managers
- operations leaders
- purchasing leaders
- strategy / industrial footprint professionals

Hard rules:
- Use ONLY the provided events JSON.
- Do not invent facts, numbers, dates, quotes, actors, or implications not grounded in the input.
- Output MUST be in English.
- Input may be in any language; translate internally without mentioning translation.
- Keep the tone professional, sharp, executive, and natural for LinkedIn.
- This is not a newspaper article and not a generic newsletter.
- Write plain text only.
- Do not use hashtags.
- Do not use emojis.
- Do not mention images, charts, attachments, or PDFs.
- The entire output must stay under 2750 characters.

Writer role:
- Selection has already been completed upstream.
- Do NOT discard, merge, filter, or re-rank events.
- Use all selected events provided in the input.
- Write one bullet per selected event.
- Your job is to publish the selected events clearly and professionally.

Style rules:
- Keep bullets concise and readable.
- Avoid repetitive wording across bullets.
- Avoid repeating the exact same implication formula in every bullet.
- The closing paragraph must synthesize the overall message without restating the bullets one by one.

Citation discipline:
- Every bullet that contains a factual statement MUST end with 1 URL.
- Use ONLY URLs from the event being referenced.
- Never introduce new URLs.
- Never cite a URL from a different event.
- Do not add URLs in the final synthesis paragraph.
"""


def _compact_payload(payload: dict, max_events: int = 12) -> dict:
    events = (payload.get("events") or [])[:max_events]
    compact = []

    for idx, event in enumerate(events, start=1):
        urls = []
        if event.get("url"):
            urls.append(event["url"])

        for member in (event.get("members") or [])[:4]:
            u = (member or {}).get("url")
            if u and u not in urls:
                urls.append(u)

        compact.append({
            "event_id": idx,
            "title": event.get("title", ""),
            "category": event.get("category", ""),
            "score": event.get("score", ""),
            "summary_seed": event.get("summary_seed", ""),
            "urls": urls,
        })

    return {
        "week_number": payload.get("week_number", ""),
        "days_back": payload.get("days_back", ""),
        "events": compact,
    }


def write_weekly_report(model: str, payload: dict) -> str:
    data = _compact_payload(payload, max_events=12)
    week = data.get("week_number", "")
    events_json = json.dumps(data, ensure_ascii=False)

    prompt = f"""
Write the output in EXACTLY this structure (plain text, no markdown tables) and LIMIT to 2950 characters!:

<short, bold, attention-grabbing hook>

Good morning and welcome to this week's update.

<One short paragraph saying this is a small AI-based experiment built to summarize the week's most relevant automotive supply-base signals, and that all sources, articles, and editorial rights remain the property of their respective publishers. Keep this note concise, professional, and neutral.>

Key signals (this line font bold)

- Write exactly one bullet for each selected event in the input JSON.
- Preserve the full set of selected events.
- Do not discard, merge, filter, or re-rank events.
- Each bullet must:
  1. state the fact,
  2. explain briefly why it matters for Tier-1 / Tier-2 suppliers,
  3. end with 1 URL from that event.urls.
- Keep each bullet concise, readable, and copy-paste ready for LinkedIn.
- Do not create sub-sections.

Why it matters (this line font bold)

- Write one short paragraph of 1 to 2 lines.
- No bullets in this section.
- Synthesize the overall meaning of the selected events.
- Do NOT restate the bullets one by one.
- Focus on the broader supplier implications.
- Do not add URLs in this section.

Additional rules:
- Do not add any title above the hook.
- Do not write "Automotive Supply Base Brief".
- Use all selected events from the input JSON.
- Keep the tone executive and practical.
- Avoid filler words and generic abstractions.
- Avoid repetitive wording across bullets.
- The final output must read like a polished LinkedIn post that can be copied and pasted as-is.
- If too long → shorten bullets, not content.

Input events JSON (authoritative):
{events_json}
"""

    resp = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
    )

    return resp.output_text