from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import json
from datetime import datetime

from services.property_search import PropertySearchService
from services.date_parser import DateParserService
from models.webhook_models import VapiWebhookRequest, VapiWebhookResponse
from utils.error_handler import ErrorHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Property Fuzzy Search API",
    description="Fuzzy search API for property availability with Vapi integration",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
property_search_service = PropertySearchService()
date_parser_service = DateParserService()
error_handler = ErrorHandler()

@app.get("/")
async def root():
    return {"message": "Property Fuzzy Search API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "property-search-api"}

@app.get("/debug/date")
async def debug_date(date_input: str):
    """Debug endpoint to test date parsing"""
    try:
        parsed_date = date_parser_service.parse_date(date_input)
        return {
            "input": date_input,
            "parsed": parsed_date,
            "is_valid_format": date_parser_service.is_valid_date_format(date_input)
        }
    except Exception as e:
        return {"error": str(e), "input": date_input}

@app.post("/api/v1/webhook/vapi")
async def vapi_webhook(request: VapiWebhookRequest):
    """
    Main webhook endpoint for Vapi voice agent integration
    """
    try:
        logger.info(f"Received webhook request: {request}")
        
        # Extract parameters
        tool_call_id = request.toolCallId
        property_name = request.parameters.property_name
        check_date_input = request.parameters.check_date
        
        # Parse the date (handles natural language)
        try:
            check_date = date_parser_service.parse_date(check_date_input)
            logger.info(f"Parsed date '{check_date_input}' to '{check_date}'")
        except Exception as e:
            logger.error(f"Date parsing error: {e}")
            return error_handler.invalid_date_response(tool_call_id, check_date_input)
        
        # Perform fuzzy search
        try:
            search_results = property_search_service.search_properties(
                property_name=property_name,
                check_date=check_date
            )
            logger.info(f"Search completed: {search_results['total_found']} properties found")
            
            # Format response for Vapi (result must be a string according to Vapi docs)
            # Try a simpler response format that Vapi might handle better
            response = {
                "results": [{
                    "toolCallId": tool_call_id,
                    "result": search_results['summary']
                }]
            }
            
            logger.info(f"Returning response for toolCallId: {tool_call_id}")
            logger.info(f"Response structure: {type(response)}")
            
            # Return with explicit headers for Vapi
            return Response(
                content=json.dumps(response),
                media_type="application/json",
                headers={
                    "Content-Type": "application/json",
                    "Cache-Control": "no-cache"
                }
            )
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return error_handler.search_error_response(tool_call_id, str(e))
            
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return error_handler.generic_error_response(request.toolCallId, str(e))

@app.post("/api/v1/webhook/vapi-simple")
async def vapi_webhook_simple(request: VapiWebhookRequest):
    """
    Alternative webhook endpoint with simpler response format for Vapi
    """
    try:
        logger.info(f"Received simple webhook request: {request}")
        
        # Extract parameters
        tool_call_id = request.toolCallId
        property_name = request.parameters.property_name
        check_date_input = request.parameters.check_date
        
        # Parse the date (handles natural language)
        try:
            check_date = date_parser_service.parse_date(check_date_input)
            logger.info(f"Parsed date '{check_date_input}' to '{check_date}'")
        except Exception as e:
            logger.error(f"Date parsing error: {e}")
            return {"error": f"Invalid date format: {check_date_input}"}
        
        # Perform fuzzy search
        try:
            search_results = property_search_service.search_properties(
                property_name=property_name,
                check_date=check_date
            )
            logger.info(f"Search completed: {search_results['total_found']} properties found")
            
            # Return simple response format
            return {
                "toolCallId": tool_call_id,
                "found": search_results['found'],
                "search_term": search_results['search_term'],
                "check_date": search_results['check_date'],
                "total_found": search_results['total_found'],
                "available_count": search_results['available_count'],
                "properties": search_results['properties'],
                "price_range": search_results['price_range'],
                "summary": search_results['summary']
            }
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return {"error": f"Search failed: {str(e)}"}
            
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return {"error": f"Processing failed: {str(e)}"}

@app.get("/api/v1/properties/search")
async def search_properties(
    property_name: str,
    check_date: str,
    limit: int = 10
):
    """
    Direct search endpoint for testing
    """
    try:
        # Parse date
        parsed_date = date_parser_service.parse_date(check_date)
        logger.info(f"Date parsed: '{check_date}' -> '{parsed_date}'")
        
        # Search properties
        results = property_search_service.search_properties(
            property_name=property_name,
            check_date=parsed_date
        )
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)