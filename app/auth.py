"""
API Key authentication middleware
"""
from fastapi import Header, HTTPException, status
from app.config import config


async def verify_api_key(x_api_key: str = Header(..., description="API Key for authentication")) -> str:
    """
    Verify the API key from request headers
    
    Args:
        x_api_key: API key from x-api-key header
        
    Returns:
        The validated API key
        
    Raises:
        HTTPException: If API key is invalid or missing
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if x_api_key != config.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return x_api_key
