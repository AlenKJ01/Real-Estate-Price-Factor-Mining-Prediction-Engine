
## updated code with using mongodb and streamlit with link, timeline, summary altogether

import os
import requests
import google.generativeai as genai
import json
import time
import re
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime

# === Load API Keys ===
load_dotenv()
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

# === MongoDB Configuration ===
MONGO_URI = "mongodb://localhost:27017"
MONGO_DB = "PricePrediction"
MONGO_COLLECTION = "PriceFactors"

# === Create MongoDB client ===
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[MONGO_DB]
collection = db[MONGO_COLLECTION]

# === Constants ===
TEST_MODE = False
search_count = 0

current_year = datetime.now().year

HEADERS = {
    "X-API-KEY": SERPER_API_KEY,
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AlenCustomBot/1.0"
}

PRICE_FACTORS = {
    "Amenities": [
        "Future hospitals or clinics", "New school construction", "University expansion",
        "Retail park or shopping center development", "New entertainment facilities",
        "New parks or recreational green spaces", "Police or fire station construction",
        "Library or community center projects", "Religious or cultural center construction",
        "EV charging station rollouts"
    ],
    "Macro": [
        "Interest Rate Trends", "Inflation Rate or CPI", "Mortgage Affordability Policies",
        "Stamp Duty Changes", "Government Housing Policies", "Planning law Reform",
        "Rental Regulation Zones", "Population Growth or Migration", "Employment or Unemployment Rate",
        "Post-Election Political Changes"
    ],
    "Geographic": [
        "Flood risk zones", "Low elevation or slope", "Near water bodies", "Soil quality or subsidence risk",
        "Near greenbelt or AONB areas", "Good air quality", "High noise pollution",
        "South-facing or high sunlight area", "Seismic or mining instability", "Urban vs rural zoning"
    ]
}

# === Helper Functions ===

def extract_location(summary, postcode):
    """
    Extract a location from the event summary and ensure it's inside the given postcode.
    Uses postcodes.io to validate UK locations.
    """

    # Basic regex / keyword extraction for place names (can be replaced with NLP if needed)
    words = summary.split()
    candidate_places = [w.strip(",.") for w in words if w.istitle() and len(w) > 2]

    # Validate each candidate place against postcode API
    for place in candidate_places:
        try:
            res = requests.get(f"https://api.postcodes.io/postcodes/{postcode}")
            if res.status_code == 200:
                data = res.json()["result"]
                if place.lower() in (data["admin_ward"].lower(), data["admin_district"].lower(),
                                     data["parish"].lower() if data["parish"] else ""):
                    return f"{place} ({postcode})"
        except Exception:
            continue

    # fallback if nothing matched
    return f"Within {postcode}"



def calculate_impact_score(summary, confidence_score):
    summary = summary.lower()
    positive = ["increase", "boost", "raise", "improve", "benefit", "positive", "growth"]
    negative = ["decline", "drop", "reduce", "negative", "decrease", "fall", "risk"]
    score = confidence_score
    if any(word in summary for word in positive):
        score += 0.1
    if any(word in summary for word in negative):
        score -= 0.1
    return round(min(max(score, 0.0), 1.0), 2)

def search_serper(query):
    global search_count
    search_count += 1
    payload = { "q": query, "num": 1 if TEST_MODE else 10 }
    try:
        response = requests.post("https://google.serper.dev/search", headers=HEADERS, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Search error for '{query}':", e)
        return {}

def summarize_with_gemini(factor, search_result):
    global search_count
    search_count += 1

    prompt = f"""
    You are analyzing real estate price factors in UK.

    Factor: {factor}
    Search Results: {search_result}

    Task:
    - Only extract concrete and actual future events only happening inside UK(United Kingdom), based on its postcode with real sources or government/local authority data.
    - Only extract concrete future events happening between 2025 and 2029.
    - Each event must be in one line: "<Event> in <Year> – <Link>".
    - If no valid event in this range, return "skip".
    - Keep output short, factual, and linked.
    """

    try:
        response = model.generate_content(prompt)
        summary = response.text.strip()

        if summary.lower() == "skip":
            return [], 0  # No valid events → empty list

        # Parse lines into structured events
        events = []
        for line in summary.split("\n"):
            if not line.strip():
                continue
            # Expected format: "Event in Year – Link"
            parts = line.split("–")
            if len(parts) == 2:
                event_text = parts[0].strip()
                link = parts[1].strip()
            else:
                event_text = line.strip()
                link = ""

            # Try to extract year
            year_match = re.search(r"(202[5-9])", event_text)
            if year_match:
                year = int(year_match.group(1))
                if 2025 <= year <= 2029:
                    events.append({
                        "event": event_text,
                        "timeline": year,
                        "link": link
                    })

        return events, 0.8  # 0.8 dummy confidence score for now

    except Exception as e:
        print(f"⚠️ Gemini error: {e}")
        return [], 0



# === Main Function ===

def main(postcode):
    global search_count
    search_count = 0

    all_data = {
        "postcode": postcode,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "search_count": 0,
        "factors": {
            "amenities": {},
            "macro": {},
            "geographic": {}
        }
    }

    try:
        for category, factors in PRICE_FACTORS.items():
            print(f"\n🔍 Category: {category}")
            category_key = category.lower()

            for factor in factors[:2] if TEST_MODE else factors:
                search_query = f"{factor} impact on property price in {postcode}"
                print(f"   • Searching: {search_query}")

                search_result = search_serper(search_query)
                events, score = summarize_with_gemini(factor, search_result)

                # Skip if no events returned
                if not events:
                    print(f"     → No events for {factor}. Skipped.\n")
                    continue

                # Filter events: must be 2025–2029 and UK-related
                filtered_events = []
                for ev in events:
                    summary = ev.get("event", "")
                    timeline = ev.get("timeline", "")
                    link = ev.get("link", "")
                    location = extract_location(summary, postcode)

                    # make timeline a string before checks
                    timeline_str = str(timeline).strip()

                    valid_timeline = (
                        timeline_str.isdigit() and
                        2025 <= int(timeline_str) <= 2029
                    )

                    valid_location = (
                        "UK" in summary or
                        postcode[:2].upper() in location.upper() or   # match outcode prefix
                        location.strip() != ""                        # accept extracted city/village
                    )

                    if valid_timeline and valid_location:
                        filtered_events.append({
                            "event": summary,
                            "timeline": int(timeline_str),
                            "link": link,
                            "location": location
                        })
                        print(f"     → {summary} ({timeline_str}) [Link: {link}]\n")
                    else:
                        print(f"⏭️ Skipping {factor} — not UK/2025–2029 relevant")

                # Only add factor if filtered events remain
                if filtered_events:
                    all_data["factors"][category_key][factor] = {
                        "query": search_query,
                        "events": filtered_events,
                        "confidence_score": round(score, 2),
                        "impact_score": calculate_impact_score(str(filtered_events), score)
                    }

                time.sleep(1)

        all_data["search_count"] = search_count

        # Save to JSON file
        filename = f"{postcode.replace(' ', '_')}_price_factors.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(all_data, f, indent=4, ensure_ascii=False)
        print(f"\n✅ Data saved to: {filename}")

        # Save/update in MongoDB
        result = collection.update_one(
            {"postcode": postcode},  # Search by postcode
            {"$set": all_data},      # Replace or update data
            upsert=True              # Insert if not exists
        )
        if result.upserted_id:
            print(f"✅ Inserted new postcode '{postcode}' into MongoDB.")
        else:
            print(f"✅ Updated existing postcode '{postcode}' in MongoDB.")

    except Exception as e:
        print(f"❌ Error occurred: {e}")
    finally:
        print(f"\n📁 Current working directory: {os.getcwd()}")



# === Run ===

if __name__ == "__main__":
    postcode = "SW3"
    main(postcode)
