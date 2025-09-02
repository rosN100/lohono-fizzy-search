import dateparser
from datetime import datetime, date
from typing import Union
import logging

logger = logging.getLogger(__name__)

class DateParserService:
    """
    Service for parsing various date formats including natural language
    """
    
    def __init__(self):
        # Configure dateparser settings
        self.settings = {
            'PREFER_DAY_OF_MONTH': 'first',
            'PREFER_DATES_FROM': 'future',
            'RELATIVE_BASE': datetime.now(),
            'DATE_ORDER': 'YMD',  # Year-Month-Day (ISO format)
            'STRICT_PARSING': False,
        }
    
    def parse_date(self, date_input: str) -> str:
        """
        Parse various date formats to YYYY-MM-DD
        
        Args:
            date_input: Date in various formats (natural language, ISO, etc.)
            
        Returns:
            str: Date in YYYY-MM-DD format
            
        Raises:
            ValueError: If date cannot be parsed
        """
        if not date_input or not date_input.strip():
            raise ValueError("Empty date input")
        
        date_input = date_input.strip()
        logger.info(f"Parsing date input: '{date_input}'")
        
        # First, try to parse as ISO format (YYYY-MM-DD)
        if self.is_valid_date_format(date_input):
            logger.info(f"Date '{date_input}' is already in ISO format, returning as-is")
            return date_input
        
        # Also check for common ISO-like patterns
        if len(date_input) == 10 and date_input.count('-') == 2:
            try:
                # Try to parse as YYYY-MM-DD
                parts = date_input.split('-')
                if len(parts) == 3 and len(parts[0]) == 4 and len(parts[1]) == 2 and len(parts[2]) == 2:
                    datetime.strptime(date_input, "%Y-%m-%d")
                    logger.info(f"Date '{date_input}' matches ISO pattern, returning as-is")
                    return date_input
            except ValueError:
                pass
        
        # Additional check: if it looks like YYYY-MM-DD, don't use dateparser
        if len(date_input) == 10 and date_input.count('-') == 2:
            try:
                # Force parse as YYYY-MM-DD
                parsed = datetime.strptime(date_input, "%Y-%m-%d")
                logger.info(f"Date '{date_input}' forced as ISO format, returning as-is")
                return date_input
            except ValueError:
                pass
        
        # Try parsing with dateparser (handles natural language)
        try:
            parsed_date = dateparser.parse(
                date_input, 
                settings=self.settings
            )
            
            if parsed_date is None:
                raise ValueError(f"Could not parse date: {date_input}")
            
            # Convert to date object and format
            if isinstance(parsed_date, datetime):
                parsed_date = parsed_date.date()
            
            # Validate the date is reasonable (not too far in past/future)
            today = date.today()
            if parsed_date < today:
                logger.warning(f"Parsed date {parsed_date} is in the past")
            
            if parsed_date.year > 2030:
                raise ValueError(f"Date {parsed_date} is too far in the future")
            
            return parsed_date.strftime("%Y-%m-%d")
            
        except Exception as e:
            logger.error(f"Date parsing failed for '{date_input}': {e}")
            raise ValueError(f"Invalid date format: {date_input}. Please use formats like '2025-09-09', '9th Sept 2025', or 'September 9'")
    
    def is_valid_date_format(self, date_str: str) -> bool:
        """
        Check if a date string is in valid YYYY-MM-DD format
        """
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False
