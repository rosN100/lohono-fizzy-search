from typing import Dict, Any
from models.webhook_models import VapiWebhookResponse, VapiWebhookResult, SearchResult

class ErrorHandler:
    """
    Centralized error handling for webhook responses
    """
    
    def invalid_date_response(self, tool_call_id: str, invalid_date: str) -> VapiWebhookResponse:
        """
        Generate response for invalid date format
        """
        result = SearchResult(
            found=False,
            search_term="",
            check_date=invalid_date,
            total_found=0,
            available_count=0,
            properties=[],
            summary=f"Invalid date format: {invalid_date}. Please use formats like '2025-09-09', '9th Sept 2025', or 'September 9'.",
            message=f"Invalid date format: {invalid_date}. Please use formats like '2025-09-09', '9th Sept 2025', or 'September 9'."
        )
        
        return VapiWebhookResponse(
            results=[VapiWebhookResult(toolCallId=tool_call_id, result=result)]
        )
    
    def search_error_response(self, tool_call_id: str, error_message: str) -> VapiWebhookResponse:
        """
        Generate response for search errors
        """
        result = SearchResult(
            found=False,
            search_term="",
            check_date="",
            total_found=0,
            available_count=0,
            properties=[],
            summary=f"Search error: {error_message}",
            message=f"Search error: {error_message}"
        )
        
        return VapiWebhookResponse(
            results=[VapiWebhookResult(toolCallId=tool_call_id, result=result)]
        )
    
    def generic_error_response(self, tool_call_id: str, error_message: str) -> VapiWebhookResponse:
        """
        Generate response for generic errors
        """
        result = SearchResult(
            found=False,
            search_term="",
            check_date="",
            total_found=0,
            available_count=0,
            properties=[],
            summary=f"Error processing request: {error_message}",
            message=f"Error processing request: {error_message}"
        )
        
        return VapiWebhookResponse(
            results=[VapiWebhookResult(toolCallId=tool_call_id, result=result)]
        )
