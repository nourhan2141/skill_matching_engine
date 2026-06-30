import os
from dotenv import load_dotenv

load_dotenv()

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.responses import RedirectResponse
from app.api.routes import match
from app.api.auth import verify_api_key
from app.core.limiter import limiter
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup checks
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key or groq_api_key == "your_groq_api_key_here":
        raise RuntimeError("GROQ_API_KEY environment variable is missing or set to the placeholder string. Please configure it before starting the application.")
        
    app_api_key = os.getenv("APP_API_KEY")
    if not app_api_key or app_api_key == "your_app_api_key_here":
        raise RuntimeError("APP_API_KEY environment variable is missing or set to the placeholder string. Please configure it before starting the application.")
    yield
    # Shutdown actions (if any are needed later)

app = FastAPI(
    title="AI Career Coach API",
    description="Match CVs to Job Descriptions using Groq and Llama 3.1 8B",
    version="1.0.0",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(match.router, dependencies=[Depends(verify_api_key)])

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")
