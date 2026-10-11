"""Reliable LLM calling for OpportunityLens.
 
Order of attempts:
1. Cache   - same prompt seen before -> reuse the saved answer (instant).
2. Gemini  - transient server errors (5xx) are retried briefly; client errors
             (4xx: bad model name, quota, bad request) are NOT retried.
3. Groq    - free backup (open models) if Gemini cannot answer.
 
The cache key is a hash of the FULL prompt (instructions + retrieved context +
opportunity), so changing the prompt automatically invalidates old answers.
A result is saved only after the parser accepted it.
"""
import hashlib
import json
import os
import time
from pathlib import Path
 
CACHE_FILE = Path("cache.json")
 
GEMINI_MODELS = ["gemini-3.7-flash", "gemini-3.8-flash"]  # models that worked for you
# Groq retires models from time to time, so several are tried in order.
# Put GROQ_MODEL=... in .env to try your own choice first.
GROQ_MODELS = [m for m in [os.getenv("GROQ_MODEL"), "openai/gpt-oss-120b", "openai/gpt-oss-20b"] if m]
 
 
def _load_cache() -> dict:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}
 
 
def _save_cache(cache: dict) -> None:
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
 
 
def _error_code(e: Exception):
    code = getattr(e, "code", None) or getattr(e, "status_code", None)
    return code if isinstance(code, int) else None
 
 
def _call_gemini(client, prompt: str) -> str:
    last_error = None
    for model in GEMINI_MODELS:
        for attempt in range(2):
            try:
                print(f"Trying Gemini: {model} (attempt {attempt + 1}/2)")
                return client.models.generate_content(model=model, contents=prompt).text
            except Exception as e:
                last_error = e
                code = _error_code(e)
                print(f"  Gemini error {code}: {str(e)[:160]}")
                if code is not None and 400 <= code < 500:
                    # Client error: retrying the same request will not help.
                    # 429 (quota) and 404 (bad model) -> stop trying Gemini entirely.
                    if code in (429, 403):
                        raise
                    break  # try the next Gemini model
                if attempt == 0:
                    time.sleep(3)
    raise last_error
 
 
def _call_groq(prompt: str) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("Backup unavailable: GROQ_API_KEY is missing from .env")
    from groq import Groq
 
    client = Groq(api_key=api_key)
    last_error = None
    for model in GROQ_MODELS:
        try:
            print(f"Trying Groq: {model}")
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=4000,
            )
            return response.choices[0].message.content
        except Exception as e:
            last_error = e
            print(f"  Groq {model} failed: {str(e)[:160]}")
    raise last_error
 
 
def generate_structured(client, prompt: str, parser, cache_key_text: str = ""):
    """Return a parsed Pydantic object using cache -> Gemini -> Groq."""
    key = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    cache = _load_cache()
 
    if key in cache:
        try:
            print("Using cached result.")
            return parser.parse(cache[key])
        except Exception:
            pass  # bad cache entry, recompute
 
    try:
        raw = _call_gemini(client, prompt)
        result = parser.parse(raw)
    except Exception as gemini_error:
        print(f"Gemini path failed ({type(gemini_error).__name__}). Switching to Groq.")
        raw = _call_groq(prompt)
        result = parser.parse(raw)
 
    cache[key] = raw
    _save_cache(cache)
    return result
 
