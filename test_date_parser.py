#!/usr/bin/env python3
"""
Test script to debug date parsing issues
"""

from services.date_parser import DateParserService

def test_date_parsing():
    parser = DateParserService()
    
    test_dates = [
        "2025-10-01",
        "2025-09-09", 
        "9th Sept 2025",
        "September 9",
        "Sept 9"
    ]
    
    for date_input in test_dates:
        try:
            result = parser.parse_date(date_input)
            print(f"Input: '{date_input}' -> Output: '{result}'")
        except Exception as e:
            print(f"Input: '{date_input}' -> Error: {e}")

if __name__ == "__main__":
    test_date_parsing()
