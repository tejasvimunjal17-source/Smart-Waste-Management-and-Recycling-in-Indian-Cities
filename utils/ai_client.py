"""
utils/ai_client.py
---------------------
Thin wrapper around the OpenRouter Chat Completions API
(https://openrouter.ai/docs). Centralizes:
  - plain chat completion
  - streaming chat completion (for Prakriti AI Connect)
  - vision-based waste image classification
  - structured JSON generation (priority, complaint text, insights)

No API key is ever hardcoded — it's read from config.settings, which
loads it from .env. If the key is missing/placeholder, functions
degrade gracefully to a clearly-labeled mock response instead of
crashing the app.
"""
import json
import base64
import logging
import requests

from config import settings

logger = logging.getLogger("ecovision.ai")

TIMEOUT = 60


def _headers():
    return {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": settings.OPENROUTER_SITE_URL,
        "X-Title": settings.OPENROUTER_APP_NAME,
    }


def _endpoint():
    return f"{settings.OPENROUTER_BASE_URL.rstrip('/')}/chat/completions"


def chat_completion(messages, model=None, temperature=0.4, max_tokens=800, json_mode=False):
    """
    Non-streaming completion. `messages` follows the OpenAI/OpenRouter
    format: [{"role": "system"|"user"|"assistant", "content": ...}]
    """
    if not settings.is_ai_configured():
        return _mock_response(messages)

    payload = {
        "model": model or settings.OPENROUTER_TEXT_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    try:
        resp = requests.post(_endpoint(), headers=_headers(), json=payload, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        logger.error("OpenRouter request failed: %s", e)
        return f"⚠️ AI service temporarily unavailable ({e}). Please try again shortly."
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        logger.error("Unexpected OpenRouter response: %s", e)
        return "⚠️ AI service returned an unexpected response. Please try again."


def stream_chat_completion(messages, model=None, temperature=0.5, max_tokens=800):
    """Generator yielding text chunks — used for the streaming chatbot UI."""
    if not settings.is_ai_configured():
        yield _mock_response(messages)
        return

    payload = {
        "model": model or settings.OPENROUTER_TEXT_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }
    try:
        with requests.post(_endpoint(), headers=_headers(), json=payload,
                            timeout=TIMEOUT, stream=True) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line:
                    continue
                line = line.decode("utf-8").strip()
                if not line.startswith("data:"):
                    continue
                data_str = line[len("data:"):].strip()
                if data_str == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    delta = chunk["choices"][0]["delta"].get("content")
                    if delta:
                        yield delta
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
    except requests.exceptions.RequestException as e:
        logger.error("OpenRouter streaming failed: %s", e)
        yield f"\n\n⚠️ Connection issue reaching the AI service ({e})."


def classify_waste_image(image_bytes: bytes, mime_type: str = "image/jpeg"):
    """
    Sends an image to a vision-capable OpenRouter model and asks for a
    structured JSON classification. Returns a dict with keys:
    category, confidence, recycling_method, disposal_guide, environmental_impact
    """
    categories = ", ".join(settings.WASTE_CATEGORIES)

    if not settings.is_ai_configured():
        return _mock_classification()

    b64 = base64.b64encode(image_bytes).decode()
    data_url = f"data:{mime_type};base64,{b64}"

    system_prompt = (
        "You are an expert municipal waste-classification AI for Indian cities. "
        f"Classify the uploaded image into exactly one of these categories: {categories}. "
        "Respond ONLY with a valid JSON object with keys: "
        "category (string, one of the allowed categories), "
        "confidence (number 0-100), "
        "recycling_method (short string), "
        "disposal_guide (2-3 sentences, India-specific, mention MCG guidelines where relevant), "
        "environmental_impact (1-2 sentences). No markdown, no extra text."
    )

    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Classify this waste image."},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
        ],
        "temperature": 0.2,
        "max_tokens": 400,
    }

    try:
        resp = requests.post(_endpoint(), headers=_headers(), json=payload, timeout=TIMEOUT)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        content = content.strip().strip("`").replace("json\n", "").strip()
        return json.loads(content)
    except Exception as e:
        logger.error("Image classification failed: %s", e)
        result = _mock_classification()
        result["note"] = f"AI classification unavailable ({e}); showing fallback estimate."
        return result


def generate_complaint_description(category, ward, raw_notes):
    prompt = (
        f"Write a concise, professional municipal waste complaint description "
        f"(3-4 sentences) for a citizen report in India. "
        f"Category: {category}. Ward: {ward or 'not specified'}. "
        f"Citizen's raw notes: '{raw_notes or 'none provided'}'. "
        "Be factual, polite, and actionable — suitable for a municipal officer to read."
    )
    return chat_completion(
        [{"role": "system", "content": "You write clear municipal complaint descriptions."},
         {"role": "user", "content": prompt}],
        temperature=0.4, max_tokens=200,
    )


def predict_priority(category, description):
    prompt = (
        f"Given this municipal waste complaint, classify its urgency as exactly one word: "
        f"High, Medium, or Low.\nCategory: {category}\nDescription: {description}\n"
        "Consider: Biomedical and E-Waste hazards, large accumulation, health risk, or road/drain "
        "blockage = High. Routine uncollected household waste = Medium. Minor/cosmetic issues = Low. "
        "Respond with ONLY the single word."
    )
    result = chat_completion(
        [{"role": "system", "content": "You triage municipal complaints by urgency."},
         {"role": "user", "content": prompt}],
        temperature=0.1, max_tokens=5,
    )
    for level in settings.PRIORITY_LEVELS:
        if level.lower() in result.lower():
            return level
    return "Medium"


def generate_awareness_content(topic, content_type="eco tips"):
    prompt = (
        f"Generate {content_type} about '{topic}' for an Indian municipal sustainability "
        "awareness campaign. Keep it practical, locally relevant, and easy to share on social "
        "media or a poster. Use short bullet points."
    )
    return chat_completion(
        [{"role": "system", "content": "You are a creative sustainability communications expert for Indian cities."},
         {"role": "user", "content": prompt}],
        temperature=0.7, max_tokens=500,
    )


def generate_resume_content(kind, profile_details):
    prompts = {
        "resume": "Write a clean, ATS-friendly resume in Markdown based on these details:",
        "cover_letter": "Write a professional cover letter (max 300 words) based on these details:",
        "portfolio": "Write a short professional portfolio 'About Me' summary based on these details:",
        "linkedin": "Write a compelling LinkedIn 'About' summary (max 150 words) based on these details:",
    }
    prompt = f"{prompts.get(kind, prompts['resume'])}\n\n{profile_details}"
    return chat_completion(
        [{"role": "system", "content": "You are an expert career coach and resume writer."},
         {"role": "user", "content": prompt}],
        temperature=0.5, max_tokens=900,
    )


def _mock_classification():
    return {
        "category": "Mixed",
        "confidence": 0,
        "recycling_method": "Segregate before disposal",
        "disposal_guide": "AI classification is not configured yet. Add a valid OPENROUTER_API_KEY "
                           "to your .env file to enable real-time image classification.",
        "environmental_impact": "Unclassified mixed waste increases landfill burden and recycling costs.",
        "mock": True,
    }


def _mock_response(messages):
    return ("🌿 Prakriti AI Connect is running in demo mode because no OpenRouter API key is "
            "configured yet. Add OPENROUTER_API_KEY to your .env file to enable real AI responses.")
