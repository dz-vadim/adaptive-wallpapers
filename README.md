<div align="center">

<img src="app/adaptive_wallpaper/assets/adaptive-wallpaper.png" width="96" alt="Adaptive Coffee Wallpaper"/>

# Adaptive Coffee Wallpaper

**Жива шпалера «неонова кав'ярня», що сама змінюється під поточний сезон, час доби й погоду.**

48 кадрів (4 сезони × 4 пори доби × 3 типи погоди), згенерованих з одного референсу,
+ кросплатформний застосунок і плагін KDE Plasma, що ставлять потрібний кадр автоматично.

[![CI](https://github.com/dz-vadim/adaptive-wallpapers/actions/workflows/ci.yml/badge.svg)](https://github.com/dz-vadim/adaptive-wallpapers/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/dz-vadim/adaptive-wallpapers?color=e3b94f)](https://github.com/dz-vadim/adaptive-wallpapers/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/dz-vadim/adaptive-wallpapers/total?color=2d6082)](https://github.com/dz-vadim/adaptive-wallpapers/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Platforms](https://img.shields.io/badge/platforms-Windows%20%7C%20Linux%20%7C%20macOS-555)

**Українська** · [English](README.en.md)

<img src="docs/images/hero.jpg" width="760" alt="Чотири сезони кав'ярні"/>

</div>

---

## ✨ Можливості

- 🌦️ **Адаптивний фон** — кадр обирається за **сезоном** (з дати), **часом доби**
  (за реальним сходом/заходом сонця) і **погодою** (wttr.in, офлайн — розумний фолбек).
- 🖥️ **Кросплатформний застосунок** (PyQt6) — трей-іконка для **Windows, Linux
  (GNOME/XFCE/KDE/…), macOS** із плавними переходами та живим прев'ю.
- 🧩 **Плагін KDE Plasma** — нативний адаптивний фон із crossfade.
- 🎠 **Дві поведінки** — *адаптивно* або *карусель* (циклічна зміна кадрів).
- 🔒 **Екран блокування** — не чіпати (з відновленням) / дзеркалити / закріпити кадр.
- 🎨 **Тема під оригінал** — палітра з референсу (синьо-зелений + золото неону),
  підлаштовується під **світлу/темну** системну тему.
- 🌐 **EN / UA** — інтерфейс англійською та українською (реактивно).
- 📦 **Готові білди** — Windows **setup.exe**, портативний zip, Linux-бінарник.

## 🎬 Прев'ю

▶️ **Слайдшоу-відео всіх 48 кадрів** із плавними переходами — згенеруй локально:
`python scripts/make_video.py` (потрібен ffmpeg, [scripts/make_video.py](scripts/make_video.py)).

| ❄️ Зима · ніч | 🌸 Весна · ранок | ☀️ Літо · день | 🍂 Осінь · вечір |
|:--:|:--:|:--:|:--:|
| [<img src="docs/gallery/12_winter_night_rain_snow.jpg" width="200">](wallpapers/12_winter_night_rain_snow.png) | [<img src="docs/gallery/13_spring_morning_clear.jpg" width="200">](wallpapers/13_spring_morning_clear.png) | [<img src="docs/gallery/28_summer_day_clear.jpg" width="200">](wallpapers/28_summer_day_clear.png) | [<img src="docs/gallery/45_autumn_evening_rain_snow.jpg" width="200">](wallpapers/45_autumn_evening_rain_snow.png) |

> 🖼️ **[Переглянути всі 48 кадрів у галереї →](GALLERY.md)**

## ⬇️ Встановлення

### Windows
Завантаж **[`adaptive-wallpaper-setup.exe`](https://github.com/dz-vadim/adaptive-wallpapers/releases/latest)**
і запусти — інсталятор (без прав адміністратора) поставить програму, ярлики,
опційний автозапуск і розпакує всі 48 шпалер. Або візьми портативний `*-windows-portable.zip`.

### Linux
```bash
# готовий бінарник + шпалери
tar xzf adaptive-wallpaper-linux.tar.gz && ./adaptive-wallpaper
# або з сорсів
cd app && pip install PyQt6 && python -m adaptive_wallpaper
```

### KDE Plasma (нативний плагін)
```bash
plasma-plugin/install.sh        # встановити + активувати
```
System Settings → Wallpaper → тип **Adaptive Coffee**.

> Білди без code-signing — SmartScreen може попередити (*More info → Run anyway*).
> Деталі: **[docs/app.md](docs/app.md)** · **[docs/windows.md](docs/windows.md)**.

## 🖥️ Застосунок

Трей-іконка ставить потрібний кадр і оновлює його за таймером. Налаштування —
режим, тека, локація, інтервал, ручний форс сезону/часу/погоди, екран блокування,
мова — із живим прев'ю. Тема йде за системною.

<div align="center">
<img src="docs/images/app-dark.png" width="340" alt="Темна тема"/>
&nbsp;&nbsp;
<img src="docs/images/app-light.png" width="340" alt="Світла тема"/>
</div>

```bash
python -m adaptive_wallpaper --once     # поставити раз і вийти (для планувальника)
python -m adaptive_wallpaper --install  # розпакувати шпалери + автозапуск
```

## 🎨 Як це зроблено

Усі 48 кадрів згенеровано з **одного** референсу через **Gemini 3 Pro Image**
(«Nano Banana Pro»), image-to-image — зберігаючи композицію, вивіски й стиль,
змінюючи лише сезон/світло/погоду та дрібні деталі.

<details>
<summary><b>Пайплайн генерації, моделі та вартість</b></summary>

```
reference/_original.jpg
        │  make_reference.py   (майстер-референс: апскейл + насиченість)
        ▼
reference/_reference.png
        │  generate.py         (48× сезон/час/погода, 2K, image-to-image)
        ▼
wallpapers/NN_<season>_<time>_<weather>.png   (01..48)
```

```fish
cp .env.example .env                                  # GEMINI_API_KEY
.venv/bin/python scripts/make_reference.py            # майстер-референс
.venv/bin/python scripts/generate.py --test           # 3 пробні кадри
.venv/bin/python scripts/generate.py                  # усі 48 (резюме безпечне)
.venv/bin/python scripts/regen.py winter_night_clear  # перегенерувати окремі
```

- **Модель:** `gemini-3-pro-image` (стабільний id). Не flash — звідти м'якість.
- **Розмір:** `2K` (sweet spot різкість/ціна), нативні пікселі без апскейлу.
- **Стиль/ефекти** — у `BASE_PROMPT` ([scripts/scenes.py](scripts/scenes.py)):
  мокрі відблиски неону, bloom, об'ємне світло, HDR; контрольована варіація.
- **Надійність:** безпечний перезапуск (пропуск готових), атомарний запис,
  ретраї з бекофом, негайний стоп при вичерпаній квоті.

| Розмір | За кадр | 48 кадрів |
|--------|---------|-----------|
| 2K     | $0.134  | ≈ $6.4    |
| 2K batch | $0.067 | ≈ $3.2   |
| 4K     | $0.24   | ≈ $11.5   |

Повний цикл ≈ **$7** разово.
</details>

<details>
<summary><b>Збірка бінарників і розробка</b></summary>

- Застосунок: [app/](app/) (PyQt6). Збірка — [docs/build.md](docs/build.md)
  (Nuitka standalone + Inno Setup `setup.exe` на Windows).
- CI: [ci.yml](.github/workflows/ci.yml) (ruff + py_compile + qmllint),
  [release.yml](.github/workflows/release.yml) (білди на тег `v*`).
- Запуск із сорсів: `cd app && pip install PyQt6 && python -m adaptive_wallpaper`.
</details>

## 📁 Структура

```
.
├── app/                  # кросплатформний застосунок (PyQt6, трей)
├── plasma-plugin/        # плагін шпалер KDE Plasma (QML)
├── scripts/              # генерація (Gemini) + make_video.py
├── wallpapers/           # 48 готових кадрів  →  див. GALLERY.md
├── reference/            # вхідний оригінал + майстер-референс
├── docs/                 # app.md · build.md · windows.md · gallery/
└── GALLERY.md            # усі 48 кадрів у сітці
```

## 🙏 Подяки

Усі кадри — похідні від оригінальної ілюстрації кав'ярні:

- **Bogdan mB0sco** — художник:
  [ArtStation](https://www.artstation.com/mb0sco) ·
  [DeviantArt](https://www.deviantart.com/mb0sco)
- **STEEZYASFUCK** — lofi-канал, для якого створено арт:
  [YouTube](https://www.youtube.com/channel/UCsIg9WMfxjZZvwROleiVsQg)

## 📄 Ліцензія

Код — [MIT](LICENSE). Зображення — похідні твори оригінального арту (див. Подяки);
використовуйте з відповідною атрибуцією авторів.
