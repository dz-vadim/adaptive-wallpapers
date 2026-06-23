#!/usr/bin/env python3
"""
Перегенерація ОКРЕМИХ шпалер за іменем — коли якісь кадри не сподобались.

Приклади (з кореня проєкту):
    # перегенерувати один-два кадри (перезаписує wallpapers/<name>.png)
    .venv/bin/python scripts/regen.py winter_night_clear summer_day_clear

    # 3 варіанти на вибір (НЕ чіпає оригінал; кладе у wallpapers/_variations/)
    .venv/bin/python scripts/regen.py autumn_evening_rain_snow --variations 3

    # точкова правка промпта для цього кадру
    .venv/bin/python scripts/regen.py spring_day_clear --extra "more rain, stronger neon reflections, denser puddles"

    # список усіх допустимих імен
    .venv/bin/python scripts/regen.py --list
"""
import argparse
import time
from pathlib import Path

from _gemini import (ROOT, MODEL, make_client, build_config, generate_image,
                     save_image, CreditsExhausted)
from scenes import build_scene, render_prompt, parse_name, ALL_NAMES, numbered

BASE_IMAGE_PATH = ROOT / "reference" / "_reference.png"
OUTPUT_DIR = ROOT / "wallpapers"
VARIATIONS_DIR = OUTPUT_DIR / "_variations"

IMAGE_SIZE = "2K"
ASPECT_RATIO = "16:9"
DELAY_BETWEEN = 2


def boost_colors(path: Path) -> None:
    from PIL import Image, ImageEnhance
    img = Image.open(path).convert("RGB")
    img = ImageEnhance.Color(img).enhance(1.12)
    img = ImageEnhance.Contrast(img).enhance(1.06)
    img = ImageEnhance.Sharpness(img).enhance(1.10)
    img.save(path, quality=95)


def main():
    ap = argparse.ArgumentParser(
        description="Перегенерація окремих шпалер за іменем.")
    ap.add_argument("names", nargs="*",
                    help="імена кадрів, напр. winter_night_clear")
    ap.add_argument("--list", action="store_true",
                    help="показати всі допустимі імена та вийти")
    ap.add_argument("--variations", type=int, default=1, metavar="N",
                    help="N варіантів на вибір у wallpapers/_variations/ "
                         "(оригінал не чіпається). Default 1 = перезапис.")
    ap.add_argument("--extra", default="",
                    help="додаткова правка промпта для цих кадрів")
    ap.add_argument("--boost", action="store_true",
                    help="пост-корекція кольору/різкості")
    ap.add_argument("--size", default=IMAGE_SIZE, choices=["1K", "2K", "4K"])
    ap.add_argument("--delay", type=float, default=DELAY_BETWEEN)
    args = ap.parse_args()

    if args.list:
        print("Допустимі імена (48):")
        for n in ALL_NAMES:
            print(f"  {n}")
        return

    if not args.names:
        raise SystemExit("Вкажи хоча б одне ім'я, або --list. "
                         "Приклад: regen.py winter_night_clear")

    # валідація імен ДО будь-яких платних викликів
    try:
        scenes = {n: build_scene(*parse_name(n)) for n in args.names}
    except ValueError as e:
        raise SystemExit(f"❌ {e}")

    if not BASE_IMAGE_PATH.exists():
        raise SystemExit(f"❌ Немає референсу: {BASE_IMAGE_PATH}")

    client = make_client()
    image_bytes = BASE_IMAGE_PATH.read_bytes()
    mime = "image/png" if BASE_IMAGE_PATH.suffix.lower() == ".png" else "image/jpeg"
    config = build_config(args.size, ASPECT_RATIO)

    mode = (f"{args.variations} варіант(и) → _variations/"
            if args.variations > 1 else "перезапис оригіналу")
    print(f"✅ Референс: {BASE_IMAGE_PATH.name}, модель: {MODEL} @ {args.size}, "
          f"режим: {mode}")
    if args.extra:
        print(f"   Правка: {args.extra}")

    # план: (ім'я, шлях виводу, сцена)
    plan = []
    for name, scene in scenes.items():
        if args.variations > 1:
            for k in range(1, args.variations + 1):
                plan.append((name, VARIATIONS_DIR / f"{numbered(name)}_v{k}.png", scene))
        else:
            plan.append((name, OUTPUT_DIR / f"{numbered(name)}.png", scene))

    (VARIATIONS_DIR if args.variations > 1 else OUTPUT_DIR).mkdir(
        parents=True, exist_ok=True)

    total = len(plan)
    errors = []
    print(f"🚀 Перегенерація: {total} зображень\n")
    for i, (name, out, scene) in enumerate(plan, 1):
        print(f"[{i}/{total}] {out.name} …")
        try:
            data = generate_image(client, image_bytes, mime,
                                  render_prompt(scene, args.extra), config)
        except CreditsExhausted as e:
            print(f"\n💳 Кредити Gemini вичерпані — зупинено. {e}\n"
                  f"   Поповни баланс на https://ai.studio/projects і запусти знову.")
            return
        if data:
            save_image(out, data)
            if args.boost:
                boost_colors(out)
            print(f"   ✅ {out.relative_to(ROOT)}")
        else:
            errors.append(out.name)
        if i < total:
            time.sleep(args.delay)

    if errors:
        print(f"\n⚠️ Не вдалося ({len(errors)}): {errors}")
    elif args.variations > 1:
        print(f"\n🎉 Готово. Обери найкращі у {VARIATIONS_DIR.relative_to(ROOT)}/ "
              f"і скопіюй у wallpapers/<name>.png.")
    else:
        print(f"\n🎉 Готово, перезаписано {total} кадр(ів).")


if __name__ == "__main__":
    main()
