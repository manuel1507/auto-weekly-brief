from dataclasses import dataclass

@dataclass
class Settings:
    days_back: int = 7
    embed_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-5-mini"

RSS_FEEDS = [
    # Add your RSS feeds here
]