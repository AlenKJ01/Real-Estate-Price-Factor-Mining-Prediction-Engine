# 🏠 Real-Estate-Price-Factor-Mining-Prediction-Engine
## 📊 AI-Powered Future Price Factor Analysis Engine  
**Built with Streamlit + Gemini + Serper + MongoDB**

---

## 🚀 Overview

The **UK Real Estate Price Predictor** is an intelligent data analytics system designed to identify **future price-driving events** in UK regions (2025–2029) using real-time search intelligence and generative AI.

It automatically:
- Fetches and summarizes **real-world future development events** from the web.
- Analyzes **impact factors** like amenities, macroeconomic trends, and geography.
- Stores results in **MongoDB** and generates a structured JSON report.
- Uses **Gemini 2.5 Flash** to interpret search data and extract real, location-specific events.
- Optionally visualized through **Streamlit dashboards**.

---

## 🧠 Core Idea

> “Property prices are influenced by what’s coming next — not what’s already there.”

This project leverages **Generative AI** and **real-time search APIs** to identify those upcoming factors — like a new hospital, school, or infrastructure plan — and ranks their **impact confidence** and **timeline** relevance.

---

## 🧩 Tech Stack

| Layer | Technology |
|-------|-------------|
| **Language** | Python 3.10+ |
| **Frontend (UI)** | Streamlit |
| **AI Model** | Google Gemini 2.5 Flash |
| **Search Engine** | Serper (Google Search API) |
| **Database** | MongoDB |
| **Data Validation** | Postcodes.io (for UK validation) |
| **Environment Management** | python-dotenv |
| **File Handling** | JSON |

---

## ⚙️ Architecture Overview



---

## 🧮 Key Components & Functions

### **1. Main(postcode)**
Main entry function that runs the pipeline:
- Iterates through all price factor categories.
- Performs search queries.
- Summarizes results with Gemini.
- Validates and filters data.
- Saves output to MongoDB and JSON file.

---

### **2. Search_serper(query)**
- Sends queries to the **Serper API** for real-time Google search results.
- Returns top 10 structured results as JSON.

---

### **3. Summarize_with_gemini(factor, search_result)**
- Sends search snippets to **Gemini 2.5 Flash**.
- Instructs Gemini to:
  - Extract only future **UK-based events (2025–2029)**.
  - Return output as one-liners with **event + link + year**.
- Returns structured event data and a confidence score.

---

### **4. Extract_location(summary, postcode)**
- Validates event location against **Postcodes.io API**.
- Ensures the event is within the same district or parish as the target postcode.

---

### **5. Calculate_impact_score(summary, confidence_score)**
- Evaluates whether the summarized event implies a **positive** or **negative** price impact.
- Adjusts confidence accordingly using a sentiment-based heuristic.

---

### **6. MongoDB Integration**
The program automatically:
- Creates a database `PricePrediction`
- Collection: `PriceFactors`
- Inserts or updates the entry by postcode

Example record:
```json
{
    "postcode": "SW3",
    "timestamp": "2025-11-04 10:22:01",
    "factors": {
        "amenities": {
            "Future hospitals or clinics": {
                "query": "...",
                "events": [
                    {
                        "event": "New NHS hospital opening in 2026 – https://gov.uk/news",
                        "timeline": 2026,
                        "link": "https://gov.uk/news",
                        "location": "Chelsea (SW3)"
                    }
                ],
                "confidence_score": 0.8,
                "impact_score": 0.9
            }
        }
    }
}
```

---

## 💾 Output

For each postcode:
- Generates a JSON file → SW3_price_factors.json
- Stores the same structure in MongoDB.

---

### 🧰 Installation & Setup
## 1️⃣ Clone the repository
```bash
git clone https://github.com/AlenKJ01/Real-Estate-Price-Factor-Mining-Prediction-Engine
.git
cd Real-Estate-Price-Factor-Mining-Prediction-Engine
```

## 2️⃣ Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate    # for Mac/Linux
venv\Scripts\activate       # for Windows
```

## 3️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

## 4️⃣ Setup environment variables

Create a .env file in the root directory:

```bash
SERPER_API_KEY=your_serper_api_key
GEMINI_API_KEY=your_gemini_api_key
```

## 5️⃣ Start MongoDB

Ensure MongoDB service is running locally on:
```bash
mongodb://localhost:27017
```
OR run via Streamlit interface (if you’ve integrated it):
```bash
streamlit run app.py
```

---

### 📊 Example Output (Console)

```bash
🔍 Category: Amenities
   • Searching: New school construction impact on property price in SW3
     → Chelsea High School expansion in 2026 – https://gov.uk/plans
✅ Data saved to: SW3_price_factors.json
✅ Updated existing postcode 'SW3' in MongoDB.
📁 Current working directory: C:\Users\Alen\PricePredictor
```
