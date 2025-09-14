Requirement
We need to perform fuzzy search on ~8,000 rows of Google Sheets data. The data contains property details and pricing.
A webhook URL should be provided, through which the Vapi voice agent will send the property name and the date for which availability needs to be checked. Our system should:
1. Search for the closest matching property/properties (fuzzy search, since the name may not always be an exact match).
2. Process the availability and pricing results.
3. Respond back on the same webhook with structured information.
Example
- Input from webhook: "villa Aurelia" or "Aurelia".
- In the Google Sheet, there are multiple variations:
    - Aurelia Villa C
    - Aurelia Villa D
    - Aurelia Villa E
    - Aurelia Villa F
    - Aurelia Villa G
- Expected response:
5 matching properties found: Aurelia Villa C, Aurelia Villa D, Aurelia Villa E, Aurelia Villa F, Aurelia Villa G.  
Per-night prices:  
- Aurelia Villa C – 67,000  
- Aurelia Villa D – 56,000  
- Aurelia Villa E – 78,000  
- Aurelia Villa F – 78,000  
- Aurelia Villa G – 40,000  
Available on 9th Sept: Aurelia Villa C, Aurelia Villa D.
Tech Stack
- Backend: Python, FastAPI
- Database: Google Sheets (current). If needed for performance and scalability, data can be migrated to Supabase.
webhook response format:
​
{
    "results": [
        {
            "toolCallId": "X",
            "result": "Y"
        }
    ]
}

Data Structure Clarification ✅
Sheet has exactly the columns needed:
•	Identifier (property name)
•	date (YYYY-MM-DD format)
•	listing price (numeric)
•	status (available/unavailable)

Data Structure
- Source: Google Sheets → Supabase migration
- Columns: Identifier, date, listing_price, status
- Records: ~8000 rows with daily availability through 2025
- Date Format: YYYY-MM-DD (standardized)

Input format vapi 
{“toolCallId”: “call_abc123”,
 “parameters”: {
   “property_name”: “villa Aurelia”,
   “check_date”: “2025-09-09”  // or flexible formats}}
Enhanced Processing Logic
1. Fuzzy Search: Match property names with 70%+ similarity
2. Handle Variations:
    - "Aurelia" → matches "Aurelia Villa C", "Aurelia Villa D", etc.
    - "Villa Aurelia" → same matches
    - "Aurilia" (typo) → matches Aurelia properties
3. Date Processing: Convert various date formats to YYYY-MM-DD
4. Filter & Aggregate: Get all matching properties for the date

Sample Response Format
{
  "results": [
    {
      "toolCallId": "call_abc123",
      "result": {
        "found": true,
        "search_term": "Aurelia",
        "check_date": "2025-09-09",
        "total_found": 5,
        "available_count": 5,
        "properties": [
          {
            "name": "Aurelia Villa C",
            "price": 42400,
            "status": "available"
          },
          {
            "name": "Aurelia Villa D",
            "price": 42400,
            "status": "available"
          },
          {
            "name": "Aurelia Villa E",
            "price": 62800,
            "status": "available"
          },
          {
            "name": "Aurelia Villa F",
            "price": 62800,
            "status": "available"
          },
          {
            "name": "Aurelia Villa G",
            "price": 42400,
            "status": "available"
          }
        ],
        "price_range": {
          "min": 42400,
          "max": 62800
        },
        "summary": "Found 5 Aurelia Villa properties available on September 9th, 2025. Prices range from ₹42,400 to ₹62,800 per night. All properties are currently available."
      }
    }
  ]
}

Fuzzy Matching Strategy
Data shows these patterns:
- “Aurelia Villa C, D, E, F, G”
- “Siena Villa A, C, D, E, F, G”
- “Monforte - Villa B, D, E, F, H, I”
- “Sacri Borod Hill 4, 5, 6, 7, 8, 9”

def fuzzy_search_properties(search_term, date):
  # 1. Direct partial match
  direct_matches = properties.filter(Identifier.ilike(f’%{search_term}%’))

  # 2. Fuzzy match with threshold
fuzzy_matches = []
for property in all_properties:
    if fuzz.partial_ratio(search_term.lower(), 
                        property.name.lower()) >= 70:
        fuzzy_matches.append(property)

# 3. Filter by date and status
return filter_by_date_and_status(matches, date)

Fuzzy Search & Availability Check – Code Guide
1. Input Handling
    - Accept search_term (property name from webhook).
    - Accept date (availability date to check).
2. Search Process
    - Direct Partial Match: Check if the search_term exists as a substring inside property names.
    - Fuzzy Match: Use a string similarity algorithm (e.g., RapidFuzz partial_ratio) or Postgres pg_trgm similarity to catch near matches (≥70% threshold).
    - Combine Results: Merge direct and fuzzy matches, ensuring no duplicates.
3. Availability Filter
    - For each matched property, check availability against the given date (e.g., booking table, calendar, or availability flag).
    - Only return properties that are available on the requested date.
4. Response Construction
    - Prepare a structured response containing:
        - Total matches found
        - Property names
        - Availability status
        - Pricing details
        - Optional: min–max price range and summary message
5. Output
    - Return results as a JSON object through the webhook response.

Date Handling Examples
def parse_date(date_input):
    # Possible input formats:
    # "2025-09-09"     → standard format
    # "9th Sept 2025"  → VAPI might send
    # "September 9"    → natural language
    # "Sept 9"         → short form

    # Convert all variants to standard format: YYYY-MM-DD
    return standardized_date

Database Schema (Supabase)
CREATE TABLE properties (
    id SERIAL PRIMARY KEY,
    identifier TEXT NOT NULL,
    date DATE NOT NULL,
    listing_price INTEGER NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_properties_identifier ON properties(identifier);
CREATE INDEX idx_properties_date ON properties(date);
CREATE INDEX idx_properties_status ON properties(status);

Perfect Test Cases from Data
Test Case 1: Exact Match
search_term = "Aurelia Villa C"
date = "2025-09-09"
# Expected: 1 result → ₹42,400

Test Case 2: Partial Match
search_term = "Aurelia"
date = "2025-09-09"
# Expected: 5 results → Aurelia Villa C, D, E, F, G

Test Case 3: Typo Handling
search_term = "Aurilia"  # typo
date = "2025-09-09"
# Expected: 5 results (fuzzy match → Aurelia Villas)

Test Case 4: Series Search
search_term = "Siena Villa"
date = "2025-09-09"
# Expected: 6 results → Siena Villa A, C, D, E, F, G

