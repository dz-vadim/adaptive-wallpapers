#!/usr/bin/env python3
"""
Робить ОДИН якісний референс із reference/_original.jpg через Gemini 3 Pro
Image ("Nano Banana Pro"): підвищує якість/різкість/насиченість і прибирає
нижні підписи — без opencv-постобробки.

Запуск (з кореня проєкту; ключ — у .env):
    .venv/bin/python scripts/make_reference.py            # 4K майстер-референс
    .venv/bin/python scripts/make_reference.py --size 2K  # за бажанням

Результат → reference/_reference.png. Саме його далі споживає generate.py.
"""
import argparse

from _gemini import MODEL, ROOT, build_config, generate_image, make_client, save_image

SRC = ROOT / "reference" / "_original.jpg"    # вхід: оригінал 1920x1080
OUT = ROOT / "reference" / "_reference.png"   # вихід: чистий якісний майстер
ASPECT_RATIO = "16:9"

# Задача моделі: реставрація+апскейл БЕЗ зміни сцени; кути — чистий асфальт.
# Уникаємо слів "remove watermark/signature" — вони тригерять відмову моделі.
PROMPT = (
    "Concept art of a cozy neon COFFEE shop on a street corner at night, "
    "anime/cyberpunk style. Recreate this exact same scene at maximum quality "
    "and the highest resolution, preserving EXACTLY the composition, layout, "
    "colors, mood, lighting and every object and detail: the camera angle, the "
    "glowing neon COFFEE sign and cup, the MOTEL sign, the SPEED 30 sign, the "
    "pedestrian crossing, the parked cars, the string of colored lights, the "
    "wet reflective asphalt and puddles. "
    "Enhance fidelity: ultra sharp focus, crisp clean edges, vibrant saturated "
    "colors, rich deep contrast, fine texture detail; remove all softness, "
    "blur and haze. "
    "Compose the bottom-left and bottom-right corners of the frame as plain, "
    "clean wet asphalt only — smooth pavement with no lettering and no captions "
    "there. The final image contains no text or letters anywhere. "
    "The scene is empty and deserted: no people, no figures, no silhouettes."
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", default="4K", choices=["1K", "2K", "4K"],
                    help="роздільність майстра (default 4K, ~$0.24 одноразово)")
    args = ap.parse_args()

    if not SRC.exists():
        raise SystemExit(f"❌ Немає вхідного файлу: {SRC}")

    client = make_client()
    image_bytes = SRC.read_bytes()
    print(f"✅ Вхід: {SRC.name} ({len(image_bytes)/1024:.0f} KB) → "
          f"{MODEL} @ {args.size} {ASPECT_RATIO}")

    config = build_config(args.size, ASPECT_RATIO)
    data = generate_image(client, image_bytes, "image/jpeg", PROMPT, config)
    if not data:
        raise SystemExit("❌ Не вдалося отримати референс.")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    save_image(OUT, data)
    print(f"🎉 Готово: reference/{OUT.name}")
    print("→ generate.py вже налаштований брати reference/_reference.png")


if __name__ == "__main__":
    main()
