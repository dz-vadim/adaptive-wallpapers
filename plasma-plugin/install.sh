#!/usr/bin/env bash
# Встановлює (симлінком) плагін шпалер Adaptive Coffee у профіль користувача,
# активує його на всіх робочих столах KDE Plasma й вписує абсолютний шлях до
# теки wallpapers/ у конфіг (щоб працювало без захардкоженого шляху в репо).
set -euo pipefail

ID="org.dz.adaptivecoffee"
SRC="$(cd "$(dirname "$0")/$ID" && pwd)"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
WALLPAPERS="$REPO/wallpapers"
DEST_DIR="$HOME/.local/share/plasma/wallpapers"
DEST="$DEST_DIR/$ID"

mkdir -p "$DEST_DIR"
rm -rf "$DEST"
ln -s "$SRC" "$DEST"          # симлінк: правки у репо одразу підхоплюються
echo "✅ Встановлено: $DEST -> $SRC"

if [ ! -d "$WALLPAPERS" ]; then
    echo "⚠️ Теки $WALLPAPERS немає — встанови шлях вручну в налаштуваннях шпалери."
fi

# Активувати плагін на всіх десктопах і вписати шлях до кадрів через Plasma
# scripting. Шлях передаємо через змінну, щоб не ламати лапки.
if command -v qdbus6 >/dev/null 2>&1; then QDBUS=qdbus6; else QDBUS=qdbus; fi
"$QDBUS" org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript "
  var path = '$WALLPAPERS';
  var ds = desktops();
  for (var i = 0; i < ds.length; i++) {
      ds[i].wallpaperPlugin = '$ID';
      ds[i].currentConfigGroup = ['Wallpaper', '$ID', 'General'];
      ds[i].writeConfig('Folder', path);
  }
" >/dev/null 2>&1 && echo "✅ Активовано на всіх робочих столах (Folder = $WALLPAPERS)." \
  || echo "ℹ️ Не вдалось активувати автоматично — обери «Adaptive Coffee» у System Settings → Wallpaper та вкажи теку $WALLPAPERS."

echo "Готово. Якщо плагіна не видно — перезапусти оболонку:  systemctl --user restart plasma-plasmashell"
