import json
from openai import AsyncOpenAI
from app.config import config

async def is_scammer_data(text: str, extracted_item: str, item_type: str) -> bool:
    client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
    
    prompt = f"""
    Analyze the text message. Determine if the {item_type} '{extracted_item}' belongs to the USER/VICTIM or the SCAMMER.
    Respond in JSON format with a single boolean key "is_scammer_data".
    Return true ONLY if the data belongs to the scammer, is a destination for a payment, or is a malicious link.
    Return false if the data is referenced as belonging to the user/victim (e.g., "your account 1234").
    
    Message: "{text}"
    """
    
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo", # Use a fast/cheap model for this
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=10
        )
        result = json.loads(response.choices[0].message.content)
        return result.get("is_scammer_data", True)
    except Exception:
        return True # Default to True on failure