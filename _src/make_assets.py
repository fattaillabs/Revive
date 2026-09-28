#!/usr/bin/env python3
"""Revive 랜딩 이미지 만들기 — 원본(옆 레포들)에서 assets/ 를 다시 뽑는다.

  python3 _src/make_assets.py

원본:
  키 비주얼(세로)  _src/kv-portrait-source.jpg — 앱 온보딩 그림에서 공중전화 부스·수화기·전화선을 걷어내고
                   창가에서 폰을 든 장면으로 바꾼 것(2026-09-06 광고 A컷, 전화선 배선이 어색하다는 지적으로)
  키 비주얼(가로)  _src/kv-wide-source.png — 위 세로 그림을 codex 이미지 편집으로 16:9 로 넓힌 것(2026-09-29)
  단계 그림        revive-promo/assets/revive-shot4*.png (내보내기·공유 시트)
                   revive-promo/screenshots/raw-<lang>/{import,chat}.png (앱 실화면, 언어별 촬영본)
  아이콘           ReviveAndroid/tools/store/play_icon_512.png

손으로 그린 그림은 없다(생성 이미지와 실화면만). 이 레포는 공개라 앱 소스는 절대 넣지 않는다 —
여기엔 결과 이미지만 들어간다.
"""
import os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEV = os.path.dirname(ROOT)
OUT = os.path.join(ROOT, "assets")
LANGS = ["en", "ko", "ja", "de", "fr", "es", "it", "pt"]


def src(*p):
    return os.path.join(DEV, *p)


def fit_w(im, w):
    return im if im.width <= w else im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)


def webp(im, name, q=80):
    path = os.path.join(OUT, name)
    im.convert("RGB").save(path, "WEBP", quality=q, method=6)
    print("%-22s %4dx%-4d %6.1f KB" % (name, im.width, im.height, os.path.getsize(path) / 1024))


def crop45(im, top):
    """폭 그대로 4:5 로 자른다. top=True 면 위쪽, False 면 아래쪽."""
    h = round(im.width * 5 / 4)
    y = 0 if top else im.height - h
    return im.crop((0, y, im.width, y + h))


os.makedirs(OUT, exist_ok=True)

# ── 키 비주얼 ──
wide = Image.open(os.path.join(HERE, "kv-wide-source.png")).convert("RGB")
webp(wide, "kv-wide.webp", 82)
webp(fit_w(wide, 960), "kv-wide-960.webp", 80)
portrait = Image.open(os.path.join(HERE, "kv-portrait-source.jpg")).convert("RGB")
webp(fit_w(portrait, 1024), "kv-portrait.webp", 82)
webp(fit_w(portrait, 720), "kv-portrait-720.webp", 80)

# OG 1200x630 — 가로 그림에서 인물과 달이 가운데 오게
W, H = 1200, 630
scale = H / wide.height * 1.08
big = wide.resize((round(wide.width * scale), round(wide.height * scale)), Image.LANCZOS)
cx = round(big.width * 0.66)
x0 = max(0, min(big.width - W, cx - W // 2))
y0 = round((big.height - H) * 0.45)
og = big.crop((x0, y0, x0 + W, y0 + H))
og.save(os.path.join(OUT, "og.jpg"), "JPEG", quality=86, optimize=True, progressive=True)
print("og.jpg", og.size)

# ── 단계 그림 ──
webp(fit_w(Image.open(src("revive-promo", "assets", "revive-shot4a-export.png")), 720), "step-export.webp")
webp(fit_w(Image.open(src("revive-promo", "assets", "revive-shot4b-sharesheet.png")), 720), "step-share.webp")
for lang in LANGS:
    raw = os.path.join("revive-promo", "screenshots", "raw-" + lang)
    webp(fit_w(crop45(Image.open(src(raw, "chat.png")), top=True), 720), "step-chat-%s.webp" % lang)
    if lang in ("ko", "ja"):     # 카카오톡·LINE 내보내기 안내가 그 언어로 찍혀 있다
        webp(fit_w(crop45(Image.open(src(raw, "import.png")), top=False), 720), "step-import-%s.webp" % lang)

# ── 아이콘 ──
icon = Image.open(src("ReviveAndroid", "tools", "store", "play_icon_512.png")).convert("RGBA")
for size, name in [(96, "icon-96.png"), (180, "apple-touch-icon.png"), (192, "icon-192.png"), (32, "favicon-32.png")]:
    icon.resize((size, size), Image.LANCZOS).save(os.path.join(OUT, name), optimize=True)
icon.resize((48, 48), Image.LANCZOS).save(os.path.join(OUT, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])
print("icons done")
