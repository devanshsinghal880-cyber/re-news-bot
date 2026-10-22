import calendar, json, os, re, time
from datetime import datetime, timezone
from difflib import SequenceMatcher
import feedparser

def gnews(query):
    q = query.replace(" ", "+")
    return f"https://news.google.com/rss/search?q={q}+when:1d&hl=en-IN&gl=IN&ceid=IN:en"

# Kahan se news aayegi (search words badal ke aur add kar sakte ho)
FEEDS = [
    gnews("real estate india"),
    gnews("RERA"),
    gnews("housing sales india"),
    gnews("home loan rates india"),
    gnews("commercial real estate india"),
]

# Ye words headline me hon to news important maani jaayegi
KEYWORDS = ["rera", "housing", "home loan", "repo rate", "property", "real estate",
            "launch", "sales", "mumbai", "delhi", "gurugram", "noida", "bengaluru",
            "pune", "hyderabad", "commercial", "office", "infra"]

def fetch_all():
    items = []
    for url in FEEDS:
        feed = feedparser.parse(url)
        for e in feed.entries:
            title = re.sub(r"\s+-\s+[^-]+$", "", e.get("title", "")).strip()
            p = e.get("published_parsed")
            ts = calendar.timegm(p) if p else time.time()
            items.append({
                "title": title,
                "source": e.get("source", {}).get("title", "Unknown"),
                "url": e.get("link", ""),
                "published_at": datetime.fromtimestamp(ts, timezone.utc).isoformat(),
                "ts": ts,
            })
    print(f"Fetched {len(items)} articles")
    return items

def dedupe(items):
    unique = []
    for it in items:
        t = it["title"].lower()
        if any(SequenceMatcher(None, t, u["title"].lower()).ratio() > 0.8 for u in unique):
            continue
        unique.append(it)
    return unique

def score(it):
    hours_old = (time.time() - it["ts"]) / 3600
    hits = sum(1 for k in KEYWORDS if k in it["title"].lower())
    return max(0, 24 - hours_old) + hits * 5

if __name__ == "__main__":
    items = dedupe(fetch_all())
    items.sort(key=score, reverse=True)
    top = items[:40]
    for it in top:
        it.pop("ts")
    os.makedirs("data", exist_ok=True)
    with open("data/raw.json", "w", encoding="utf-8") as f:
        json.dump(top, f, ensure_ascii=False, indent=2)
    print(f"Saved top {len(top)} articles to data/raw.json")
