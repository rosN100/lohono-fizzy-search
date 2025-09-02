import pandas as pd
from typing import List, Dict, Any, Optional
from rapidfuzz import fuzz, process
import logging
from datetime import datetime
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
    
    def search_properties(self, property_name: str, check_date: str) -> Dict[str, Any]:
        """
        Search for properties using fuzzy matching
        
        Args:
            property_name: Name of the property to search for
            check_date: Date in YYYY-MM-DD format
            
        Returns:
            Dict containing search results
        """
        try:
            logger.info(f"Searching for '{property_name}' on date '{check_date}'")
            if self._data_cache is None:
                raise ValueError("Data not loaded")
            
            # Get all unique property identifiers
            all_property_names = self._data_cache['Identifier'].unique().tolist()
            
            if not all_property_names:
                return self._no_properties_found_response(property_name, check_date)
            
            # Perform fuzzy search
            fuzzy_matches = self._fuzzy_search_properties(property_name, all_property_names)
            
            if not fuzzy_matches:
                return self._no_properties_found_response(property_name, check_date)
            
            # Get availability data for matched properties on the specified date
            property_data = self._get_property_availability(fuzzy_matches, check_date)
            
            # Format response
            return self._format_search_response(
                property_name, check_date, fuzzy_matches, property_data
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
    
    def _get_property_availability(self, property_names: List[str], check_date: str) -> List[Dict[str, Any]]:
        """
        Get availability data for properties on a specific date
        """
        try:
            # Filter data for the specific date and properties
            filtered_data = self._data_cache[
                (self._data_cache['date'] == check_date) & 
                (self._data_cache['Identifier'].isin(property_names))
            ]
            
            # Convert to list of dictionaries
            property_data = []
            for _, row in filtered_data.iterrows():
                property_data.append({
                    'Identifier': row['Identifier'],
                    'listing price': row['listing price'],
                    'status': row['status']
                })
            
            return property_data
            
        except Exception as e:
            logger.error(f"Error fetching property availability: {e}")
            return []
    
    def _format_search_response(
        self, 
        search_term: str, 
        check_date: str, 
        matched_properties: List[str], 
        property_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Format the search response according to the PRD specification
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
                properties_list.append({
                    "name": prop_name,
                    "price": int(prop_data["listing price"]),
                    "status": prop_data["status"]
                })
                prices.append(int(prop_data["listing price"]))
                if prop_data["status"] == "available":
                    available_count += 1
            else:
                # Property exists but no data for this date
                properties_list.append({
                    "name": prop_name,
                    "price": None,
                    "status": "no_data"
                })
        
        # Calculate price range
        price_range = None
        if prices:
            price_range = {
                "min": min(prices),
                "max": max(prices)
            }
        
        # Generate summary message
        summary = self._generate_summary(
            search_term, check_date, len(matched_properties), 
            available_count, price_range
        )
        
        return {
            "found": True,
            "search_term": search_term,
            "check_date": check_date,
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
    
    def _no_properties_found_response(self, search_term: str, check_date: str) -> Dict[str, Any]:
        """
        Generate response when no properties are found
        """
        return {
            "found": False,
            "search_term": search_term,
            "check_date": check_date,
            "total_found": 0,
            "available_count": 0,
            "properties": [],
            "price_range": None,
            "summary": f"No properties found matching '{search_term}'. Try searching for 'Aurelia', 'Siena', or 'Monforte'.",
            "message": f"No properties found matching '{search_term}'. Try searching for 'Aurelia', 'Siena', or 'Monforte'."
        }
