#!/usr/bin/env python3
"""Точка входу для «заморожених» збірок (Nuitka/PyInstaller).

Запуск із репозиторію — краще через `python -m adaptive_wallpaper`;
цей файл потрібен інструментам збірки, які хочуть один стартовий скрипт.
"""
import sys

from adaptive_wallpaper.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
