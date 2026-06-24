#!/usr/bin/env python3
"""Збирає слайдшоу-відео з 48 шпалер із плавним crossfade між кадрами.

Кадри беруться в порядку нумерації (01..48 = сезон×час×погода), тож відео
плавно проходить зиму→весну→літо→осінь і ранок→ніч.

Приклади:
    python scripts/make_video.py                      # дефолт: зміна ~1.5с, фейд 0.6с, 1080p
    python scripts/make_video.py --interval 1.0 --fade 0.5
    python scripts/make_video.py --size 2752x1536 --fps 60 --out slideshow_4k.mp4

Потрібен ffmpeg у PATH.
"""
import argparse
import subprocess
import sys
from pathlib import Path

WALLPAPERS = Path(__file__).resolve().parent.parent / "wallpapers"


def frames() -> list[Path]:
    fs = sorted(WALLPAPERS.glob("[0-9][0-9]_*.png"))
    if not fs:
        sys.exit(f"❌ Немає кадрів у {WALLPAPERS}")
    return fs


def build_cmd(fs, w, h, fps, interval, fade, out) -> list[str]:
    dur = interval + fade                 # тривалість входу на кадр
    cmd = ["ffmpeg", "-y"]
    for f in fs:
        cmd += ["-loop", "1", "-t", f"{dur:.3f}", "-i", str(f)]

    # нормалізація кожного входу: заповнити кадр (crop), потрібний fps/формат
    parts = []
    for i in range(len(fs)):
        parts.append(
            f"[{i}:v]scale={w}:{h}:force_original_aspect_ratio=increase,"
            f"crop={w}:{h},setsar=1,fps={fps},format=yuv420p[v{i}]")

    # ланцюг xfade: offset_k = k*interval
    prev = "v0"
    for i in range(1, len(fs)):
        out_lbl = f"x{i}" if i < len(fs) - 1 else "vout"
        off = i * interval
        parts.append(
            f"[{prev}][v{i}]xfade=transition=fade:duration={fade:.3f}:"
            f"offset={off:.3f}[{out_lbl}]")
        prev = out_lbl

    cmd += ["-filter_complex", ";".join(parts), "-map", "[vout]",
            "-c:v", "libx264", "-crf", "20", "-preset", "medium",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)]
    return cmd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=float, default=1.5,
                    help="секунд між переходами (зміна кадру), типово 1.5")
    ap.add_argument("--fade", type=float, default=0.6,
                    help="тривалість crossfade у секундах, типово 0.6")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--size", default="1920x1080", help="ШxВ, типово 1920x1080")
    ap.add_argument("--out", default="wallpapers_slideshow.mp4")
    args = ap.parse_args()

    w, h = (int(x) for x in args.size.lower().split("x"))
    fs = frames()
    total = len(fs) * args.interval + args.fade
    out = Path(args.out).resolve()
    print(f"🎞️  {len(fs)} кадрів → {out.name}  "
          f"({w}x{h}@{args.fps}, зміна кожні {args.interval}с, "
          f"фейд {args.fade}с, ~{total:.0f}с)")

    cmd = build_cmd(fs, w, h, args.fps, args.interval, args.fade, out)
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        sys.exit("❌ ffmpeg не знайдено в PATH.")
    except subprocess.CalledProcessError as e:
        sys.exit(f"❌ ffmpeg завершився з помилкою ({e.returncode}).")
    print(f"✅ Готово: {out}")


if __name__ == "__main__":
    main()
