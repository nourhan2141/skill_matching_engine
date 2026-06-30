from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
import os

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(api_key: str = Security(api_key_header)):
    expected_api_key = os.getenv("APP_API_KEY")
    if not expected_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: APP_API_KEY is not set in the environment."
        )
    if not api_key or api_key != expected_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate API key. Please provide a valid X-API-Key header."
        )
    return api_key
