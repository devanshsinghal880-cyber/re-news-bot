import json, os
from datetime import datetime, timezone
from google import genai

MODEL = "gemini-3.8-flash"
CATEGORIES = ["Residential", "Commercial", "Policy", "Finance", "Infra"]

with open("data/raw.json", encoding="utf-8") as f:
    articles = json.load(f)

def make_item(rank, a, summary="", category="General"):
    return {"rank": rank, "title": a["title"], "summary": summary,
            "category": category, "source": a["source"],
            "url": a["url"], "published_at": a["published_at"]}

def ask_gemini():
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    headlines = "\n".join(f'{i}. {a["title"]} ({a["source"]})' for i, a in enumerate(articles))
    prompt = f"""You are a real estate news editor for Indian home buyers and investors.
From the headlines below, pick the 10 most important and useful stories.
Skip duplicates, ads and very local or minor news.
Return a JSON array of exactly 10 objects, most important first:
{{"id": <headline number>, "summary": "<1-2 simple sentences explaining why it matters>",
 "category": "<one of {', '.join(CATEGORIES)}>"}}
Use only what the headline says. Do not invent numbers or facts.

Headlines:
{headlines}"""
    resp = client.models.generate_content(
        model=MODEL, contents=prompt,
        config={"response_mime_type": "application/json"})
    picks = json.loads(resp.text)
    top, used = [], set()
    for p in picks:
        i = int(p["id"])
        if 0 <= i < len(articles) and i not in used:
            used.add(i)
            top.append(make_item(len(top) + 1, articles[i], p.get("summary", ""), p.get("category", "General")))
        if len(top) == 10:
            break
    return top

try:
    items = ask_gemini()
    print("Gemini picked", len(items), "stories")
except Exception as e:
    print("Gemini failed, using fallback:", e)
    items = [make_item(i + 1, a) for i, a in enumerate(articles[:10])]

now = datetime.now(timezone.utc)
result = {"date": now.strftime("%Y-%m-%d"), "generated_at": now.isoformat(), "items": items}

os.makedirs("data/archive", exist_ok=True)
for path in ["data/news.json", f"data/archive/{result['date']}.json"]:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
print("Saved data/news.json")
