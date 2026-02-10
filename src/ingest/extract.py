import requests
import trafilatura

def fetch_html(url: str, timeout=25) -> str:
    r = requests.get(url, timeout=timeout, headers={"User-Agent": "auto-weekly-brief/1.0"})
    r.raise_for_status()
    return r.text

def extract_text(html: str) -> str:
    text = trafilatura.extract(html, include_comments=False, include_tables=False)
    return (text or "").strip()