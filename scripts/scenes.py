"""Опис сцен (сезон × час × погода) і складання промптів.

Спільне для generate.py (повний набір) і regen.py (окремі кадри),
щоб логіка й візуальний стиль були в одному місці.
"""

# Базовий промпт: фіксує композицію, задає якість і СУЧАСНІ візуальні ефекти,
# забороняє людей/текст. Конкретну сцену додає render_prompt().
BASE_PROMPT = (
    "A cozy neon coffee shop building on a street corner, anime/cyberpunk "
    "aesthetic, in the exact style of the input reference image. "
    "CRITICAL: preserve the exact architectural layout, building proportions, "
    "camera angle, composition, and the exact placement of the neon COFFEE "
    "sign, the SPEED 30 sign, the MOTEL sign and the pedestrian crossing from "
    "the reference. "
    # --- сучасні візуальні ефекти ---
    "Cinematic, polished modern digital-art look with rich atmosphere: soft "
    "neon glow and bloom around light sources, gentle volumetric light and "
    "light rays, subtle atmospheric depth, delicate bokeh on distant lights, "
    "crisp specular highlights, high dynamic range. "
    "Surface wetness MUST match the weather: when it is raining or the ground "
    "is wet, the asphalt is glossy and mirror-like with vivid colorful neon "
    "reflections and puddles; on clear sunny dry days the asphalt is DRY and "
    "matte — no puddles, no mirror reflections, no wet sheen. "
    # --- якість ---
    "Highly detailed, ultra sharp focus, clean crisp edges, rich natural "
    "organic colors, vibrant and saturated but believable, deep contrast, "
    "fine texture detail. Colors must stay punchy and full — never pale, "
    "desaturated, faded or washed-out. "
    # --- читабельність вивісок (точні слова, щоб не було гібериш-тексту) ---
    "Render every sign with sharp, clean, correctly-spelled lettering: the "
    "large rooftop neon sign clearly reads \"COFFEE\" and is ALWAYS switched "
    "on — brightly lit, vividly glowing in every scene including full daylight, "
    "never an unlit dark outline; the white road sign "
    "clearly reads \"SPEED\" then \"30\" then \"MAXIMUM\" stacked vertically; "
    "the retro roadside sign clearly reads \"MOTEL\"; the horizontal green "
    "street-name sign on the pole clearly reads \"LOFTSTREET\"; the door sign "
    "reads \"OPEN\". Keep all letters crisp, even and legible — no blurry, "
    "warped, doubled or random gibberish text. "
    # --- заборони ---
    "The scene is completely empty and deserted: absolutely no people, no "
    "humans, no pedestrians, no figures, no silhouettes inside or outside. "
    "No extra overlay text, captions, watermark, logo, signature or UI icons "
    "beyond the in-scene signs described above. "
    "Avoid: blur, washed-out colors, low contrast, soft mushy details, muddy "
    "flat lighting. Do not add snow unless the scene explicitly says so. "
    # --- контрольована варіація (баланс із аналізу) ---
    "Keep the building architecture, proportions, render style, the cozy "
    "art style, the camera angle, the 16:9 framing, the overall composition "
    "and ALL signage wording exactly as in the reference. Do NOT restyle the "
    "facade into a neon-tube cyberpunk front, do NOT re-frame, zoom or crop "
    "differently, do NOT add extra background buildings, and do NOT change any "
    "sign text. Within that fixed stage, small props and vehicles MAY vary "
    "subtly and naturally to fit the season and time. Vehicles are optional "
    "and flexible, and SHOULD differ from image to image: sometimes none at "
    "all, sometimes one parked by the corner (now and then a police car), "
    "sometimes one or two vehicles further down the road — parked in different "
    "spots, driving toward the camera, passing by the cafe, or placed off to "
    "the side near the road sign or behind the cafe; rarely a motorcycle. Each "
    "vehicle must blend naturally into the scene. Use varied but ordinary cars "
    "that fit the cozy retro anime street setting, modest in number, never a "
    "crowded parking lot, and they must NOT block or cover the main "
    "composition or the cafe building. No Cybertrucks, no exotic, futuristic "
    "or sci-fi vehicles. The bike rack may "
    "occasionally hold one ordinary bicycle; the potted plants and flowers may "
    "differ; the plastic chair may shift slightly. Keep every such change "
    "subtle, plausible and in the same art style. No implausible flourishes "
    "such as words projected on the ground or giant murals over the windows."
)

SEASONS = {
    "winter": "winter, snow on the ground, bare frosty trees",
    "spring": "spring, blooming flowers, fresh green leaves, no snow",
    "summer": "summer, lush green trees, warm clear atmosphere, no snow",
    "autumn": "autumn, orange and red foliage, fallen leaves, no snow",
}

TIMES_OF_DAY = {
    "morning": "early morning, soft sunrise illumination, long gentle shadows",
    "day":     "midday, bright directional sunlight, sharp crisp shadows",
    "evening": "golden hour, warm sunset lighting, dramatic colorful sky",
    "night":   "night, dark sky, brightly illuminated neon COFFEE sign, glowing streetlights",
}

WEATHER = {
    "clear":     "clear sky, bright sunshine, pleasant weather, high visibility, dry matte asphalt with no puddles",
    "cloudy":    "overcast sky, moody soft diffused light, mostly dry ground with only slight dampness",
    "rain_snow": "heavy rain, glistening wet asphalt with vivid neon reflections and ripples in puddles",
}

# Посезонний декор. Різнокольорова святкова гірлянда — ЛИШЕ взимку; в інші
# сезони теплі однотонні лампочки або без них (фікс «новорічні вогники влітку»).
DECOR = {
    "winter": "festive warm multicolored string lights along the awning, cozy "
              "winter touches, snow-dusted props",
    "spring": "plain warm-white string lights, window boxes of fresh spring "
              "flowers (tulips, daffodils, blossoms); no multicolored holiday lights",
    "summer": "plain warm-white string lights or none, leafy green potted "
              "plants; no multicolored holiday lights",
    "autumn": "plain warm-white string lights, scattered fallen leaves, a "
              "couple of small pumpkins by the door; no multicolored holiday lights",
}


def build_scene(season: str, time: str, weather: str) -> str:
    """Збирає опис конкретної сцени; зима+опади → сніг замість дощу."""
    s, t = SEASONS[season], TIMES_OF_DAY[time]
    if weather == "rain_snow" and season == "winter":
        w = ("heavy snowfall, thick fresh snow covering the roof and ground, "
             "wet glistening road")
    else:
        w = WEATHER[weather]
    return f"{s}, {t}, {w}. Seasonal styling: {DECOR[season]}"


def render_prompt(scene: str, extra: str = "") -> str:
    """Повний промпт: база + сцена (+ опційна правка користувача)."""
    p = f"{BASE_PROMPT} Scene: {scene}."
    if extra:
        p += f" Additional art direction: {extra}."
    return p


def parse_name(name: str):
    """`winter_night_rain_snow` → ('winter','night','rain_snow'). Валідовано."""
    parts = name.split("_")
    if len(parts) >= 3:
        season, time, weather = parts[0], parts[1], "_".join(parts[2:])
        if season in SEASONS and time in TIMES_OF_DAY and weather in WEATHER:
            return season, time, weather
    raise ValueError(
        f"невідома назва '{name}'. Очікується <season>_<time>_<weather>, "
        f"де season∈{list(SEASONS)}, time∈{list(TIMES_OF_DAY)}, "
        f"weather∈{list(WEATHER)}.")


ALL_NAMES = [f"{s}_{t}_{w}"
             for s in SEASONS for t in TIMES_OF_DAY for w in WEATHER]

# Порядковий номер кожної сцени (порядок генерації) — для збереження файлів
# у правильній послідовності: 01_winter_morning_clear … 48_autumn_night_rain_snow.
NUMBER = {name: i for i, name in enumerate(ALL_NAMES, 1)}


def numbered(name: str) -> str:
    """`winter_day_clear` → `04_winter_day_clear` (префікс для сортування)."""
    return f"{NUMBER[name]:02d}_{name}"


def all_jobs():
    """Усі 48 завдань: [(name, scene), ...]."""
    return [(f"{s}_{t}_{w}", build_scene(s, t, w))
            for s in SEASONS for t in TIMES_OF_DAY for w in WEATHER]


# Пробні кадри для --test: по одному на КОЖЕН сезон, різні час/погода,
# щоб оцінити діапазон і візуальні ефекти перед повним прогоном.
TEST_CASES = [
    ("winter_night_rain_snow",   build_scene("winter", "night", "rain_snow")),
    ("spring_morning_clear",     build_scene("spring", "morning", "clear")),
    ("summer_day_clear",         build_scene("summer", "day", "clear")),
    ("autumn_evening_rain_snow", build_scene("autumn", "evening", "rain_snow")),
]
