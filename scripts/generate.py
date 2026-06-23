#!/usr/bin/env python3
"""
Генерація адаптивних шпалер (сезон × час доби × погода) на базі одного
референсного зображення через Gemini image-to-image.

Запуск локально (з кореня проєкту; ключ — у .env):
    .venv/bin/python scripts/generate.py --list-models   # 1) доступні моделі
    .venv/bin/python scripts/generate.py --test          # 2) пробні 3 кадри
    .venv/bin/python scripts/generate.py                 # 3) всі 48 кадрів

Ключові рішення щодо ЯКОСТІ (чому картинки виходять різкими й насиченими):
  * вхід — якісний референс reference/_reference.png (make_reference.py);
  * модель — Gemini 3 Pro Image ("Nano Banana Pro"), яка нативно віддає 2K/4K,
    тому АПСКЕЙЛ НЕ ПОТРІБЕН — це справжні пікселі, а не домальовані;
  * промпт містить явні вимоги до різкості/насиченості й заборону людей/тексту;
  * легка пост-корекція кольору опційна (--boost).
"""
import argparse
import time
from pathlib import Path

from _gemini import (ROOT, MODEL, make_client, build_config, generate_image,
                     save_image, CreditsExhausted)
from scenes import all_jobs, render_prompt, TEST_CASES, numbered

# --- Конфіг -------------------------------------------------------------------
BASE_IMAGE_PATH = ROOT / "reference" / "_reference.png"
OUTPUT_DIR = ROOT / "wallpapers"

IMAGE_SIZE = "2K"        # "1K" | "2K" | "4K"; 2K — sweet spot для шпалер
ASPECT_RATIO = "16:9"
DELAY_BETWEEN = 2        # секунди паузи між викликами, щоб не ловити rate-limit


def list_models(client) -> None:
    print("Моделі, що вміють генерувати зображення:\n")
    for m in client.models.list():
        actions = getattr(m, "supported_actions", None) or []
        name = m.name.replace("models/", "")
        if "image" in name.lower() or "generateContent" in actions:
            print(f"  {name:45s}  {actions}")
    print(f"\n→ Поточна MODEL = {MODEL}. Онови у scripts/_gemini.py за потреби.")


def boost_colors(path: Path) -> None:
    """Легка пост-корекція (--boost): більше «панчу» як в оригіналі."""
    from PIL import Image, ImageEnhance
    img = Image.open(path).convert("RGB")
    img = ImageEnhance.Color(img).enhance(1.12)
    img = ImageEnhance.Contrast(img).enhance(1.06)
    img = ImageEnhance.Sharpness(img).enhance(1.10)
    img.save(path, quality=95)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list-models", action="store_true",
                    help="показати доступні моделі та вийти")
    ap.add_argument("--test", action="store_true",
                    help="згенерувати лише 3 пробні кадри")
    ap.add_argument("--boost", action="store_true",
                    help="увімкнути пост-корекцію кольору/різкості")
    ap.add_argument("--delay", type=float, default=DELAY_BETWEEN,
                    help=f"пауза між викликами, сек (default {DELAY_BETWEEN})")
    ap.add_argument("--size", default=IMAGE_SIZE, choices=["1K", "2K", "4K"],
                    help=f"роздільність (default {IMAGE_SIZE}; 4K — чіткіший "
                         f"дрібний текст, але дорожче)")
    args = ap.parse_args()

    client = make_client()
    if args.list_models:
        list_models(client)
        return

    if not BASE_IMAGE_PATH.exists():
        raise SystemExit(f"❌ Немає референсу: {BASE_IMAGE_PATH}\n"
                         f"   Спершу: .venv/bin/python scripts/make_reference.py")
    image_bytes = BASE_IMAGE_PATH.read_bytes()
    mime = "image/png" if BASE_IMAGE_PATH.suffix.lower() == ".png" else "image/jpeg"
    config = build_config(args.size, ASPECT_RATIO)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✅ База: {BASE_IMAGE_PATH.name} ({len(image_bytes)/1024:.0f} KB), "
          f"модель: {MODEL}, розмір: {args.size} {ASPECT_RATIO}")

    jobs = list(TEST_CASES) if args.test else all_jobs()
    total = len(jobs)
    errors = []
    print(f"🚀 Старт: {total} зображень → {OUTPUT_DIR}\n")

    for i, (name, scene) in enumerate(jobs, 1):
        out = OUTPUT_DIR / f"{numbered(name)}.png"
        if out.exists():
            print(f"[{i}/{total}] ⏭️  вже є: {name}")
            continue
        print(f"[{i}/{total}] {name} …")
        try:
            data = generate_image(client, image_bytes, mime,
                                  render_prompt(scene), config)
        except CreditsExhausted as e:
            done = len(list(OUTPUT_DIR.glob("*.png")))
            print(f"\n💳 Кредити Gemini вичерпані — прогін зупинено.\n"
                  f"   {e}\n"
                  f"   Готово {done}/{total}. Поповни баланс на "
                  f"https://ai.studio/projects і запусти скрипт знову — "
                  f"готові пропустяться, догенеруються лише решта.")
            return
        if data:
            save_image(out, data)
            if args.boost:
                boost_colors(out)
            print(f"   ✅ {out.name}")
        else:
            errors.append(name)
        if i < total:
            time.sleep(args.delay)

    if errors:
        print(f"\n⚠️ Не вдалося ({len(errors)}): {errors}")
        print("   Перезапусти скрипт — готові файли пропустяться, "
              "догенеруються лише ці.")
    else:
        print(f"\n🎉 Готово, всі {total} згенеровано.")


if __name__ == "__main__":
    main()
