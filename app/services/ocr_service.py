import base64
from app.core.llm import client
from app.core.config import GROQ_VISION_MODEL

# Groq vision model that supports image inputs


async def extract_text_from_image(image_bytes: bytes, content_type: str = "image/png") -> str:
    """
    Uses Groq's vision model to perform OCR on an image and extract all text.
    Supports PNG, JPEG, WEBP, and other common image formats.

    Args:
        image_bytes: Raw bytes of the image file.
        content_type: MIME type of the image (e.g. 'image/png', 'image/jpeg').

    Returns:
        The extracted text from the image.
    """
    # Encode image to base64 data URL
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    data_url = f"data:{content_type};base64,{b64_image}"

    response = await client.chat.completions.create(
        model=GROQ_VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "You are an OCR assistant. Extract ALL text from this image exactly as it appears. "
                            "Preserve the structure, bullet points, headings, and formatting as closely as possible. "
                            "Do not add any explanations, comments, or summaries. Only output the raw extracted text."
                        )
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": data_url
                        }
                    }
                ]
            }
        ],
        temperature=0.0,
        max_tokens=4096
    )

    return response.choices[0].message.content.strip()
