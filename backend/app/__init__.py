from pathlib import Path

from dotenv import load_dotenv

# .env читаем до импорта db и llm: они берут настройки из окружения при импорте
load_dotenv(Path(__file__).resolve().parents[2] / ".env")
