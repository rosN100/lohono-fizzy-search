#!/bin/bash

# Property Fuzzy Search API - Run Script
echo "🚀 Starting Property Fuzzy Search API..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if required packages are installed
echo "📦 Checking dependencies..."
python3 -c "import fastapi, uvicorn, pandas, rapidfuzz, dateparser, pydantic" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📥 Installing dependencies..."
    pip3 install fastapi uvicorn pandas rapidfuzz dateparser pydantic
fi

# Check if CSV file exists
if [ ! -f "Lohono Stays Mastersheet _ Dummy data for Voice bot Testing.xlsx - Availablity & Pricing (1).csv" ]; then
    echo "❌ CSV data file not found. Please ensure the CSV file is in the current directory."
    exit 1
fi

echo "✅ All dependencies and data files are ready!"
echo "🌐 Starting server on http://localhost:8000"
echo "📚 API documentation available at http://localhost:8000/docs"
echo "🔍 Test endpoint: http://localhost:8000/api/v1/properties/search?property_name=Aurelia&check_date=2025-10-01"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --reload
