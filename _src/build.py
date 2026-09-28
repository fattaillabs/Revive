#!/usr/bin/env python3
"""Revive 랜딩 로케일 빌드.

원본은 둘: _src/template.html(구조·스타일·스크립트) + _src/i18n.json(8개 언어 카피·데모 대화).
언어마다 index.html, ko/index.html, ja/index.html … 을 써낸다. 배포 파일에는 그 언어 글만
들어가므로 JS 를 안 돌리는 크롤러도 그대로 읽는다.

  python3 _src/build.py          # 8개 페이지 + sitemap.xml 생성
  python3 _src/build.py --check  # 생성 결과가 현재 파일과 같은지만 확인

카피는 i18n.json 만 고치고 다시 빌드한다. 로케일 페이지를 직접 고치면 다음 빌드에서 덮어써진다.
`_src/` 는 GitHub Pages(Jekyll)가 게시하지 않는다(밑줄 폴더).

데모 대화는 언어마다 그 나라에서 쓰는 메신저의 실제 내보내기 형식이다 — 한국어는 카카오톡
(`2024년 3월 9일 오후 12:10, 엄마 : …`), 일본어는 LINE(시각·이름·본문), 나머지는 그 로케일의
WhatsApp 날짜 형식. 앱 파서 테스트(ReviveAndroid …/parser/*Test.kt)에 있는 형식만 쓴다.
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BASE_URL = "https://fattaillabs.com/Revive/"
APP_ID = "6759059883"
APP_STORE = "https://apps.apple.com/app/id%s" % APP_ID
PLAY_URL = None          # 구글 플레이 공개되면 "https://play.google.com/store/apps/details?id=com.fattail.revive"
PRIVACY_URL = BASE_URL + "revive-privacy.html"
FREE_DAILY = 10          # MissingYou SubscriptionManager.freeDailyMessageLimit 와 같아야 한다
LANG_ORDER = ["en", "ko", "ja", "de", "fr", "es", "it", "pt"]

SERIF_LATIN = '"Newsreader", "Iowan Old Style", Georgia, serif'
SANS_LATIN = '"Hanken Grotesk", "Helvetica Neue", Arial, sans-serif'
FONTS = {
    # 뉴스리더에는 한글·가나가 없다 — 라틴(Re:vive·숫자)은 뉴스리더, 나머지는 그 언어 명조
    "ko": ("&family=Gowun+Batang:wght@400;700",
           '"Newsreader", "Gowun Batang", "AppleMyungjo", serif',
           '-apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Noto Sans KR", "Malgun Gothic", sans-serif'),
    "ja": ("&family=Shippori+Mincho:wght@400;500",
           '"Newsreader", "Shippori Mincho", "Hiragino Mincho ProN", "Yu Mincho", serif',
           '-apple-system, BlinkMacSystemFont, "Hiragino Sans", "Noto Sans JP", "Yu Gothic", sans-serif'),
}


def page_url(cfg):
    return BASE_URL + cfg["dir"]


def attr(s):
    """속성 값용 — 태그를 벗기고 따옴표를 이스케이프."""
    return html.escape(re.sub(r"<[^>]+>", "", s), quote=True)


def jsonld(lang, cfg, locales):
    data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "MobileApplication",
                "name": "Re:vive",
                "alternateName": "Re:vive – AI Memory Chat",
                "operatingSystem": "iOS",
                "applicationCategory": "EntertainmentApplication",
                "description": cfg["ld_description"],
                "url": page_url(cfg),
                "inLanguage": [locales[l]["hreflang"] for l in LANG_ORDER],
                "installUrl": [APP_STORE] + ([PLAY_URL] if PLAY_URL else []),
                "image": BASE_URL + "assets/og.jpg",
                "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
                "publisher": {"@id": "https://fattaillabs.com/#org"},
            },
            {
                "@type": "Organization",
                "@id": "https://fattaillabs.com/#org",
                "name": "FatTail Labs",
                "alternateName": "팻테일랩스",
                "url": "https://fattaillabs.com/",
                "logo": "https://fattaillabs.com/images/FatTailLabs_Logo.png",
            },
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def build(lang, cfg, locales, tpl):
    base = "../" if cfg["dir"] else ""
    demo = cfg["demo"]

    raw_lines = "\n".join(
        '              <li data-i="%d">%s</li>' % (i, demo["raw_fmt"].format(
            stamp=html.escape(stamp), name=html.escape(demo["name"]), text=html.escape(text)))
        for i, (stamp, text) in enumerate(demo["lines"]))
    past = "\n".join('            <div class="b them past" data-m="%d">%s</div>' % (i, html.escape(text))
                     for i, (_, text) in enumerate(demo["lines"]))
    hreflang = "\n".join('<link rel="alternate" hreflang="%s" href="%s">' % (locales[l]["hreflang"], page_url(locales[l]))
                         for l in LANG_ORDER)
    hreflang += '\n<link rel="alternate" hreflang="x-default" href="%s">' % BASE_URL
    og_alt = "\n".join('<meta property="og:locale:alternate" content="%s">' % locales[l]["og_locale"]
                       for l in LANG_ORDER if l != lang)
    lang_links = "\n".join(
        '      <li><a href="%s" hreflang="%s" lang="%s"%s>%s</a></li>' % (
            (base + locales[l]["dir"]) or "./", locales[l]["hreflang"], locales[l]["html_lang"],
            ' aria-current="page"' if l == lang else "", locales[l]["label"])
        for l in LANG_ORDER)

    if PLAY_URL:
        android_hero = '<a class="btn ghost" href="%s">Google Play</a>' % PLAY_URL
        android_end = android_hero
    else:
        android_hero = '<span class="btn ghost">Android <small>%s</small></span>' % cfg["soon"]
        android_end = '<span class="btn ghost">Google Play <small>%s</small></span>' % cfg["soon"]

    extra, serif, sans = FONTS.get(lang, ("", SERIF_LATIN, SANS_LATIN))
    blocks = {
        "HREFLANG": hreflang, "OG_ALTERNATES": og_alt, "JSONLD": jsonld(lang, cfg, locales),
        "RAW_LINES": raw_lines, "PAST_BUBBLES": past, "LANG_LINKS": lang_links,
        "ANDROID_HERO": android_hero, "ANDROID_END": android_end,
        "FONT_EXTRA": extra, "FONT_SERIF": serif, "FONT_SANS": sans,
        "APP_ID": APP_ID, "APP_STORE": APP_STORE, "PRIVACY_URL": PRIVACY_URL, "BASE_URL": BASE_URL,
        "LANG": lang, "LANG_CODE": lang.upper(), "base": base, "url": page_url(cfg),
    }
    # 메타(속성)에 들어가는 값은 태그 없는 평문
    plain = {"title", "description", "og_title", "og_description", "kv_alt", "mem_aria", "raw_aria",
             "step1_alt", "step2_alt", "step3_alt", "langs_label"}

    def sub(m):
        key = m.group(1)
        if key in blocks:
            return blocks[key]
        if key.startswith("demo."):
            return html.escape(demo[key[5:]])
        val = cfg[key]
        if not isinstance(val, str):
            raise KeyError(key)
        val = val.replace("{free}", str(FREE_DAILY))
        return attr(val) if key in plain else val

    out = re.sub(r"\{\{([A-Za-z0-9_.]+)\}\}", sub, tpl)
    assert "{{" not in out and "{free}" not in out, lang
    return out


def sitemap(locales):
    rows = []
    for l in LANG_ORDER:
        alts = "\n".join('    <xhtml:link rel="alternate" hreflang="%s" href="%s"/>' % (locales[a]["hreflang"], page_url(locales[a]))
                         for a in LANG_ORDER)
        alts += '\n    <xhtml:link rel="alternate" hreflang="x-default" href="%s"/>' % BASE_URL
        rows.append("  <url>\n    <loc>%s</loc>\n%s\n  </url>" % (page_url(locales[l]), alts))
    rows.append("  <url>\n    <loc>%s</loc>\n  </url>" % PRIVACY_URL)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
            + "\n".join(rows) + "\n</urlset>\n")


if __name__ == "__main__":
    locales = json.load(open(os.path.join(HERE, "i18n.json")))
    tpl = open(os.path.join(HERE, "template.html")).read()
    check = "--check" in sys.argv
    outputs = {os.path.join(ROOT, locales[l]["dir"], "index.html"): build(l, locales[l], locales, tpl) for l in LANG_ORDER}
    outputs[os.path.join(ROOT, "sitemap.xml")] = sitemap(locales)
    dirty = 0
    for path, out in outputs.items():
        cur = open(path).read() if os.path.exists(path) else None
        if check:
            if cur != out:
                dirty += 1
                print("stale:", os.path.relpath(path, ROOT))
        else:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            open(path, "w").write(out)
            print("wrote", os.path.relpath(path, ROOT), len(out.encode()), "bytes")
    if check:
        print("up to date" if not dirty else "%d stale" % dirty)
        sys.exit(1 if dirty else 0)
