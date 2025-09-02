# Property Fuzzy Search API

A FastAPI-based fuzzy search service for property availability with Vapi voice agent integration.

## 🚀 Features

- **Fuzzy Search**: 70%+ similarity matching for property names using RapidFuzz
- **Natural Language Date Parsing**: Handles formats like "9th Sept 2025", "September 9", "2025-09-09"
- **CSV-based Data**: No database setup required - works directly with CSV files
- **Vapi Webhook Integration**: Ready for voice agent integration
- **Comprehensive Error Handling**: User-friendly error responses
- **Production Ready**: FastAPI with automatic API documentation

## 📋 Requirements

- Python 3.8+
- CSV data file: `Lohono Stays Mastersheet _ Dummy data for Voice bot Testing.xlsx - Availablity & Pricing (1).csv`

## 🛠️ Installation

1. **Clone or download the project files**

2. **Install dependencies**:
   ```bash
   pip3 install fastapi uvicorn pandas rapidfuzz dateparser pydantic
   ```

3. **Ensure CSV data file is present**:
   - The CSV file should be in the project root directory
   - Expected columns: `Identifier`, `date`, `listing price`, `status`

## 🚀 Quick Start

### Option 1: Using the run script (Recommended)
```bash
./run.sh
```

### Option 2: Manual start
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📚 API Endpoints

### 1. Vapi Webhook (Main Endpoint)
```
POST /api/v1/webhook/vapi
```

**Request**:
```json
{
  "toolCallId": "call_abc123",
  "parameters": {
    "property_name": "villa Aurelia",
    "check_date": "9th Sept 2025"
  }
}
```

**Response**:
```json
{
  "results": [{
    "toolCallId": "call_abc123",
    "result": {
      "found": true,
      "search_term": "villa Aurelia",
      "check_date": "2025-09-09",
      "total_found": 5,
      "available_count": 5,
      "properties": [
        {
          "name": "Aurelia Villa C",
          "price": 42400,
          "status": "available"
        }
      ],
      "price_range": {"min": 42400, "max": 62800},
      "summary": "Found 5 villa Aurelia properties available on September 9, 2025..."
    }
  }]
}
```

### 2. Direct Search (Testing)
```
GET /api/v1/properties/search?property_name=Aurelia&check_date=2025-10-01
```

### 3. Health Check
```
GET /health
```

## 🧪 Testing

### Test Fuzzy Search
```bash
curl -X GET "http://localhost:8000/api/v1/properties/search?property_name=Aurelia&check_date=2025-10-01"
```

### Test Natural Language Dates
```bash
curl -X POST "http://localhost:8000/api/v1/webhook/vapi" \
  -H "Content-Type: application/json" \
  -d '{
    "toolCallId": "test_123",
    "parameters": {
      "property_name": "Aurelia",
      "check_date": "9th Sept 2025"
    }
  }'
```

### Test Typo Handling
```bash
curl -X GET "http://localhost:8000/api/v1/properties/search?property_name=Aurilia&check_date=2025-10-01"
```

## 🔍 Fuzzy Search Examples

The API handles various search patterns:

| Search Term | Matches | Example Properties |
|-------------|---------|-------------------|
| "Aurelia" | 5 properties | Aurelia Villa C, D, E, F, G |
| "Siena Villa" | 6 properties | Siena Villa A, C, D, E, F, G |
| "Monforte" | 6 properties | Monforte - Villa B, D, E, F, H, I |
| "Aurilia" (typo) | 5 properties | Same as "Aurelia" (70% similarity) |

## 📅 Date Format Support

The API supports multiple date formats:

| Input Format | Example | Output |
|--------------|---------|--------|
| ISO Date | `2025-09-09` | `2025-09-09` |
| Natural Language | `9th Sept 2025` | `2025-09-09` |
| Short Form | `Sept 9` | `2025-09-09` |
| Full Month | `September 9` | `2025-09-09` |

## 🏗️ Project Structure

```
lohono-fuzzy-search/
├── main.py                 # FastAPI application
├── models/
│   └── webhook_models.py   # Pydantic models
├── services/
│   ├── date_parser.py      # Date parsing service
│   └── property_search.py  # Fuzzy search service
├── utils/
│   └── error_handler.py    # Error handling
├── run.sh                  # Run script
├── requirements.txt        # Dependencies
└── README.md              # This file
```

## 🔧 Configuration

### Fuzzy Search Threshold
- **Default**: 70% similarity
- **Location**: `services/property_search.py`
- **Variable**: `self.similarity_threshold`

### Date Parser Settings
- **Default**: YMD format (Year-Month-Day)
- **Location**: `services/date_parser.py`
- **Variable**: `self.settings`

## 🚨 Error Handling

The API provides comprehensive error responses:

### Invalid Date Format
```json
{
  "results": [{
    "toolCallId": "call_123",
    "result": {
      "found": false,
      "summary": "Invalid date format: invalid-date. Please use formats like '2025-09-09', '9th Sept 2025', or 'September 9'."
    }
  }]
}
```

### No Properties Found
```json
{
  "results": [{
    "toolCallId": "call_123",
    "result": {
      "found": false,
      "summary": "No properties found matching 'NonExistent Villa'. Try searching for 'Aurelia', 'Siena', or 'Monforte'."
    }
  }]
}
```

## 📊 Performance

- **Data Size**: ~6,834 property records
- **Search Time**: <100ms for fuzzy search
- **Memory Usage**: ~50MB (CSV loaded in memory)
- **Concurrent Requests**: Supports multiple simultaneous requests

## 🔒 Security Notes

- CORS is enabled for all origins (configure for production)
- No authentication implemented (add as needed)
- Input validation through Pydantic models

## 🐛 Troubleshooting

### Common Issues

1. **CSV file not found**
   - Ensure the CSV file is in the project root
   - Check the exact filename matches

2. **Import errors**
   - Run `pip3 install -r requirements.txt`
   - Ensure Python 3.8+ is installed

3. **Date parsing issues**
   - Use ISO format (YYYY-MM-DD) for reliable parsing
   - Check date is not too far in the past/future

4. **No properties found**
   - Verify the date exists in the CSV data
   - Check property name spelling
   - Try partial matches (e.g., "Aurelia" instead of "Aurelia Villa C")

## 📈 Future Enhancements

- [ ] Database integration (PostgreSQL/Supabase)
- [ ] Caching layer (Redis)
- [ ] Authentication & authorization
- [ ] Rate limiting
- [ ] Advanced filtering options
- [ ] Property image support
- [ ] Real-time availability updates

## 📄 License

This project is created for Lohono Stays property search integration.

## 🤝 Support

For issues or questions, please check the troubleshooting section or review the API documentation at `/docs` endpoint.
