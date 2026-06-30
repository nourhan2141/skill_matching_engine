import os
import json
import asyncio
import logging
import groq
from groq import AsyncGroq
from app.core.config import GROQ_MODEL

client = AsyncGroq(
    api_key=os.environ.get("GROQ_API_KEY")
)

def _clean_keys(obj):
    """Recursively strip whitespace from all dictionary keys."""
    if isinstance(obj, dict):
        return {k.strip(): _clean_keys(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_clean_keys(item) for item in obj]
    return obj

async def generate_json(prompt: str, model_name: str = GROQ_MODEL) -> dict:
    """
    Sends the prompt to the Groq API and strictly expects a JSON object back.
    Includes retry logic with exponential backoff for 429 Rate Limit errors.
    """
    max_retries = 3
    backoff_times = [1, 2, 4]
    response = None

    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant. Always respond with valid JSON only. No markdown, no explanations, no extra text."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.0,  # Keep temperature 0 for deterministic rubric scoring
                max_tokens=4096
            )
            break
        except (groq.RateLimitError, groq.APIConnectionError, groq.APITimeoutError) as e:
            if attempt < max_retries - 1:
                wait_time = backoff_times[attempt]
                logging.debug(f"LLM API error ({type(e).__name__}). Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                logging.exception("Groq API error limit exceeded after all retries.")
                raise e
                
    if response is None:
        raise RuntimeError("Failed to generate response due to unhandled errors during LLM communication.")
    
    content = response.choices[0].message.content
    logging.debug(f"Raw LLM output (first 500 chars): {repr(content[:500])}")
    
    content = content.strip()
    # Strip markdown code fences if the LLM wraps its output in ```json ... ```
    if content.startswith("```"):
        content = content.split("\n", 1)[1]  
        content = content.rsplit("```", 1)[0] 
        content = content.strip()
    try:
        parsed = json.loads(content)
        return _clean_keys(parsed)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from LLM: {str(e)} | Raw output: {content[:1000]}")
