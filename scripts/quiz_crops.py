#!/usr/bin/env python3
"""算出「看图认植物」每一格该取哪个部位。

问题：首页小测要展示一张放大的局部图，让人猜是哪一种。但 84 张实景照
构图各异，固定的居中裁切经常切到天空、水面或柏油路——放大之后是一片
纯色，谁都猜不出来，题目就白出了。

做法：把每张图按 2 倍焦距切成 5×5 共 25 个候选窗口，各自算一次边缘强度
（灰度取边缘后求标准差），取最强的那一格。叶片、枝条、花序这些有纹理的
区域分数高，纯色天空和路面分数低，于是自动避开。

结果写进 data/quiz_crops.json。build.py 只读这个文件，构建时不依赖 PIL，
也不用每次都重算（84 张 × 25 格，重算是分钟级的）。

改图之后重跑一次：
    python3 scripts/quiz_crops.py
"""

import json
import os

from PIL import Image, ImageFilter, ImageStat

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZOOM = 2.0                       # 裁切倍率：放大到 2 倍焦距
GRID = (0, 25, 50, 75, 100)      # background-position 的百分比候选
OUT = os.path.join(ROOT, "data", "quiz_crops.json")


def plant_ratio(rgb):
    """这个窗口里「像植物」的像素占多少。

    只按饱和度算不行：蓝天也很艳，一格里有半格天空，照样能拿高分。所以
    先按规则排除掉不像植被的颜色——
      · 灰的（饱和度低）：树皮、石头、柏油路、水泥墙；
      · 蓝的：天空、水面；
      · 太暗的：树荫里的死黑。
    剩下的就是叶和花。缩到 48×48 再数，够用而且快。
    """
    small = rgb.resize((48, 48))
    data = small.tobytes()          # 比 getdata() 快，也不触发新版 Pillow 的弃用警告
    total = len(data) // 3
    good = 0
    for i in range(0, len(data), 3):
        r, g, b = data[i], data[i + 1], data[i + 2]
        mx, mn = (r if r > g else g), (r if r < g else g)
        if b > mx:
            mx = b
        if b < mn:
            mn = b
        if mx < 40:
            continue
        if (mx - mn) / mx < 0.18:
            continue
        if b >= mx - 2 and b > r + 14:
            continue
        good += 1
    return good / float(total)


def score(im, xp, yp):
    """返回这个窗口的分数。数字越大，越适合拿来出题。

    窗口尺寸要跟 CSS 里实际显示的一模一样，否则算出来的「最佳位置」到了
    页面上是另一块地方。首页的方块是正方形，用的是：
        background-size: 200% auto   →  图宽画成 2 个方块宽
    那么方块里看到的，是原图中一块「边长为图宽一半」的正方形。
    纵向可移动的余量是 h - w/2，横向是 w/2，对应 background-position
    的 0–100%。

    评分 = 植被占比 × 100 + 边缘强度 × 0.3。

    主项是「像植物的像素」占多少：一张特写里花瓣很平，边缘强度反而低，
    拿边缘当主项会把最好的花朵特写排到最后。边缘只用来在同分时挑纹理多的
    那一个，避免选到一格里全是同一片平叶子的地方。
    """
    w, h = im.size
    side = w / ZOOM
    x = (w - side) * xp / 100.0
    y = (h - side) * yp / 100.0
    box = (int(x), int(y), int(x + side), int(y + side))
    rgb = im.crop(box).convert("RGB").resize((160, 160))
    edge = ImageStat.Stat(rgb.convert("L").filter(ImageFilter.FIND_EDGES)).stddev[0]
    ratio = plant_ratio(rgb)
    # 两个指标都要：像植物（ratio）＋ 有细节（edge）。只用前者，会把一整片
    # 远树的树冠排到最前面——满格都是绿的，但放大之后仍是一片模糊，认不出来。
    return ratio * 60 + min(edge, 90) * 0.8, ratio, edge


def main():
    photos = json.load(open(os.path.join(ROOT, "data", "photos.json"), encoding="utf-8"))
    plants = json.load(open(os.path.join(ROOT, "data", "plants.json"), encoding="utf-8"))["plants"]

    out = {}
    flat = []
    for p in plants:
        slug = p["slug"]
        shots = photos.get(slug) or []
        if not shots:
            continue
        rel = "assets/img/field/" + shots[0]["file"]
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            print("缺图：", rel)
            continue
        im = Image.open(path)
        best = max(((score(im, x, y), x, y) for x in GRID for y in GRID),
                   key=lambda r: r[0][0])
        (sc, ratio, edge), x, y = best
        out[slug] = {"x": x, "y": y, "score": round(sc, 1),
                     "ratio": round(ratio, 3), "edge": round(edge, 1),
                     "img": rel, "w": im.size[0], "h": im.size[1]}
        if ratio < 0.45 or edge < 40:
            flat.append(slug)

    json.dump(out, open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, sort_keys=True)
    print("写入 %s：%d 种" % (OUT, len(out)))
    if flat:
        print("细节偏少的（出题时避开）：%d 种" % len(flat))


if __name__ == "__main__":
    main()
