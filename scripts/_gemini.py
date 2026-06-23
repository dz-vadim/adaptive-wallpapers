"""Спільні утиліти для викликів Gemini image API (Nano Banana Pro).

Усе, що дублювалося між make_reference.py і generate.py:
ініціалізація клієнта, побудова конфіга з контролем роздільності,
надійний виклик із ретраями та витяганням байтів зображення.
"""
import os
import time
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_env() -> None:
    """Підвантажує .env із кореня проєкту (необов'язково)."""
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
    except ImportError:
        pass


load_env()

from google import genai
from google.genai import types

# Gemini 3 Pro Image — стабільний id ("Nano Banana Pro").
# Звір актуальний id через `generate.py --list-models`.
MODEL = "gemini-3-pro-image"

MAX_RETRIES = 4
RETRY_BASE_DELAY = 4  # секунди; експоненційно: 4, 8, 16, 32


class CreditsExhausted(Exception):
    """Передплачені кредити / білінг вичерпані. Ретраї марні — треба зупинити
    весь прогін, поповнити баланс і запустити знову (готові пропустяться)."""


def _is_credits_depleted(exc: Exception) -> bool:
    msg = str(exc).lower()
    return ("credits are depleted" in msg or "prepayment credit" in msg
            or "billing" in msg)


def save_image(path: Path, data: bytes) -> None:
    """Надійне збереження: спершу перевіряємо, що байти декодуються в
    зображення, пишемо в тимчасовий файл і атомарно перейменовуємо.
    Так резюме (skip за out.exists()) ніколи не натикається на обрізаний
    чи побитий файл — на диску лежать лише цілісні картинки.
    """
    from PIL import Image
    with Image.open(BytesIO(data)) as im:
        im.verify()  # кине виняток на пошкоджених байтах
    tmp = path.with_name(path.name + ".part")
    tmp.write_bytes(data)
    os.replace(tmp, path)  # атомарно в межах однієї ФС


def make_client() -> "genai.Client":
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise SystemExit(
            "❌ Немає GEMINI_API_KEY (env або .env у корені проєкту).")
    return genai.Client(api_key=key)


def build_config(image_size: str = "2K", aspect_ratio: str = "16:9"):
    """Конфіг із нативною високою роздільністю.

    Fallback ловиться саме тут (на побудові конфіга), а не навколо
    мережевого виклику — інакше старий SDK мовчки роняв би якість.
    """
    try:
        return types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
            image_config=types.ImageConfig(
                aspect_ratio=aspect_ratio,
                image_size=image_size,
            ),
        )
    except (TypeError, ValueError) as e:
        print(f"⚠️ SDK не підтримує image_config ({e}); "
              f"генеруємо без контролю роздільності — онови google-genai.")
        return types.GenerateContentConfig(response_modalities=["IMAGE"])


def _is_transient(exc: Exception) -> bool:
    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    if isinstance(code, int) and code in (429, 500, 503):
        return True
    msg = str(exc)
    return any(s in msg for s in (
        "429", "500", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE",
        "deadline", "timeout", "Timeout"))


def _extract_image(resp):
    """Повертає (bytes, None) при успіху або (None, причина) для діагностики."""
    cands = getattr(resp, "candidates", None)
    if not cands:
        fb = getattr(resp, "prompt_feedback", None)
        return None, f"немає кандидатів (можливе блокування промпта: {fb})"
    cand = cands[0]
    content = getattr(cand, "content", None)
    # parts може бути None, якщо модель відмовилась/заблокувала — захищаємось
    parts = (getattr(content, "parts", None) or []) if content else []
    for part in parts:
        data = getattr(getattr(part, "inline_data", None), "data", None)
        if data:
            return data, None
    reason = getattr(cand, "finish_reason", None)
    safety = getattr(cand, "safety_ratings", None)
    txt = next((p.text for p in parts if getattr(p, "text", None)), None)
    detail = f"finish_reason={reason}"
    if safety:
        detail += f", safety={safety}"
    if txt:
        detail += f", text={txt[:200]}"
    return None, detail


def generate_image(client, image_bytes: bytes, mime: str, prompt: str,
                   config) -> "bytes | None":
    """Один виклик image-to-image із ретраями. Повертає байти PNG або None."""
    contents = [
        types.Part.from_bytes(data=image_bytes, mime_type=mime),
        prompt,
    ]
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = client.models.generate_content(
                model=MODEL, contents=contents, config=config)
            data, err = _extract_image(resp)
            if data:
                return data
            print(f"   ⚠️ Модель не повернула зображення: {err}")
            return None
        except Exception as e:
            if _is_credits_depleted(e):
                # фатально: ретраї не допоможуть, зупиняємо весь прогін
                raise CreditsExhausted(str(e)[:200]) from e
            if _is_transient(e) and attempt < MAX_RETRIES:
                delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                print(f"   ⏳ {str(e)[:80]} — ретрай через {delay}s "
                      f"({attempt}/{MAX_RETRIES})")
                time.sleep(delay)
                continue
            print(f"   ❌ Помилка API: {str(e)[:200]}")
            return None
    return None
