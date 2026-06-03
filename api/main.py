"""
Malaysia Postcodes REST API
FastAPI application with authentication and rate limiting.
"""

import os
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from api import __version__
from api.models import (
    APIInfo, HealthCheck, State, City, StateListItem,
    PostcodeInfo, SearchResult, ErrorResponse
)
from api.data_loader import load_postcode_data, get_postcode_data
from api.auth import load_api_keys, verify_api_key, get_api_key_identifier, get_api_key_manager
from api.rate_limiter import check_api_rate_limit, check_ip_rate_limit_only


# Rate limiting setup
def rate_limit_key_func(request: Request) -> str:
    """Custom key function for rate limiting by API key."""
    api_key = request.headers.get("X-API-Key", "")
    if api_key:
        return get_api_key_identifier(api_key)
    # Fall back to IP address for public endpoints
    return get_remote_address(request)


# Get rate limit from environment variable (default: 100/minute)
RATE_LIMIT = os.getenv("RATE_LIMIT", "100/minute")

limiter = Limiter(
    key_func=rate_limit_key_func,
    default_limits=[RATE_LIMIT]
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Startup: Load data
    print("Starting Malaysia Postcodes API...")
    
    # Load postcode data
    data_file = os.getenv("DATA_FILE", "all.json")
    load_postcode_data(data_file)
    print(f"✓ Loaded postcode data from {data_file}")
    
    # Load API keys
    keys_file = os.getenv("API_KEYS_FILE", "api_keys.json")
    load_api_keys(keys_file)
    print(f"✓ Loaded API keys from {keys_file}")
    
    print("✓ API is ready!")
    
    yield
    
    # Shutdown
    print("Shutting down Malaysia Postcodes API...")


# Create FastAPI app
app = FastAPI(
    title="Malaysia Postcodes API",
    description="REST API for Malaysian postcode lookup with authentication and rate limiting",
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Middleware to remove server header
@app.middleware("http")
async def remove_server_header(request: Request, call_next):
    """Remove server identification header for security."""
    response = await call_next(request)
    response.headers["Server"] = ""
    return response

# CORS middleware
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


# Public endpoints (no authentication required)

@app.get(
    "/",
    response_model=APIInfo,
    tags=["Info"],
    summary="API Information",
    description="Get basic information about the API"
)
async def root(request: Request):
    """Get API information."""
    # Apply IP rate limiting to public endpoint
    await check_ip_rate_limit_only(request)
    
    return APIInfo(
        name="Malaysia Postcodes API",
        version=__version__,
        description="REST API for Malaysian postcode lookup with authentication and rate limiting",
        documentation=f"{request.url}docs"
    )


@app.get(
    "/health",
    response_model=HealthCheck,
    tags=["Info"],
    summary="Health Check",
    description="Check API health and data status"
)
async def health_check(request: Request):
    """Health check endpoint."""
    # Apply IP rate limiting to public endpoint
    await check_ip_rate_limit_only(request)
    
    data = get_postcode_data()
    return HealthCheck(
        status="healthy",
        data_loaded=True,
        total_states=data.get_total_states(),
        total_postcodes=data.get_total_postcodes()
    )


# Protected endpoints (require API key and rate limited)

@app.get(
    "/states",
    response_model=List[StateListItem],
    tags=["States"],
    summary="List All States",
    description="Get a list of all Malaysian states with summary information. Requires API key.",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized - Invalid or missing API key"},
        429: {"model": ErrorResponse, "description": "Too Many Requests - Rate limit exceeded"}
    }
)
async def list_states(
    request: Request,
    api_key: Optional[str] = Depends(verify_api_key)
):
    """List all states with summary information."""
    # Check rate limit for this specific API key
    await check_api_rate_limit(api_key, request)
    
    data = get_postcode_data()
    return data.get_all_states()


@app.get(
    "/states/{state_name}",
    response_model=State,
    tags=["States"],
    summary="Get State Details",
    description="Get detailed information about a specific state including all cities and postcodes. Requires API key.",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized - Invalid or missing API key"},
        404: {"model": ErrorResponse, "description": "State not found"},
        429: {"model": ErrorResponse, "description": "Too Many Requests - Rate limit exceeded"}
    }
)
async def get_state(
    state_name: str,
    request: Request,
    api_key: Optional[str] = Depends(verify_api_key)
):
    """Get state details by name."""
    # Check rate limit for this specific API key
    await check_api_rate_limit(api_key, request)
    
    data = get_postcode_data()
    state = data.get_state(state_name)
    
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"State '{state_name}' not found"
        )
    
    return state


@app.get(
    "/states/{state_name}/cities",
    response_model=List[City],
    tags=["Cities"],
    summary="List Cities in State",
    description="Get all cities in a specific state. Requires API key.",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized - Invalid or missing API key"},
        404: {"model": ErrorResponse, "description": "State not found"},
        429: {"model": ErrorResponse, "description": "Too Many Requests - Rate limit exceeded"}
    }
)
async def list_cities_in_state(
    state_name: str,
    request: Request,
    api_key: Optional[str] = Depends(verify_api_key)
):
    """List all cities in a state."""
    # Check rate limit for this specific API key
    await check_api_rate_limit(api_key, request)
    
    data = get_postcode_data()
    cities = data.get_cities_in_state(state_name)
    
    if cities is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"State '{state_name}' not found"
        )
    
    return cities


@app.get(
    "/states/{state_name}/cities/{city_name}",
    response_model=City,
    tags=["Cities"],
    summary="Get City Details",
    description="Get details of a specific city in a state. Requires API key.",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized - Invalid or missing API key"},
        404: {"model": ErrorResponse, "description": "State or city not found"},
        429: {"model": ErrorResponse, "description": "Too Many Requests - Rate limit exceeded"}
    }
)
async def get_city(
    state_name: str,
    city_name: str,
    request: Request,
    api_key: Optional[str] = Depends(verify_api_key)
):
    """Get city details."""
    # Check rate limit for this specific API key
    await check_api_rate_limit(api_key, request)
    
    data = get_postcode_data()
    city = data.get_city_in_state(state_name, city_name)
    
    if not city:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"City '{city_name}' not found in state '{state_name}'"
        )
    
    return city


@app.get(
    "/postcodes/{postcode}",
    response_model=PostcodeInfo,
    tags=["Postcodes"],
    summary="Lookup Postcode",
    description="Reverse lookup: find state and city for a given postcode. Requires API key.",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized - Invalid or missing API key"},
        404: {"model": ErrorResponse, "description": "Postcode not found"},
        429: {"model": ErrorResponse, "description": "Too Many Requests - Rate limit exceeded"}
    }
)
async def lookup_postcode(
    postcode: str,
    request: Request,
    api_key: Optional[str] = Depends(verify_api_key)
):
    """Lookup location by postcode."""
    # Check rate limit for this specific API key
    await check_api_rate_limit(api_key, request)
    
    data = get_postcode_data()
    result = data.lookup_postcode(postcode)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Postcode '{postcode}' not found"
        )
    
    state_name, city_name = result
    return PostcodeInfo(
        postcode=postcode,
        city=city_name,
        state=state_name
    )


@app.get(
    "/search",
    response_model=List[SearchResult],
    tags=["Search"],
    summary="Search States and Cities",
    description="Search for states or cities by name (case-insensitive substring match). Requires API key.",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized - Invalid or missing API key"},
        429: {"model": ErrorResponse, "description": "Too Many Requests - Rate limit exceeded"}
    }
)
async def search(
    q: str,
    request: Request,
    api_key: Optional[str] = Depends(verify_api_key)
):
    """Search for states or cities."""
    # Check rate limit for this specific API key
    await check_api_rate_limit(api_key, request)
    
    if not q or len(q.strip()) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Search query must be at least 2 characters"
        )
    
    data = get_postcode_data()
    results = data.search(q)
    
    return [SearchResult(**result) for result in results]


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred"
        }
    )
