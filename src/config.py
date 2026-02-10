from dataclasses import dataclass
from typing import List

@dataclass
class Settings:
    days_back: int = 7
    max_items_per_feed: int = 40
    # Cost-effective defaults; adjust later
    llm_model: str = "gpt-5-mini"
    embed_model: str = "text-embedding-3-small"
    dedup_threshold: float = 0.86
    max_events_in_report: int = 80

# Start with RSS only (stable). Add your own feeds.
RSS_FEEDS: List[str] = [
    # Examples (replace with your chosen feeds)
  "https://www.autonews.com/rss.xml"
  #"https://europe.autonews.com/rss.xml",
  #"https://www.automotiveworld.com/feed/",
  #"https://www.just-auto.com/feed/",
  #"https://www.wardsauto.com/rss.xml",
  #"https://www.automotivelogistics.media/rss",
  #"https://www.automotivemanufacturingsolutions.com/rss",
  #"https://www.supplychainbrain.com/rss/topic/auto",
  #"https://www.eetimes.com/category/automotive/feed/",
  #"https://www.electronicsweekly.com/automotive/feed",
  #"https://semiengineering.com/category/automotive/feed/",
  #"https://www.sae.org/rss",
  #"https://www.press.bmwgroup.com/global/rss",
  #"https://www.volkswagen-newsroom.com/en/rss.xml",
  #"https://www.media.stellantis.com/rss",
]

# Tier-1 lens keywords: used for scoring and section routing
KEYWORDS = {
    "oem_demand": ["sales", "deliveries", "pricing", "price cut", "inventory", "mix", "launch"],
    "suppliers": ["supplier", "contract", "award", "tier-1", "tier 1", "tier-2", "tier 2", "quote"],
    "footprint_ops": ["plant", "factory", "capacity", "shutdown", "closure", "expansion", "localization", "nearshoring"],
    "ev_battery": ["EV", "battery", "cell", "cathode", "anode", "lithium", "LFP", "NMC", "gigafactory", "recycling"],
    "electronics_sdv": ["ECU", "E/E", "chip", "semiconductor", "ADAS", "software-defined", "SDV", "cybersecurity"],
    "policy_trade": ["tariff", "subsidy", "regulation", "emissions", "homologation", "ban", "duty"],
    "quality_recalls": ["recall", "defect", "safety", "campaign", "investigation"],
}
