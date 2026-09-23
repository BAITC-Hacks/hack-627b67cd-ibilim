"""Единственная точка вызова LLM. Больше нигде OpenAI не импортируется.

Правила (см. docs/05-llm.md):
  - только Structured Outputs, strict: true;
  - не сошлась схема — ретрай, не «починка регуляркой»;
  - PROMPT_VERSION входит в ключ кеша: поменял промпт — бампни версию;
  - DEMO_MODE=1 отдаёт фикстуры вместо сети (страховка на демо).
"""

import hashlib
import json
import os
from pathlib import Path

from openai import OpenAI

PROMPT_VERSION = "v1"

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "seed" / "fixtures"

MODEL = os.getenv("OPENAI_MODEL", "gpt-5")
VISION_MODEL = os.getenv("OPENAI_VISION_MODEL", MODEL)
DEMO_MODE = os.getenv("DEMO_MODE", "0") == "1"

_client: OpenAI | None = None


def client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client


def cache_key(*parts: str) -> str:
    return hashlib.sha256("|".join([PROMPT_VERSION, *parts]).encode()).hexdigest()


def _fixture(name: str) -> dict | None:
    path = FIXTURES / f"{name}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def call_json(name: str, system: str, user: str, schema: dict, *, retries: int = 2) -> dict:
    """Вызов с жёсткой схемой. name — имя вызова, оно же имя фикстуры для DEMO_MODE."""
    if DEMO_MODE:
        fixture = _fixture(name)
        if fixture is not None:
            return fixture

    last_error: Exception | None = None
    for _ in range(retries + 1):
        try:
            response = client().chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {"name": name, "schema": schema, "strict": True},
                },
            )
            return json.loads(response.choices[0].message.content)
        except Exception as exc:  # noqa: BLE001 — на хакатоне важнее не упасть
            last_error = exc
    raise RuntimeError(f"llm call {name} failed: {last_error}")


def call_vision(name: str, system: str, user: str, image_b64: str, schema: dict) -> dict:
    """Распознавание работы с фото. Модель НЕ решает задачу — только извлекает написанное."""
    if DEMO_MODE:
        fixture = _fixture(name)
        if fixture is not None:
            return fixture

    response = client().chat.completions.create(
        model=VISION_MODEL,
        messages=[
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
                ],
            },
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": name, "schema": schema, "strict": True},
        },
    )
    return json.loads(response.choices[0].message.content)
