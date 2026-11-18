#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把珠海市行政区划边界（GeoJSON，GCJ-02）压成站点用的小体积多边形。

    python3 tools/prep_geo.py 路径/440400_full.json

数据来源：阿里云 DataV.GeoAtlas 行政区划边界（民政部区划底图），
坐标为 GCJ-02。本脚本只做投影、抽稀与取整，不改动界线本身。

输出 data/geo.json：
    {"w": 1000, "h": 496.8,
     "transform": {"lon0":…, "lat1":…, "kx":…, "scale":…},
     "districts": [{"name": "香洲区", "polys": [[[x,y],…], …]}, …]}
坐标已是 viewBox 单位（0–1000），保留一位小数。
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIDTH = 1000.0
EPS = 0.32          # 抽稀阈值，单位：viewBox 像素


def rings(geom):
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in polys:
        yield poly[0]


def dp(points, eps):
    """Douglas–Peucker 线段抽稀"""
    if len(points) < 3:
        return points
    ax, ay = points[0]
    bx, by = points[-1]
    dx, dy = bx - ax, by - ay
    norm = math.hypot(dx, dy)
    best, idx = -1.0, -1
    for i in range(1, len(points) - 1):
        px, py = points[i]
        if norm == 0:
            d = math.hypot(px - ax, py - ay)
        else:
            d = abs(dy * px - dx * py + bx * ay - by * ax) / norm
        if d > best:
            best, idx = d, i
    if best <= eps:
        return [points[0], points[-1]]
    left = dp(points[:idx + 1], eps)
    right = dp(points[idx:], eps)
    return left[:-1] + right


def main():
    src = Path(sys.argv[1])
    data = json.loads(src.read_text(encoding="utf-8"))

    lons, lats = [], []
    for f in data["features"]:
        for r in rings(f["geometry"]):
            for x, y in r:
                lons.append(x)
                lats.append(y)
    lon0, lon1 = min(lons), max(lons)
    lat0, lat1 = min(lats), max(lats)

    latm = (lat0 + lat1) / 2
    kx = math.cos(math.radians(latm))
    span_x = (lon1 - lon0) * kx
    span_y = lat1 - lat0
    scale = WIDTH / span_x
    height = round(span_y * scale, 1)

    def project(lon, lat):
        return ((lon - lon0) * kx * scale, (lat1 - lat) * scale)

    out = []
    total = 0
    for f in data["features"]:
        name = f["properties"]["name"]
        polys = []
        for r in rings(f["geometry"]):
            pts = [project(x, y) for x, y in r]
            pts = dp(pts, EPS)
            if len(pts) < 3:
                continue
            polys.append([[round(x, 1), round(y, 1)] for x, y in pts])
            total += len(pts)
        out.append({"name": name, "polys": polys})

    dst = ROOT / "data" / "geo.json"
    dst.write_text(json.dumps({
        "w": WIDTH,
        "h": height,
        "transform": {"lon0": lon0, "lat1": lat1, "kx": kx, "scale": scale},
        "districts": out,
    }, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{dst.name}: {len(out)} districts, {total} pts, {dst.stat().st_size/1024:.1f} KB, "
          f"bbox {lon0:.4f},{lat0:.4f} – {lon1:.4f},{lat1:.4f}, viewBox 1000×{height}")


if __name__ == "__main__":
    main()
