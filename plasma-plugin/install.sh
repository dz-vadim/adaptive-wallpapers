#!/usr/bin/env bash
# Встановлює (симлінком) плагін шпалер Adaptive Coffee у профіль користувача
# та активує його на всіх робочих столах KDE Plasma.
set -euo pipefail

ID="org.dz.adaptivecoffee"
SRC="$(cd "$(dirname "$0")/$ID" && pwd)"
DEST_DIR="$HOME/.local/share/plasma/wallpapers"
DEST="$DEST_DIR/$ID"

mkdir -p "$DEST_DIR"
rm -rf "$DEST"
ln -s "$SRC" "$DEST"          # симлінк: правки у репо одразу підхоплюються
echo "✅ Встановлено: $DEST -> $SRC"

# Активувати плагін на всіх десктопах через Plasma scripting.
if command -v qdbus6 >/dev/null 2>&1; then QDBUS=qdbus6; else QDBUS=qdbus; fi
"$QDBUS" org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript '
  var ds = desktops();
  for (var i = 0; i < ds.length; i++) {
      ds[i].wallpaperPlugin = "org.dz.adaptivecoffee";
  }
' >/dev/null 2>&1 && echo "✅ Активовано на всіх робочих столах." \
  || echo "ℹ️ Не вдалось активувати автоматично — обери «Adaptive Coffee» у System Settings → Wallpaper."

echo "Готово. Якщо плагіна не видно — перезапусти оболонку:  systemctl --user restart plasma-plasmashell"
