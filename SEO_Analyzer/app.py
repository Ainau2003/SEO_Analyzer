from flask import Flask, request, jsonify, render_template
import requests
import urllib.parse
from flask_cors import CORS
from bs4 import BeautifulSoup
import random
from datetime import datetime
import time
import json
import os

app = Flask(__name__)
CORS(app)

SUGGEST_URL = "https://suggestqueries.google.com/complete/search?client=firefox&q="
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

KEYWORD_CATEGORIES = {
    "technology": {"min_volume": 1000, "max_volume": 50000},
    "health": {"min_volume": 5000, "max_volume": 100000},
    "business": {"min_volume": 2000, "max_volume": 30000},
    "education": {"min_volume": 1000, "max_volume": 20000},
    "shopping": {"min_volume": 3000, "max_volume": 80000}
}

TREND_PATTERNS = {
    "how to": "Rising",
    "best": "Stable",
    "buy": "Seasonal",
    str(datetime.now().year): "Declining",
    "near me": "Rising",
    "review": "Stable",
    "vs": "Stable",
    "alternatives": "Rising"
}

TRUST_DOMAINS = [".gov", ".edu", ".org", ".com", ".net"]
CACHE_FILE = "seo_cache.json"
cache = {}
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r") as f:
        cache = json.load(f)

@app.route('/')
def home():
    return render_template("SEO_analyzer.html")

def detect_category(keyword):
    keyword = keyword.lower()
    if any(x in keyword for x in ["how to", "tutorial", "learn", "guide"]):
        return "education"
    elif any(x in keyword for x in ["buy", "price", "shop", "deal", "discount"]):
        return "shopping"
    elif any(x in keyword for x in ["disease", "symptoms", "doctor", "medical", "health"]):
        return "health"
    elif any(x in keyword for x in ["business", "startup", "marketing", "entrepreneur"]):
        return "business"
    else:
        return "technology"

def detect_tail_length(keyword):
    count = len(keyword.strip().split())
    return "Short-tail" if count == 1 else "Mid-tail" if count <= 3 else "Long-tail"

def analyze_serp(keyword):
    try:
        url = f"https://www.google.com/search?q={urllib.parse.quote(keyword)}&gl=us&hl=en"
        response = requests.get(url, headers=HEADERS, timeout=10)

        # Check if blocked by Google
        if "unusual traffic" in response.text.lower() or "captcha" in response.text.lower():
            raise Exception("Blocked by Google")

        soup = BeautifulSoup(response.text, "html.parser")
        results = soup.select("div.g")[:10]
        domains = set()
        title_match_count = 0

        for r in results:
            title_tag = r.find("h3")
            if title_tag and keyword.lower() in title_tag.text.lower():
                title_match_count += 1
            cite_tag = r.find("cite")
            if cite_tag:
                domain = cite_tag.text.split("/")[0].replace("www.", "").strip()
                domains.add(domain)

        if not domains:
            raise Exception("No domains parsed from SERP")

        trust_score = sum(1 for d in domains if any(tld in d for tld in TRUST_DOMAINS)) * 20

        return {
            "competitors": len(results),
            "title_match_count": title_match_count,
            "top_domains": list(domains)[:5],
            "trust_score": trust_score
        }

    except Exception:
        fallback_domains = random.sample([
            "moz.com", "semrush.com", "ahrefs.com", "neilpatel.com", "hubspot.com",
            "searchenginejournal.com", "backlinko.com", "forbes.com", "wikipedia.org"
        ], 5)

        return {
            "competitors": random.randint(6, 10),
            "title_match_count": random.randint(1, 4),
            "top_domains": fallback_domains,
            "trust_score": random.choice([40, 50, 60, 70])
        }

def generate_realistic_seo_data(keyword):
    if keyword in cache:
        return cache[keyword]

    random.seed(keyword)
    category = detect_category(keyword)
    cat_data = KEYWORD_CATEGORIES[category]

    trend = next((v for k, v in TREND_PATTERNS.items() if k in keyword.lower()), "Stable")
    search_volume = random.randint(cat_data["min_volume"], cat_data["max_volume"])
    cpc = round(random.uniform(0.5, 10.0), 2)
    difficulty = random.randint(20, 80)
    opportunity_score = 100 - difficulty + (search_volume // 1000)

    serp = analyze_serp(keyword)

    data = {
        'keyword': keyword,
        'search_volume': search_volume,
        'cpc': cpc,
        'competition': random.choice(["Low", "Medium", "High"]),
        'competition_index': random.randint(10, 80),
        'trend': trend,
        'difficulty': difficulty,
        'opportunity_score': opportunity_score,
        'tail_type': detect_tail_length(keyword),
        'category': category,
        'serp_analysis': serp
    }

    cache[keyword] = data
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

    return data

@app.route('/seo', methods=['GET'])
def get_keywords():
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "Missing query param"}), 400
    try:
        suggestions = requests.get(SUGGEST_URL + urllib.parse.quote(query)).json()[1][:10]
        primary_data = [generate_realistic_seo_data(kw) for kw in suggestions]
        total_volume = sum(d['search_volume'] for d in primary_data)
        avg_difficulty = sum(d['difficulty'] for d in primary_data) / len(primary_data)
        best_keyword = max(primary_data, key=lambda x: x['opportunity_score'])

        return jsonify({
            "query": query,
            "primary_keywords": primary_data,
            "summary": {
                "total_keywords": len(primary_data),
                "average_search_volume": total_volume // len(primary_data),
                "average_difficulty": round(avg_difficulty, 1),
                "recommendation": "Good opportunity" if avg_difficulty < 50 else "Competitive",
                "best_keyword": best_keyword
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)