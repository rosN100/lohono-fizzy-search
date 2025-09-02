#!/usr/bin/env python3
"""
Test script to debug the full flow
"""

from services.property_search import PropertySearchService
from services.date_parser import DateParserService

def test_full_flow():
    # Initialize services
    date_parser = DateParserService()
    property_search = PropertySearchService()
    
    # Test date parsing
    test_date = "2025-10-01"
    print(f"Testing date: {test_date}")
    
    # Parse date
    parsed_date = date_parser.parse_date(test_date)
    print(f"Parsed date: {parsed_date}")
    
    # Search properties
    results = property_search.search_properties("Aurelia", parsed_date)
    print(f"Search results check_date: {results['check_date']}")
    print(f"Total found: {results['total_found']}")
    print(f"Available count: {results['available_count']}")

if __name__ == "__main__":
    test_full_flow()
