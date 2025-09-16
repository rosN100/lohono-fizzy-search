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
        self.similarity_threshold = 90  # 90% similarity threshold for better precision
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
            logger.info(f"Starting fuzzy search for '{property_name}' against {len(all_property_names)} properties")
            fuzzy_matches = self._fuzzy_search_properties(property_name, all_property_names)
            logger.info(f"Fuzzy search returned {len(fuzzy_matches)} matches")
            
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
        Perform fuzzy search on property names with improved matching for property variations
        """
        search_term_lower = search_term.lower().strip()
        search_words = set(search_term_lower.split())
        
        # First, try exact partial matches (case insensitive)
        direct_matches = [
            prop for prop in all_properties
            if search_term_lower in prop.lower()
        ]
        
        # If we have direct matches, use them (more precise)
        if direct_matches:
            logger.info(f"Found {len(direct_matches)} direct matches for '{search_term}'")
            return direct_matches
        
        # Enhanced matching: check for word-based matches with property variations
        word_matches = []
        for prop in all_properties:
            # Continue with normal processing
            prop_lower = prop.lower()
            prop_words = set(prop_lower.replace('-', ' ').split())
            
            # Check if search words are present in property name (ignoring order)
            # Require at least 80% of search words to match for better precision
            intersection_ratio = len(search_words.intersection(prop_words)) / len(search_words)
            
            # Additional check: ensure the main property identifier (non-generic words) match
            # Filter out common generic words like 'villa', 'house', etc.
            # Only exclude words that are standalone, not when they're part of compound words
            generic_words = {'villa', 'house', 'cottage', 'estate', 'manor', 'palace', 'resort'}
            search_specific = {word for word in search_words if word not in generic_words}
            prop_specific = {word for word in prop_words if word not in generic_words}
            
            # If we have specific words in search, require at least one to match (exact or fuzzy)
            if search_specific:
                exact_matches = search_specific.intersection(prop_specific)
                
                # Check for fuzzy matches of specific words
                fuzzy_word_matches = False
                for search_word in search_specific:
                    for prop_word in prop_specific:
                        if fuzz.ratio(search_word, prop_word) >= 85:  # 85% similarity threshold
                            fuzzy_word_matches = True
                            break
                    if fuzzy_word_matches:
                        break
                
                specific_match = len(exact_matches) > 0 or fuzzy_word_matches
                
                # Log for debugging
                if len(word_matches) < 3 or fuzzy_word_matches:
                    logger.info(f"Checking '{prop}': search_specific={search_specific}, prop_specific={prop_specific}, exact_matches={exact_matches}, fuzzy_word_matches={fuzzy_word_matches}")
                
                if search_words.issubset(prop_words) or (intersection_ratio >= 0.8 and specific_match):
                    word_matches.append(prop)
            else:
                # If only generic words, use stricter matching
                if search_words.issubset(prop_words):
                    word_matches.append(prop)
        
        if word_matches:
            logger.info(f"Found {len(word_matches)} word-based matches for '{search_term}'")
            return word_matches
        
        # Enhanced fuzzy matching with multiple scoring methods
        fuzzy_matches = []
        
        # Method 1: Standard partial ratio
        matches_partial = process.extract(
            search_term_lower,
            [prop.lower() for prop in all_properties],
            scorer=fuzz.partial_ratio,
            limit=20
        )
        
        # Method 2: Token sort ratio (handles word order differences)
        matches_token_sort = process.extract(
            search_term_lower,
            [prop.lower() for prop in all_properties],
            scorer=fuzz.token_sort_ratio,
            limit=20
        )
        
        # Method 3: Token set ratio (handles word variations)
        matches_token_set = process.extract(
            search_term_lower,
            [prop.lower() for prop in all_properties],
            scorer=fuzz.token_set_ratio,
            limit=20
        )
        
        # Combine and score all matches
        all_matches = {}
        for matches, weight in [(matches_partial, 1.0), (matches_token_sort, 1.2), (matches_token_set, 1.1)]:
            for match, score, idx in matches:
                prop_name = all_properties[idx]
                weighted_score = score * weight
                if prop_name not in all_matches or all_matches[prop_name] < weighted_score:
                    all_matches[prop_name] = weighted_score
                    

        
        # Filter by similarity threshold and sort by score
        # Apply additional filtering for fuzzy matches to prevent false positives
        filtered_matches = []
        for prop, score in sorted(all_matches.items(), key=lambda x: x[1], reverse=True):
            if score >= self.similarity_threshold:
                # Additional check: ensure at least one non-generic word matches
                prop_lower = prop.lower()
                prop_words = set(prop_lower.replace('-', ' ').split())
                # Only exclude words that are standalone, not when they're part of compound words
                generic_words = {'villa', 'house', 'cottage', 'estate', 'manor', 'palace', 'resort'}
                search_specific = {word for word in search_words if word not in generic_words}
                prop_specific = {word for word in prop_words if word not in generic_words}
                
                # Only include if there's a meaningful match beyond generic words
                # For non-existent properties, be very strict
                if search_specific:
                    # Check for exact matches first
                    search_specific_lower = {word.lower() for word in search_specific}
                    prop_specific_lower = {word.lower() for word in prop_specific}
                    exact_matches = search_specific_lower.intersection(prop_specific_lower)
                    
                    # If no exact matches, check for fuzzy matches on individual words
                    fuzzy_word_matches = False
                    if not exact_matches:
                        for search_word in search_specific_lower:
                            for prop_word in prop_specific_lower:
                                # Use fuzzy matching for individual words (85% threshold for spelling variations)
                                word_similarity = fuzz.ratio(search_word, prop_word)
                                if word_similarity >= 85:
                                    fuzzy_word_matches = True
                                    break
                            if fuzzy_word_matches:
                                break
                    
                    # Debug logging for first few properties and when fuzzy matches are found
                    if len(filtered_matches) < 3 or fuzzy_word_matches:
                        logger.info(f"Checking '{prop}': search_specific={search_specific_lower}, prop_specific={prop_specific_lower}, exact_matches={exact_matches}, fuzzy_word_matches={fuzzy_word_matches}")
                    
                    if exact_matches or fuzzy_word_matches:
                        # At least one specific word matches exactly or with high similarity
                        filtered_matches.append(prop)
                else:
                    # If only generic words, require very high similarity (95%+)
                    if score >= 95:
                        filtered_matches.append(prop)
        
        fuzzy_matches = filtered_matches
        
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
        
        # Calculate price range - only include if there are multiple distinct prices
        price_range = None
        if prices:
            unique_prices = list(set(prices))
            if len(unique_prices) > 1:
                price_range = {
                    "min": min(prices),
                    "max": max(prices)
                }
        
        # Generate summary message
        summary = self._generate_summary_range(
            search_term, check_in_date, check_out_date, len(matched_properties), 
            available_count, price_range, prices
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
        price_range: Optional[Dict[str, int]],
        prices: List[int] = None
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
        elif prices and len(prices) > 0:
            # Single price available
            price_text = f"Per-night price is ₹{prices[0]:,}."
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
