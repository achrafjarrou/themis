from __future__ import annotations
import os, instructor, asyncio
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI
from loguru import logger

# Charger .env explicitement depuis la racine du projet
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

_KEYS = [k for k in [
    os.getenv("GROQ_API_KEY", ""),
    os.getenv("GROQ_API_KEY_2", ""),
] if k.strip()]

if not _KEYS:
    raise RuntimeError("[LLM] Aucune cle GROQ trouvee dans .env — verifiez GROQ_API_KEY")

_key_index = 0

def _make_clients(key: str):
    raw = AsyncOpenAI(
        api_key=key,
        base_url="https://api.groq.com/openai/v1",
    )
    cli = instructor.from_openai(raw)
    return raw, cli

_raw, client = _make_clients(_KEYS[0])
logger.info(f"[LLM] Groq initialise avec {len(_KEYS)} cle(s)")

def rotate_key():
    global _key_index, _raw, client
    _key_index = (_key_index + 1) % len(_KEYS)
    _raw, client = _make_clients(_KEYS[_key_index])
    logger.warning(f"[LLM] TPD reached — switched to key {_key_index + 1}")

async def chat_with_retry(messages, model="llama-3.1-8b-instant", max_tokens=1024, retries=3):
    last_exc = None
    attempts = retries * len(_KEYS)
    for attempt in range(attempts):
        try:
            resp = await _raw.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content
        except Exception as e:
            last_exc = e
            err = str(e)
            if "429" in err and ("TPD" in err or "tokens per day" in err.lower()):
                rotate_key()
                await asyncio.sleep(2)
            elif "429" in err:
                # TPM — attendre selon le message Groq
                import re as _re
                wait = 5.0
                m = _re.search(r"try again in ([\d.]+)s", err)
                if m:
                    wait = float(m.group(1)) + 0.5
                logger.debug(f"[LLM] TPM 429 — sleeping {wait:.1f}s (attempt {attempt+1})")
                await asyncio.sleep(wait)
            elif "timeout" in err.lower() or "timed out" in err.lower():
                await asyncio.sleep(3)
            else:
                raise
    raise last_exc

# ── Constantes attendues par les agents ──────────────────────────
MODEL          = "llama-3.1-8b-instant"
LLM_TIMEOUT    = 60
MAX_RETRIES    = 3
OLLAMA_OPTIONS = {}
