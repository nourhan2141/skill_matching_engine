from slowapi import Limiter
from fastapi import Request
import logging

def get_client_ip(request: Request) -> str:
    """
    Strictly reads the client host provided by ASGI. 
    To protect against X-Forwarded-For spoofing when behind a proxy (like Nginx/AWS), 
    Uvicorn MUST be run with the --proxy-headers flag.
    """
    if not request.client:
        logging.warning("request.client is None — rate limit fallback to 127.0.0.1")
        return "127.0.0.1"
    return request.client.host

limiter = Limiter(key_func=get_client_ip)
