import json
from openai import OpenAI

client = OpenAI()

SYSTEM = (
    "You are an automotive Tier-1 industry intelligence analyst.\n"
    "RULES:\n"
    "- Use ONLY the provided events.\n"
    "- Do NOT invent facts.\n"
    "- Every bullet MUST include at least one source URL.\n"
    "- Keep it concise and executive.\n"
)

def write_weekly_report(model: str, payload: dict) -> str:
    prompt = (
        "Write a Weekly Global Automotive Industry Briefing (Tier-1 lens) in English.\n"
        "Required sections:\n"
        "1) Executive Summary (Top 10)\n"
        "2) OEM & Demand Signals\n"
        "3) Suppliers (Tier-1/Tier-2)\n"
        "4) Footprint & Operations\n"
        "5) EV / Battery / Materials\n"
        "6) Semis / Electronics / SDV / ADAS\n"
        "7) Policy & Trade\n"
        "8) Quality & Recalls\n"
        "9) Watchlist (next 2–4 weeks)\n\n"
        "Formatting:\n"
        "- Use short bullets.\n"
        "- For each bullet include: What happened — Why it matters for Tier-1s — Source: <url>\n"
        "- If evidence is weak or unclear, OMIT the bullet.\n\n"
        f"Input events JSON:\n{json.dumps(payload, ensure_ascii=False)}"
    )

    resp = client.responses.create(
        model=model,
        input=[{"role": "system", "content": SYSTEM},
               {"role": "user", "content": prompt}]
    )
    return resp.output_text
