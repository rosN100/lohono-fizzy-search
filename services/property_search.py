import pandas as pd
from typing import List, Dict, Any, Optional
from rapidfuzz import fuzz, process
import logging
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

class PropertySearchService:
    """
    Service for fuzzy searching properties in CSV data
    """
    
    def __init__(self, csv_file_path: str = "Lohono Stays Mastersheet _ Dummy data for Voice bot Testing.xlsx - Availablity & Pricing (1).csv"):
        self.csv_file_path = csv_file_path
        self.similarity_threshold = 70  # 70% similarity threshold as per PRD
        self._data_cache = None
        self._load_data()
    
    def _load_data(self):
        """
        Load CSV data into memory
        """
        try:
            logger.info(f"Loading data from {self.csv_file_path}")
            self._data_cache = pd.read_csv(self.csv_file_path)
            
            # Clean column names (remove spaces)
            self._data_cache.columns = self._data_cache.columns.str.strip()
            
            # Ensure date column is in proper format
            self._data_cache['date'] = pd.to_datetime(self._data_cache['date']).dt.strftime('%Y-%m-%d')
            
            logger.info(f"Loaded {len(self._data_cache)} records")
            logger.info(f"Columns: {list(self._data_cache.columns)}")
            
        except Exception as e:
            logger.error(f"Error loading CSV data: {e}")
            raise e
    
    def search_properties(self, property_name: str, check_in_date: str, check_out_date: str) -> Dict[str, Any]:
        """
        Search for properties using fuzzy matching and check availability for date range
        
        Args:
            property_name: Name of the property to search for
            check_in_date: Check-in date in YYYY-MM-DD format
            check_out_date: Check-out date in YYYY-MM-DD format
            
        Returns:
            Dict containing search results
        """
        try:
            logger.info(f"Searching for '{property_name}' from {check_in_date} to {check_out_date}")
            if self._data_cache is None:
                raise ValueError("Data not loaded")
            
            # Validate date range
            if not self._validate_date_range(check_in_date, check_out_date):
                return self._invalid_date_range_response(property_name, check_in_date, check_out_date)
            
            # Get all unique property identifiers
            all_property_names = self._data_cache['Identifier'].unique().tolist()
            
            if not all_property_names:
                return self._no_properties_found_response(property_name, check_in_date, check_out_date)
            
            # Perform fuzzy search
            fuzzy_matches = self._fuzzy_search_properties(property_name, all_property_names)
            
            if not fuzzy_matches:
                return self._no_properties_found_response(property_name, check_in_date, check_out_date)
            
            # Get availability data for matched properties for the date range
            property_data = self._get_property_availability_range(fuzzy_matches, check_in_date, check_out_date)
            
            # Format response
            return self._format_search_response(
                property_name, check_in_date, check_out_date, fuzzy_matches, property_data
            )
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            raise e
    
    def _fuzzy_search_properties(self, search_term: str, all_properties: List[str]) -> List[str]:
        """
        Perform fuzzy search on property names
        """
        search_term_lower = search_term.lower().strip()
        
        # First, try exact partial matches (case insensitive)
        direct_matches = [
            prop for prop in all_properties
            if search_term_lower in prop.lower()
        ]
        
        # If we have direct matches, use them (more precise)
        if direct_matches:
            logger.info(f"Found {len(direct_matches)} direct matches for '{search_term}'")
            return direct_matches
        
        # If no direct matches, use fuzzy matching
        matches = process.extract(
            search_term_lower,
            [prop.lower() for prop in all_properties],
            scorer=fuzz.partial_ratio,
            limit=20  # Limit to top 20 matches
        )
        
        # Filter by similarity threshold
        fuzzy_matches = [
            all_properties[i] for i, (match, score, _) in enumerate(matches)
            if score >= self.similarity_threshold
        ]
        
        logger.info(f"Found {len(fuzzy_matches)} fuzzy matches for '{search_term}'")
        return fuzzy_matches

    def _validate_date_range(self, check_in_date: str, check_out_date: str) -> bool:
        """
        Validate that check_in_date is before check_out_date
        """
        try:
            check_in = datetime.strptime(check_in_date, "%Y-%m-%d")
            check_out = datetime.strptime(check_out_date, "%Y-%m-%d")
            return check_in < check_out
        except ValueError:
            return False

    def _get_date_range(self, start_date: str, end_date: str) -> List[str]:
        """
        Generate list of dates between start_date and end_date (exclusive of end_date)
        """
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        date_list = []
        current_date = start
        while current_date < end:
            date_list.append(current_date.strftime("%Y-%m-%d"))
            current_date += timedelta(days=1)
        
        return date_list

    def _get_property_availability_range(self, property_names: List[str], check_in_date: str, check_out_date: str) -> List[Dict[str, Any]]:
        """
        Get availability data for properties across a date range
        """
        try:
            # Get all dates in the range
            date_range = self._get_date_range(check_in_date, check_out_date)
            
            property_data = []
            for prop_name in property_names:
                # Check availability for all dates in range
                is_available = True
                total_price = 0
                daily_prices = []
                
                for date in date_range:
                    day_data = self._data_cache[
                        (self._data_cache['date'] == date) & 
                        (self._data_cache['Identifier'] == prop_name)
                    ]
                    
                    if day_data.empty:
                        is_available = False
                        break
                    
                    day_record = day_data.iloc[0]
                    if day_record['status'] != 'available':
                        is_available = False
                        break
                    
                    try:
                        price = int(day_record['listing price']) if day_record['listing price'] is not None else 0
                        daily_prices.append(price)
                        total_price += price
                    except (ValueError, TypeError):
                        daily_prices.append(0)
                
                # Calculate average per-night price
                per_night_price = int(total_price / len(date_range)) if date_range and total_price > 0 else None
                
                property_data.append({
                    'Identifier': prop_name,
                    'availability': 'available' if is_available else 'information not available. experience team will contact the caller.',
                    'per_night_price': per_night_price,
                    'is_available': is_available
                })
            
            return property_data
            
        except Exception as e:
            logger.error(f"Error fetching property availability range: {e}")
            return []


    
    def _format_search_response(
        self, 
        search_term: str, 
        check_in_date: str,
        check_out_date: str,
        matched_properties: List[str], 
        property_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Format the search response according to the VAPI specification
        """
        # Create a mapping of property name to data
        property_map = {prop["Identifier"]: prop for prop in property_data}
        
        # Build properties list
        properties_list = []
        available_count = 0
        prices = []
        
        for prop_name in matched_properties:
            if prop_name in property_map:
                prop_data = property_map[prop_name]
                
                if prop_data["is_available"]:
                    properties_list.append({
                        "name": prop_name,
                        "availability": prop_data["availability"],
                        "per_night_price": prop_data["per_night_price"]
                    })
                    
                    # Only add to prices list if price is valid
                    if prop_data["per_night_price"] is not None:
                        prices.append(prop_data["per_night_price"])
                        
                    available_count += 1
                else:
                    # Property not available - return simple message
                    properties_list.append({
                        "name": prop_name,
                        "availability": "Property data not available.",
                        "per_night_price": None
                    })
            else:
                # Property exists but no data for this date range
                properties_list.append({
                    "name": prop_name,
                    "availability": "Property data not available.",
                    "per_night_price": None
                })
        
        # Calculate price range
        price_range = None
        if prices:
            price_range = {
                "min": min(prices),
                "max": max(prices)
            }
        
        # Generate summary message
        summary = self._generate_summary_range(
            search_term, check_in_date, check_out_date, len(matched_properties), 
            available_count, price_range
        )
        
        return {
            "found": True,
            "search_term": search_term,
            "check_in_date": check_in_date,
            "check_out_date": check_out_date,
            "total_found": len(matched_properties),
            "available_count": available_count,
            "properties": properties_list,
            "price_range": price_range,
            "summary": summary
        }
    
    def _generate_summary(
        self, 
        search_term: str, 
        check_date: str, 
        total_found: int, 
        available_count: int, 
        price_range: Optional[Dict[str, int]]
    ) -> str:
        """
        Generate a human-readable summary message
        """
        # Format date for display
        try:
            date_obj = datetime.strptime(check_date, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%B %d, %Y")
        except:
            formatted_date = check_date
        
        if total_found == 0:
            return f"No properties found matching '{search_term}'."
        
        if available_count == 0:
            return f"Found {total_found} {search_term} properties, but none are available on {formatted_date}."
        
        if price_range:
            price_text = f"Prices range from ₹{price_range['min']:,} to ₹{price_range['max']:,} per night."
        else:
            price_text = "Pricing information available."
        
        return f"Found {total_found} {search_term} properties available on {formatted_date}. {price_text} {available_count} properties are currently available."

    def _generate_summary_range(
        self, 
        search_term: str, 
        check_in_date: str,
        check_out_date: str,
        total_found: int, 
        available_count: int, 
        price_range: Optional[Dict[str, int]]
    ) -> str:
        """
        Generate a human-readable summary message for date range
        """
        # Format dates for display
        try:
            check_in_obj = datetime.strptime(check_in_date, "%Y-%m-%d")
            check_out_obj = datetime.strptime(check_out_date, "%Y-%m-%d")
            formatted_check_in = check_in_obj.strftime("%B %d, %Y")
            formatted_check_out = check_out_obj.strftime("%B %d, %Y")
        except:
            formatted_check_in = check_in_date
            formatted_check_out = check_out_date
        
        if total_found == 0:
            return f"No properties found matching '{search_term}'."
        
        if available_count == 0:
            return f"Found {total_found} {search_term} properties, but none are available from {formatted_check_in} to {formatted_check_out}."
        
        if price_range:
            price_text = f"Per-night prices range from ₹{price_range['min']:,} to ₹{price_range['max']:,}."
        else:
            price_text = "Pricing information available."
        
        return f"Found {total_found} {search_term} properties for {formatted_check_in} to {formatted_check_out}. {price_text} {available_count} properties are currently available."

    def _no_properties_found_response(self, search_term: str, check_in_date: str, check_out_date: str) -> Dict[str, Any]:
        """
        Generate response when no properties are found
        """
        return {
            "found": False,
            "search_term": search_term,
            "check_in_date": check_in_date,
            "check_out_date": check_out_date,
            "total_found": 0,
            "available_count": 0,
            "properties": [],
            "price_range": None,
            "summary": f"No properties found matching '{search_term}'. Try searching for 'Aurelia', 'Siena', or 'Monforte'.",
            "message": f"No properties found matching '{search_term}'. Try searching for 'Aurelia', 'Siena', or 'Monforte'."
        }

    def _invalid_date_range_response(self, search_term: str, check_in_date: str, check_out_date: str) -> Dict[str, Any]:
        """
        Generate response for invalid date range
        """
        return {
            "found": False,
            "search_term": search_term,
            "check_in_date": check_in_date,
            "check_out_date": check_out_date,
            "total_found": 0,
            "available_count": 0,
            "properties": [],
            "price_range": None,
            "summary": "Invalid date range: check-in date must be before check-out date.",
            "message": "Invalid date range: check-in date must be before check-out date."
        }
