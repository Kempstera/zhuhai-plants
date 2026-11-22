#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成分享卡片 assets/og/<slug>.jpg（1080×1080）。

为什么需要：原来 84 个物种页共用一张 assets/og.png，转发香樟和转发簕杜鹃
出去的卡片长得一模一样 —— 没有辨识度，也就没人愿意再转第二次。

为什么用实景照片：图版（assets/img/opt/*.webp）是植物学插画，风格统一但
「不像你在路边看到的那棵」。分享到群里，实景照的点击率更高。

为什么是正方形：微信转发卡片的缩略图是居中裁成 1:1 的，横图会被切掉两侧。
这里用「同图模糊铺底 + 原图完整居中」，任何比例都不会裁坏主体。

可重复运行：已存在且比源图新的会跳过，`--force` 强制重做。
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIELD = os.path.join(ROOT, "assets", "img", "field")
PLATE = os.path.join(ROOT, "assets", "img", "opt")
OUT = os.path.join(ROOT, "assets", "og")

S = 1080
FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"
BRAND = "珠海草木志 · FLORA OF ZHUHAI"

INK = (248, 245, 236)
DIM = (216, 208, 190)


def font(size):
    return ImageFont.truetype(FONT, size, index=0)


def cover(im, size):
    w, h = im.size
    r = max(size / w, size / h)
    im = im.resize((max(size, round(w * r)), max(size, round(h * r))), Image.LANCZOS)
    left, top = (im.width - size) // 2, (im.height - size) // 2
    return im.crop((left, top, left + size, top + size))


def shade(im, frac=0.46, strength=232):
    mask = Image.new("L", (1, S), 0)
    px = mask.load()
    start = int(S * (1 - frac))
    for y in range(S):
        if y >= start:
            t = (y - start) / max(1, S - start)
            px[0, y] = int(strength * (t ** 1.6))
    mask = mask.resize((S, S))
    im.paste(Image.new("RGB", (S, S), (10, 16, 12)), (0, 0), mask)
    return im


def wrap_cjk(text, f, maxw, draw):
    out, line = [], ""
    for ch in text:
        if draw.textlength(line + ch, font=f) <= maxw:
            line += ch
        else:
            out.append(line)
            line = ch
    if line:
        out.append(line)
    return out


def render(src, dst, name, latin, kicker):
    base = Image.open(src).convert("RGB")

    bg = cover(base, S).filter(ImageFilter.GaussianBlur(52))
    bg = Image.eval(bg, lambda v: int(v * 0.66))

    r = min(S / base.width, S / base.height)
    fg = base.resize((max(1, round(base.width * r)), max(1, round(base.height * r))),
                     Image.LANCZOS)
    canvas = bg.copy()
    canvas.paste(fg, ((S - fg.width) // 2, max(0, (S - fg.height) // 2 - 46)))

    canvas = shade(canvas)
    d = ImageDraw.Draw(canvas)

    f_name, f_latin, f_small = font(78), font(30), font(21)

    if latin:
        d.text((72, S - 78), latin, font=f_latin, fill=DIM, anchor="ls")
    if name:
        lines = wrap_cjk(name, f_name, S - 148, d)
        for i, line in enumerate(reversed(lines)):
            d.text((70, S - 130 - i * 88), line, font=f_name, fill=INK, anchor="ls")

    if kicker:
        d.text((72, 66), kicker, font=f_small, fill=(226, 219, 202))

    bw = d.textlength(BRAND, font=f_small)
    d.text((S - 72 - bw, 62), BRAND, font=f_small, fill=(238, 232, 219))
    d.line([(S - 72 - bw, 94), (S - 72, 94)], fill=(168, 178, 164), width=1)

    canvas.save(dst, "JPEG", quality=84, optimize=True, progressive=True)


def main():
    force = "--force" in sys.argv
    os.makedirs(OUT, exist_ok=True)

    data = json.load(open(os.path.join(ROOT, "data", "plants.json")))
    plants = data["plants"]
    cats = {c["id"]: c["name"] for c in data["categories"]}
    photos = json.load(open(os.path.join(ROOT, "data", "photos.json")))

    made = skipped = failed = 0
    for p in plants:
        slug = p["slug"]
        cand = []
        for ph in photos.get(slug, []) or []:
            cand.append(os.path.join(FIELD, ph["file"]))
        cand.append(os.path.join(PLATE, "%s.webp" % slug))
        src = next((c for c in cand if os.path.exists(c)), None)
        if not src:
            failed += 1
            continue
        dst = os.path.join(OUT, "%s.jpg" % slug)
        if not force and os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
            skipped += 1
            continue
        try:
            kicker = "No. %s · %s" % (p.get("no", ""), cats.get(p.get("cat"), ""))
            render(src, dst, p["name"], p["latin"], kicker)
            made += 1
        except Exception as ex:
            failed += 1
            print("  ! %s: %s" % (slug, ex))
    print("分享图：新建 %d，跳过 %d，失败 %d" % (made, skipped, failed))


if __name__ == "__main__":
    main()
