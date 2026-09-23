"""Единственная точка вызова LLM. Больше нигде OpenAI не импортируется.

Правила: только Structured Outputs (strict: true); ответ не разобрался или не прошёл проверку —
повтор с причиной отказа; кончились попытки — LLMUnavailable, и ai.py включает локальную заглушку.
"""

import json
import os
from collections.abc import Callable

from openai import OpenAI

MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")
REASONING_EFFORT = os.getenv("OPENAI_REASONING_EFFORT", "")  # только для reasoning-моделей
TIMEOUT = float(os.getenv("OPENAI_TIMEOUT", "40"))
DEMO_MODE = os.getenv("DEMO_MODE", "0") == "1"

_client: OpenAI | None = None


class LLMUnavailable(Exception):
    """Нет ключа, сеть или модель не дала валидный ответ за все попытки."""

    def __init__(self, message: str, attempts: int):
        super().__init__(message)
        self.attempts = attempts


def mode() -> str:
    """llm — ходим в API; stub — DEMO_MODE или нет ключа: работает локальная заглушка."""
    return "stub" if DEMO_MODE or not os.getenv("OPENAI_API_KEY") else "llm"


def client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], timeout=TIMEOUT, max_retries=0)
    return _client


def _validate_schema(value, schema: dict, path: str = "$") -> None:
    """Локально проверяет типы, обязательные поля и enum наших схем Structured Outputs.

    Строгая схема на стороне API не заменяет проверку ответа перед использованием.
    Поддерживаемые типы намеренно ограничены схемами в ai.py; неизвестная схема отклоняется.
    """
    kind = schema.get("type")
    types = {"object": dict, "array": list, "string": str, "boolean": bool}
    if kind not in types or type(value) is not types[kind]:
        raise ValueError(f"{path}: ожидается {kind}")
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(f"{path}: значение вне допустимого списка")
    if kind == "object":
        properties = schema.get("properties", {})
        missing = set(schema.get("required", [])) - value.keys()
        if missing:
            raise ValueError(f"{path}: отсутствуют поля {', '.join(sorted(missing))}")
        if schema.get("additionalProperties") is False and value.keys() - properties.keys():
            raise ValueError(f"{path}: лишние поля")
        for key, item in value.items():
            if key in properties:
                _validate_schema(item, properties[key], f"{path}.{key}")
    elif kind == "array":
        for index, item in enumerate(value):
            _validate_schema(item, schema["items"], f"{path}[{index}]")


def call_json(
    name: str,
    system: str,
    user: str,
    schema: dict,
    validate: Callable[[dict], None] | None = None,
    retries: int = 2,
) -> tuple[dict, int]:
    """Вызов со строгой схемой → (ответ, число попыток).

    validate бросает ValueError, если ответ по смыслу негодный; причина уходит в следующую попытку.
    """
    if mode() == "stub":
        raise LLMUnavailable("нет OPENAI_API_KEY или включён DEMO_MODE", 0)

    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    extra = {"reasoning_effort": REASONING_EFFORT} if REASONING_EFFORT else {}
    last_error = ""
    for attempt in range(1, retries + 2):
        try:
            response = client().chat.completions.create(
                model=MODEL,
                messages=messages,
                response_format={
                    "type": "json_schema",
                    "json_schema": {"name": name, "schema": schema, "strict": True},
                },
                **extra,
            )
            data = json.loads(response.choices[0].message.content or "")
            _validate_schema(data, schema)
            if validate:
                validate(data)
            return data, attempt
        except ValueError as exc:  # в т.ч. JSONDecodeError: ответ пришёл, но негодный
            last_error = str(exc)
            messages = messages[:2] + [{"role": "user", "content": f"Предыдущий ответ отклонён: {exc}. Исправь и ответь заново."}]
        except Exception as exc:  # noqa: BLE001 — сеть, лимиты, таймаут: повторяем, потом заглушка
            last_error = f"{type(exc).__name__}: {exc}"
    raise LLMUnavailable(last_error, retries + 1)
