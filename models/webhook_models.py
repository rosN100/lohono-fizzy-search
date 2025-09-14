from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class VapiParameters(BaseModel):
    property_name: str
    check_in_date: str
    check_out_date: str

class VapiWebhookRequest(BaseModel):
    toolCallId: str
    parameters: VapiParameters

class PropertyResult(BaseModel):
    name: str
    availability: str
    per_night_price: Optional[int]

class PriceRange(BaseModel):
    min: int
    max: int

class SearchResult(BaseModel):
    found: bool
    search_term: str
    check_in_date: str
    check_out_date: str
    total_found: int
    available_count: int
    properties: List[PropertyResult]
    price_range: Optional[PriceRange] = None
    summary: str
    message: Optional[str] = None

class VapiWebhookResult(BaseModel):
    toolCallId: str
    result: str  # Vapi expects result to be a string according to their docs

class VapiWebhookResponse(BaseModel):
    results: List[VapiWebhookResult]