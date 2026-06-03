"""
Data models for API responses using Pydantic.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class PostcodeInfo(BaseModel):
    """Information about a postcode lookup."""
    postcode: str = Field(..., description="The postcode")
    city: str = Field(..., description="City name")
    state: str = Field(..., description="State name")


class City(BaseModel):
    """City with its postcodes."""
    name: str = Field(..., description="City name")
    postcode: List[str] = Field(..., description="List of postcodes for this city")


class State(BaseModel):
    """State with its cities."""
    name: str = Field(..., description="State name")
    city: List[City] = Field(..., description="List of cities in this state")


class StateListItem(BaseModel):
    """Simplified state info for listing."""
    name: str = Field(..., description="State name")
    city_count: int = Field(..., description="Number of cities in this state")
    postcode_count: int = Field(..., description="Number of postcodes in this state")


class SearchResult(BaseModel):
    """Search result item."""
    type: str = Field(..., description="Type of result: 'state' or 'city'")
    name: str = Field(..., description="Name of the state or city")
    state: Optional[str] = Field(None, description="State name (for city results)")
    postcode_count: int = Field(..., description="Number of postcodes")


class APIInfo(BaseModel):
    """API information."""
    name: str = Field(..., description="API name")
    version: str = Field(..., description="API version")
    description: str = Field(..., description="API description")
    documentation: str = Field(..., description="Link to interactive documentation")


class HealthCheck(BaseModel):
    """Health check response."""
    status: str = Field(..., description="API status")
    data_loaded: bool = Field(..., description="Whether postcode data is loaded")
    total_states: int = Field(..., description="Total number of states")
    total_postcodes: int = Field(..., description="Total number of postcodes")


class ErrorResponse(BaseModel):
    """Error response."""
    error: str = Field(..., description="Error type")
    detail: str = Field(..., description="Error details")
