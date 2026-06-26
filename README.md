# Adaptive Wallpapers

[![CI](https://github.com/dz-vadim/adaptive-wallpapers/actions/workflows/ci.yml/badge.svg)](https://github.com/dz-vadim/adaptive-wallpapers/actions/workflows/ci.yml)

Генерація набору шпалер «неонова кав'ярня» під **сезон × час доби × погода**
(4 × 4 × 3 = 48) на основі одного референсу через Gemini 3 Pro Image
(«Nano Banana Pro»), image-to-image. Плюс два способи автоматично ставити
потрібний кадр: нативний плагін KDE Plasma і кросплатформний застосунок (PyQt6,
трей) для GNOME/XFCE/Windows/macOS.

## Структура

```
.
├── scripts/
│   ├── _gemini.py          # спільні утиліти API (клієнт, конфіг, виклик+ретраї)
│   ├── scenes.py           # промпти: матриця сезон×час×погода + нумерація
│   ├── make_reference.py   # 1. робить якісний майстер-референс із оригіналу
│   ├── generate.py         # 2. генерує всі 48 шпалер із референсу
│   ├── regen.py            # 3. перегенерує ОКРЕМІ кадри за іменем (на вибір)
│   └── set_wallpaper.py    #    ставить шпалеру за поточними умовами (CLI/таймер)
├── plasma-plugin/          # плагін шпалер KDE Plasma (адаптивний фон, QML)
│   ├── org.dz.adaptivecoffee/   # сам плагін
│   └── install.sh          #    встановлення + активація
├── app/                    # кросплатформний застосунок (PyQt6, трей)
│   └── adaptive_wallpaper/ #    рушій, GUI, інсталятор — для не-Plasma і Windows
├── docs/                   # app.md (застосунок), build.md (збірка), windows.md
├── reference/              # вхідні зображення (оригінал + майстер-референс)
├── wallpapers/             # вихід: 48 готових шпалер (NN_<season>_<time>_<weather>.png)
├── notebook/               # початковий Colab-ноутбук (історія, без виводів)
├── requirements.txt
├── .env.example            # шаблон ключа → скопіюй у .env
└── LICENSE
```

## Пайплайн

```
reference/_original.jpg
        │  make_reference.py  (Nano Banana Pro: апскейл + насиченість,
        ▼                      видалення підписів, без людей)
reference/_reference.png
        │  generate.py        (48× сезон/час/погода, 2K, image-to-image)
        ▼
wallpapers/NN_<season>_<time>_<weather>.png   (01..48, у порядку послідовності)
```

## Запуск

```fish
cp .env.example .env                  # встав GEMINI_API_KEY у .env
.venv/bin/python scripts/make_reference.py            # майстер-референс (~$0.24, 4K)
.venv/bin/python scripts/generate.py --list-models    # звірити id моделі
.venv/bin/python scripts/generate.py --test           # 3 пробні кадри (~$0.40)
.venv/bin/python scripts/generate.py                  # всі 48 (~$6.6 @ 2K)
```

## Надійність і відновлення

- **Безпечний перезапуск.** `generate.py` пропускає кадри, для яких файл уже
  існує (`wallpapers/<name>.png`). Якщо процес перервався (Ctrl-C, збій мережі,
  вичерпана квота) — просто запусти його ще раз: догенеруються лише відсутні,
  готові не чіпаються й не оплачуються повторно.
- **Атомарний запис.** Кожне зображення спершу перевіряється на цілісність
  (декодування через Pillow), пишеться в тимчасовий `*.part` і лише потім
  атомарно перейменовується. Тож на диску ніколи не лежить обрізаний чи побитий
  файл, який резюме помилково вважало б готовим.
- **Ретраї.** Тимчасові помилки (429/500/503, timeout) повторюються з
  експоненційним бекофом (4→8→16→32 с), між викликами — пауза `--delay` (2 с),
  щоб не впертись у rate-limit на партії з 48.
- Невдалі кадри наприкінці виводяться списком — перезапуск догенерує саме їх.

## Моделі та розмір

- **Модель:** `gemini-3-pro-image` (стабільний id, «Nano Banana Pro»). Задається
  в [scripts/_gemini.py](scripts/_gemini.py). Звірити доступні id:
  `generate.py --list-models`. **Не** використовуй flash-моделі (1K) — звідти
  м'якість і тьмяні кольори.
- **Розмір:** `2K` для шпалер — sweet spot (різкість/ціна). `4K` — помітно
  дорожче без виграшу на екрані; `1K` — замало. Задається `IMAGE_SIZE`
  у [scripts/generate.py](scripts/generate.py) і `--size` у `make_reference.py`
  (там дефолт 4K, бо це одноразовий майстер).
- **Апскейл не потрібен:** Pro-модель віддає нативні 2K/4K — справжні пікселі.

## Вартість (Gemini 3 Pro Image)

| Розмір | За картинку | 48 кадрів |
|--------|-------------|-----------|
| 2K     | $0.134      | ≈ $6.4    |
| 2K batch | $0.067    | ≈ $3.2    |
| 4K     | $0.24       | ≈ $11.5   |

Повний цикл за замовчуванням: майстер-референс 4K (~$0.24) + 4 тестові кадри
2K (~$0.54) + 48 кадрів 2K (~$6.4) ≈ **$7** разово. Кожна перегенерація через
`regen.py` — ~$0.134 за кадр (2K). Вхідні токени додають ~$0.15 на весь набір.

## Послідовність запуску

```fish
# 0. один раз: середовище та ключ
.venv/bin/python -m pip install -r requirements.txt   # якщо .venv ще нема
cp .env.example .env                                  # встав GEMINI_API_KEY

# 1. майстер-референс (оригінал → reference/_reference.png)
.venv/bin/python scripts/make_reference.py

# 2. (необов'язково) звірити id моделі
.venv/bin/python scripts/generate.py --list-models

# 3. пробні 4 кадри (по одному на сезон) — оцінити якість/ефекти
.venv/bin/python scripts/generate.py --test

# 4. усі 48 (можна перезапускати скільки завгодно — резюме безпечне)
.venv/bin/python scripts/generate.py
```

## Перегенерація окремих кадрів

Якщо якісь шпалери не сподобались — `regen.py` переробляє лише їх, не чіпаючи
решту:

```fish
# перезаписати конкретні кадри
.venv/bin/python scripts/regen.py winter_night_clear summer_day_clear

# 3 варіанти на вибір → wallpapers/_variations/ (оригінал не чіпається)
.venv/bin/python scripts/regen.py autumn_evening_rain_snow --variations 3

# точкова правка промпта для цього кадру
.venv/bin/python scripts/regen.py spring_day_clear --extra "stronger neon reflections, denser puddles"

# усі допустимі імена
.venv/bin/python scripts/regen.py --list
```

## Візуальні ефекти

Стиль задається `BASE_PROMPT` у [scripts/scenes.py](scripts/scenes.py) — там
зібрані сучасні ефекти: дзеркальні мокрі поверхні з кольоровими відблисками
неону, bloom/сяйво навколо джерел світла, об'ємне світло, боке, HDR,
кінематографічність. Хочеш підсилити/змінити — редагуй один цей рядок, він
впливає і на `generate.py`, і на `regen.py`.

## Робочий стіл

Шпалера автоматично змінюється під поточні **сезон + час доби + погоду**.
Сезон — з дати; **час доби — за реальним сходом/заходом сонця** (із wttr.in),
офлайн — фіксовані межі; погода — з wttr.in із кешем (30 хв), а **без інтернету
обирається випадково** (реалістичний ухил: частіше ясно/хмарно).

**KDE Plasma — нативний плагін (рекомендовано):** змінює фон плавним crossfade,
оновлюється сам.
```fish
plasma-plugin/install.sh        # встановити + активувати
```
Потім System Settings → Wallpaper → тип **Adaptive Coffee**. У налаштуваннях:
тека (з кнопкою Browse), локація погоди, інтервал, ручний форс сезону/часу/
погоди, прев'ю активного кадру, а також **режим «Carousel»** — циклічна зміна
відмічених кадрів із заданою періодичністю.

**Кросплатформний застосунок (PyQt6) — для не-Plasma і Windows:** трей-іконка,
що сама ставить кадр за сезоном/часом/погодою на GNOME, XFCE, Cinnamon, MATE,
Windows, macOS. Шлях до зображень визначається автоматично, є GUI-налаштування
(режим, тека з Browse, локація, інтервал, ручний форс, прев'ю), **опція екрана
блокування** (зберегти оригінал із відновленням / дзеркалити робочий стіл /
обрати кадр із бібліотеки — KDE/GNOME/Windows), **англійська/українська** мова
(реактивно, авто за локаллю), сучасний тематичний інтерфейс, **один екземпляр**
(другий запуск показує налаштування) та інсталятор: на Windows — звичайний
**setup.exe** (Inno Setup), на Linux — розпакування в системну теку + автозапуск.
```fish
cd app && pip install PyQt6
python -m adaptive_wallpaper            # трей-застосунок
python -m adaptive_wallpaper --once     # поставити раз і вийти (для планувальника)
python -m adaptive_wallpaper --install  # розпакувати зображення + автозапуск
```
Готові бінарники (Linux/Windows) — у [Releases](https://github.com/dz-vadim/adaptive-wallpapers/releases)
(збираються в CI на тег `v*`). Деталі: [docs/app.md](docs/app.md),
збірка власноруч — [docs/build.md](docs/build.md).

**Простий CLI-скрипт** (KDE, відладка): `scripts/set_wallpaper.py` —
`--dry-run`, `--weather`, `--time`, `--location`. Windows-нюанси —
[docs/windows.md](docs/windows.md).

> **Шляхи портативні:** і плагін, і застосунок визначають теку зі шпалерами
> самі (плагін — через `install.sh`, застосунок — автодетектом). Захардкоджених
> особистих шляхів немає. (i18n рядків — у планах.)

## Подяки

Усі 48 шпалер згенеровано **на основі оригінального зображення-референсу** —
сцени затишної неонової кав'ярні. Подяка авторам вихідного арту, що задав
композицію, стиль і атмосферу всього набору:

- **Bogdan mB0sco** — художник:
  [ArtStation](https://www.artstation.com/mb0sco) ·
  [DeviantArt](https://www.deviantart.com/mb0sco)
- **STEEZYASFUCK** — lofi-канал, для якого створено оригінальну ілюстрацію:
  [YouTube](https://www.youtube.com/channel/UCsIg9WMfxjZZvwROleiVsQg)

Згенеровані кадри — похідні від цієї роботи.

## Посилання

- [Gemini API — генерація зображень](https://ai.google.dev/gemini-api/docs/image-generation)
- [Модель `gemini-3-pro-image`](https://ai.google.dev/gemini-api/docs/models/gemini-3-pro-image)
- [Тарифи Gemini API](https://ai.google.dev/gemini-api/docs/pricing)
- [`ImageConfig` (image_size 1K/2K/4K, aspect_ratio)](https://googleapis.github.io/js-genai/release_docs/interfaces/types.ImageConfig.html)
- [google-genai (Python SDK)](https://github.com/googleapis/python-genai)
- [API-ключ — Google AI Studio](https://aistudio.google.com/apikey)
