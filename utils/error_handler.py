from typing import Dict, Any
from models.webhook_models import VapiWebhookResponse, VapiWebhookResult, SearchResult

class ErrorHandler:
    """
    Centralized error handling for webhook responses
    """
    
    def invalid_date_response(self, tool_call_id: str, invalid_date: str) -> dict:
        """
        Generate response for invalid date format
        """
        error_message = f"Invalid date format: {invalid_date}. Please use formats like '2025-09-09', '9th Sept 2025', or 'September 9'."
        
        return {
            "results": [{
                "toolCallId": tool_call_id,
                "result": error_message
            }]
        }
    
    def search_error_response(self, tool_call_id: str, error_message: str) -> dict:
        """
        Generate response for search errors
        """
        error_msg = f"Search error: {error_message}"
        
        return {
            "results": [{
                "toolCallId": tool_call_id,
                "result": error_msg
            }]
        }
    
    def generic_error_response(self, tool_call_id: str, error_message: str) -> dict:
        """
        Generate response for generic errors
        """
        error_msg = f"Error processing request: {error_message}"
        
        return {
            "results": [{
                "toolCallId": tool_call_id,
                "result": error_msg
            }]
        }
