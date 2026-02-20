"""
Image handler service - detects image data in message.text and converts it to
a plain-text description via the OpenAI Vision API.

Supported input formats for message.text:
  1. Data URI  : "data:image/png;base64,<b64data>"
  2. Raw base64: a long base64 string whose decoded bytes start with a known image magic number

No changes to the Message model or request schema are required.
"""
import base64
import re
from openai import AsyncOpenAI
from app.config import config

VISION_MODEL = "gpt-4o"

_DESCRIBE_PROMPT = (
    "You are a forensic analyst reviewing an image sent by a potential scammer. "
    "Transcribe ALL visible text in the image exactly as written. "
    "Also note any logos, branding, QR codes, URLs, phone numbers, account numbers, "
    "UPI IDs, or other suspicious elements. Be thorough and literal."
)

# Magic bytes for common image formats
_IMAGE_MAGIC = {
    b"\x89PNG": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
    b"GIF8": "image/gif",
    b"RIFF": "image/webp",   # RIFF....WEBP
    b"BM": "image/bmp",
    b"\x00\x00\x01\x00": "image/x-icon",  # ICO
    b"\x00\x00\x02\x00": "image/x-icon",  # CUR
}

_DATA_URI_RE = re.compile(
    r'^data:(image/[a-zA-Z0-9.+_-]+);base64,([A-Za-z0-9+/=]+)$',
    re.DOTALL
)


def _detect_image_in_text(text: str):
    """
    Check whether text contains image data.

    Returns (data_url, media_type) if image detected, else (None, None).
    """
    stripped = text.strip()

    # Case 1: data URI
    m = _DATA_URI_RE.match(stripped)
    if m:
        media_type = m.group(1)
        b64_data = m.group(2)
        return f"data:{media_type};base64,{b64_data}", media_type

    # Case 2: raw base64 string (no spaces, long enough to be an image)
    if len(stripped) > 100 and re.match(r'^[A-Za-z0-9+/=]+$', stripped):
        try:
            raw = base64.b64decode(stripped + '==')  # pad safely
            for magic, mime in _IMAGE_MAGIC.items():
                if raw[:len(magic)] == magic:
                    return f"data:{mime};base64,{stripped}", mime
        except Exception:
            pass

    return None, None


class ImageHandler:
    """Detect and convert image data in message.text to a plain-text description."""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

    def is_image(self, text: str) -> bool:
        """Return True if text appears to contain image data."""
        data_url, _ = _detect_image_in_text(text)
        return data_url is not None

    async def text_to_description(self, text: str) -> str:
        """
        If text contains image data, return a Vision-API description.
        Otherwise return the original text unchanged.

        Args:
            text: The raw message.text value.

        Returns:
            Plain-text description of the image, or the original text.
        """
        data_url, media_type = _detect_image_in_text(text)
        if data_url is None:
            return text

        try:
            response = await self.client.chat.completions.create(
                model=VISION_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": _DESCRIBE_PROMPT},
                            {
                                "type": "image_url",
                                "image_url": {"url": data_url, "detail": "high"},
                            },
                        ],
                    }
                ],
                max_tokens=500,
            )
            description = response.choices[0].message.content.strip()
            return f"[Image content]: {description}"

        except Exception as e:
            print(f"[ImageHandler] Vision API error: {e}")
            return "[Image content]: (Could not process image)"
