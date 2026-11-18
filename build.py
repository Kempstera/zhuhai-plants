#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""珠海草木志 · static site builder"""
import json, os, math, shutil
from pathlib import Path

ROOT = Path(__file__).parent
DATA = json.loads((ROOT / "data" / "plants.json").read_text(encoding="utf-8"))
OUT = ROOT / "dist"

META = DATA["meta"]
CATS = DATA["categories"]
PLANTS = DATA["plants"]
ARCHIVE = DATA["archive"]
PHOTO_FILE = ROOT / "data" / "photos.json"
PHOTOS = json.loads(PHOTO_FILE.read_text(encoding="utf-8")) if PHOTO_FILE.exists() else {}
CATMAP = {c["id"]: c for c in CATS}

SITE = "https://plants.signupeverywhere.cc"

SITE = "https://plants.signupeverywhere.cc"

ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]

# ---------------------------------------------------------------- helpers


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def flower_text(months):
    if not months:
        return "——"
    if len(months) == 12:
        return "全年"
    if len(months) >= 8:
        return f"{months[0]}–{months[-1]} 月"
    groups, cur = [], [months[0]]
    for m in months[1:]:
        if m == cur[-1] + 1:
            cur.append(m)
        else:
            groups.append(cur)
            cur = [m]
    groups.append(cur)
    out = []
    for g in groups:
        out.append(str(g[0]) if len(g) == 1 else f"{g[0]}–{g[-1]}")
    return "、".join(out) + " 月"


def nav(prefix, active):
    items = [
        ("", "封面", "home"),
        ("atlas", "图鉴", "atlas"),
        ("calendar", "花历", "calendar"),
        ("map", "分布", "map"),
        ("roster", "名录", "roster"),
        ("about", "关于", "about"),
    ]
    lis = []
    for href, label, key in items:
        cls = ' class="is-active"' if key == active else ""
        lis.append(f'<a href="{prefix}{href}"{cls}>{label}</a>')
    return "\n        ".join(lis)


def palm_svg():
    """程序化羽状叶线描（右上角装饰）"""
    paths = []
    # 中轴
    paths.append('<path d="M 0 0 C 40 60 70 150 78 260" />')
    # 羽片
    for i in range(22):
        t = i / 21.0
        x = 4 + 78 * t ** 1.6
        y = 8 + 250 * t
        ln = 74 * (1 - 0.55 * t) * (0.5 + 0.5 * math.sin(math.pi * min(1, t * 1.15)))
        for sgn in (-1, 1):
            dx = sgn * ln * 0.92
            dy = ln * 0.55 + 10 * t
            paths.append(
                f'<path d="M {x:.1f} {y:.1f} Q {x+dx*0.45:.1f} {y+dy*0.25:.1f} {x+dx:.1f} {y+dy:.1f}" />'
            )
            paths.append(
                f'<path d="M {x:.1f} {y:.1f} Q {x+dx*0.45:.1f} {y+dy*0.75:.1f} {x+dx*0.86:.1f} {y+dy*1.28:.1f}" />'
            )
    return (
        '<svg class="hero__canvas" viewBox="0 0 420 420" fill="none" '
        'stroke="#3D5C4D" stroke-width="0.9" stroke-linecap="round" '
        'xmlns="http://www.w3.org/2000/svg" aria-hidden="true" '
        'style="left:auto;right:-100px;top:-170px;width:660px;height:660px;transform:rotate(12deg)">'
        + "".join(paths)
        + "</svg>"
    )


def head(title, prefix, desc, active, path="/", extra_css=""):
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="theme-color" content="#F8F4EB">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="珠海草木志">
<meta property="og:locale" content="zh_CN">
<meta property="og:url" content="{SITE}{path}">
<meta property="og:image" content="{SITE}/assets/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{SITE}{path}">
<link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{prefix}assets/css/style.css">
{extra_css}
</head>
<body>
<header class="site-head">
  <div class="site-head__inner">
    <a class="brand" href="{prefix}">
      <span class="brand__name">珠海草木志</span>
      <span class="brand__latin">Flora of Zhuhai</span>
    </a>
    <nav class="nav">
        {nav(prefix, active)}
    </nav>
  </div>
</header>
"""


def foot(prefix):
    return f"""
<footer class="site-foot">
  <div class="wrap">
    <div class="foot__grid">
      <div>
        <h3 class="foot__title">珠海草木志</h3>
        <p class="foot__p">一份关于南亚热带滨海城市的植物观察笔记。收录珠海街头、公园与海岸线上最寻常、也最容易被忽略的七十余种植物。</p>
      </div>
      <div>
        <div class="foot__k">BROWSE</div>
        <div class="foot__links">
          <a href="{prefix}atlas">图鉴总览</a>
          <a href="{prefix}calendar">十二月花历</a>
          <a href="{prefix}map">分布示意</a>
          <a href="{prefix}roster">补充名录</a>
          <a href="{prefix}about">编例与说明</a>
        </div>
      </div>
      <div>
        <div class="foot__k">NOTE</div>
        <div class="foot__links">
          <span style="color:var(--ink-faint);font-size:13.5px;line-height:1.9">花期因年份、纬度和局部小气候而异，文中月份为珠海城区的常见区间。插图均为风格化植物图谱，用于辨识形态要点，非实景照片。</span>
        </div>
      </div>
    </div>
    <div class="foot__end">
      <span>珠海 · 北纬 22°14′ — 22°37′</span>
      <span>共 {len(PLANTS)} 种详解 · {len(ARCHIVE)} 种著录</span>
    </div>
  </div>
</footer>
<script src="{prefix}assets/js/site.js"></script>
</body>
</html>
"""


# ---------------------------------------------------------------- 卡片

def card_html(p, prefix="/", show_lead=True):
    cat = CATMAP[p["cat"]]
    img = f'{prefix}assets/img/{p["slug"]}.webp'
    lead = f'<p class="card__lead">{esc(p["lead"])}</p>' if show_lead else ""
    return f"""      <a class="card reveal" href="{prefix}species/{p['slug']}" data-cat="{p['cat']}" data-months="{','.join(map(str, p['months']))}" data-name="{esc(p['name'])} {esc(p['latin'])} {esc(p['alias'])} {esc(p['family'])}">
        <div class="card__plate">
          <img src="{img}" alt="{esc(p['name'])}（{esc(p['latin'])}）植物图谱" loading="lazy" width="900" height="1125">
        </div>
        <div class="card__body">
          <div class="card__no">No. {p['no']} · {cat['name']}</div>
          <h3 class="card__name">{esc(p['name'])}</h3>
          <div class="card__latin">{esc(p['latin'])}</div>
          {lead}
          <div class="card__foot">
            <span>花期 {flower_text(p['months'])}</span>
            <span>{esc(p['family'])}</span>
          </div>
        </div>
      </a>"""


# ---------------------------------------------------------------- 首页

def build_index():
    # 花历统计
    by_month = {m: [] for m in range(1, 13)}
    for p in PLANTS:
        for m in p["months"]:
            by_month[m].append(p)
    maxn = max(len(v) for v in by_month.values())

    cols = []
    for m in range(1, 13):
        n = len(by_month[m])
        pct = int(round(n / maxn * 100))
        cols.append(
            f"""      <div class="almanac__col" data-month="{m}" role="button" tabindex="0" aria-label="{m} 月花历，{n} 种植物开花">
        <div class="almanac__m">{ROMAN[m-1]}</div>
        <div class="almanac__plot"><span style="height:{pct}%"></span></div>
        <div class="almanac__n">{n}</div>
      </div>"""
        )

    # 五卷
    vols = []
    for c in CATS:
        ps = [p for p in PLANTS if p["cat"] == c["id"]]
        vols.append(
            f"""      <a class="volume__row reveal" href="/atlas?cat={c['id']}">
        <div class="volume__no">{c['no']}</div>
        <div>
          <h3 class="volume__name">{c['name']}</h3>
          <p class="volume__lead">{c['lead']}</p>
        </div>
        <div class="volume__count">{len(ps):02d} <span>SPECIES</span></div>
      </a>"""
        )

    # 精选
    picks = ["delonix-regia", "ficus-microcarpa", "plumeria-rubra", "mangifera-indica",
             "bauhinia-blakeana", "handroanthus-chrysanthus", "bombax-ceiba",
             "roystonea-regia", "bougainvillea-spectabilis", "ixora-chinensis"]
    pickmap = {p["slug"]: p for p in PLANTS}
    cards = "\n".join(card_html(pickmap[s], show_lead=False) for s in picks)

    stats = f"""        <div><b>{len(PLANTS) + len(ARCHIVE)}</b>收录物种</div>
        <div><b>{len(CATS)}</b>分卷</div>
        <div><b>22.5℃</b>年均气温</div>
        <div><b>2,300</b>日照小时</div>"""

    html = head(
        "珠海草木志 · 一座南亚热带城市的植物观察",
        "/", "珠海常见行道树、绿化带植物与园林花卉图鉴。细叶榕的荫凉、凤凰木的火、簕杜鹃的市中花色，六十余种草木的形态、花期与故事。",
        "home", "/")
    html += palm_svg()
    html += f"""
<main>
  <section class="hero">
    <div class="wrap hero__inner">
      <div class="hero__line">
        <span class="tick"></span>
        <span class="eyebrow">Zhuhai · Guangdong<span class="hide-sm"> · 22°16′N 113°34′E</span></span>
      </div>
      <h1>海风经过的地方，<br>草木替城市<em>记着节令</em>。</h1>
      <p class="hero__sub">珠海是一座长在植物里的城市。北回归线以南、伶仃洋以西，长夏无冬，雨热同期——于是榕树的气根垂成帘，凤凰木在五月点着整条街，簕杜鹃从天桥一路开到海堤。这里收录它们当中的七十余种：行道树、绿篱灌木、地被草花，与海岸线上的棕榈。</p>
      <div class="hero__latin">Sub-tropical monsoon, evergreen all year round.</div>
      <div class="hero__meta">
{stats}
      </div>
    </div>
  </section>

  <section class="section section--tight">
    <div class="wrap">
      <div class="section__head">
        <div>
          <div class="eyebrow">Contents</div>
          <h2>五卷</h2>
        </div>
        <p>依植物在城中承担的角色而分，而非严格的分类学。同一种树，可能既是行道树，也是夏天的花。</p>
      </div>
      <div class="volume">
{chr(10).join(vols)}
      </div>
    </div>
  </section>

  <section class="section">
    <div class="wrap">
      <div class="section__head">
        <div>
          <div class="eyebrow">Almanac of Bloom</div>
          <h2>十二月花历</h2>
        </div>
        <p>点选月份，查看当月开花的物种。南方的花期不以春天为限——真正的空档，其实只有八月的台风天。</p>
      </div>
      <div class="almanac">
{chr(10).join(cols)}
      </div>
      <div style="margin-top:30px;display:flex;justify-content:flex-end">
        <a href="/calendar" class="chip" style="padding:10px 24px;font-size:12.5px">查 看 完 整 花 历 &nbsp;→</a>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="wrap">
      <div class="section__head">
        <div>
          <div class="eyebrow">Selected</div>
          <h2>十种读懂珠海的方式</h2>
        </div>
        <p>如果只有半天时间认识这座城市的植物，从这里开始。</p>
      </div>
      <div class="grid">
{cards}
      </div>
    </div>
  </section>

  <section class="section section--tight">
    <div class="wrap">
      <div class="section__head">
        <div>
          <div class="eyebrow">On the City</div>
          <h2>为什么是这些植物</h2>
        </div>
        <p>风、盐、雨、热——四种力量共同筛选出珠海的行道树名单。</p>
      </div>
      <div style="display:grid;grid-template-columns:1fr;gap:28px;max-width:760px;font-size:16px;line-height:2.05;color:var(--ink-soft)">
        <p style="margin:0">珠海地处南亚热带季风气候区，年均气温约 22.5℃，年降水量 1,700–2,300 毫米，全年无霜。夏季漫长而湿热，冬季短暂温和，加之濒临南海，每年平均受 3–4 个热带气旋影响。这样的气候给植物出了一道苛刻的考题：既要耐得住长时间的高温高湿，又要在台风过境时不被连根拔起；既要扛住海风的盐雾，也要适应填海地带偏碱、偏浅的土层。</p>
        <p style="margin:0">于是名单被反复筛过。榕属以气生根与柔韧的枝干胜出，樟科以深根与芳香油脂胜出，棕榈科以能屈能伸的羽叶胜出。凤凰木、木棉、黄花风铃木则代表了另一种策略：在风季到来之前完成开花结实，把一年中最好的几周押在一个短促的季节里。</p>
        <p style="margin:0">这座城市的绿，因此不是一种颜色，而是一套被气候反复修改过的答案。</p>
      </div>
    </div>
  </section>

  <section class="section section--tight">
    <div class="wrap" style="border-top:1px solid var(--rule);padding-top:44px;display:flex;flex-wrap:wrap;gap:24px;justify-content:space-between;align-items:center">
      <div>
        <div class="eyebrow">Appendix</div>
        <h2 style="margin:10px 0 6px;font-size:26px;font-weight:400;letter-spacing:.08em">还有 {len(ARCHIVE)} 种，著录于名录</h2>
        <p style="margin:0;font-size:14px;color:var(--ink-faint)">白兰、黄槿、海南蒲桃、苏铁、睡莲……按音序排列。</p>
      </div>
      <a href="/roster" class="chip" style="padding:12px 26px;font-size:13px">翻 阅 名 录 &nbsp;→</a>
    </div>
  </section>
</main>
"""
    html += foot("/")
    (OUT / "index.html").write_text(html, encoding="utf-8")


# ---------------------------------------------------------------- 图鉴

def build_atlas():
    cards = "\n".join(card_html(p) for p in PLANTS)
    chips = ['<button class="chip is-on" data-cat="all">全部</button>']
    for c in CATS:
        chips.append(f'<button class="chip" data-cat="{c["id"]}">{c["name"]}</button>')

    html = head("图鉴总览 · 珠海草木志", "/", f"珠海常见园林植物图鉴，共 {len(PLANTS)} 种详解，可按类别、花期与名称检索。", "atlas", "/atlas")
    html += f"""
<main>
  <section class="section section--tight" style="padding-bottom:28px">
    <div class="wrap">
      <div class="eyebrow">Atlas</div>
      <h1 style="margin:12px 0 14px;font-size:clamp(32px,5vw,52px);font-weight:400;letter-spacing:.1em">图鉴总览</h1>
      <p style="margin:0;max-width:600px;font-size:15.5px;line-height:2;color:var(--ink-soft)">{len(PLANTS)} 种详解，每一种都附有形态图谱、花期区间、实景摄影与在珠海的具体观察位置。按类别筛选，或直接输入名字。</p>
    </div>
  </section>

  <div class="filters">
    <div class="wrap filters__inner">
      {''.join(chips)}
      <div class="search">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color:var(--ink-faint);flex:none"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/></svg>
        <input type="search" id="q" placeholder="搜索名称 / 学名 / 科属" aria-label="搜索植物">
      </div>
    </div>
  </div>

  <section class="section" style="padding-top:44px">
    <div class="wrap">
      <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:26px">
        <div class="count" id="count">共 {len(PLANTS)} 种</div>
        <button class="chip" id="reset" style="display:none">清除筛选</button>
      </div>
      <div class="grid" id="grid">
{cards}
      </div>
      <div class="empty" id="empty" style="display:none">没有符合条件的植物。<br><span style="font-size:13px">换一个月份，或清除筛选试试。</span></div>
    </div>
  </section>
</main>
"""
    html += foot("/")
    (OUT / "atlas.html").write_text(html, encoding="utf-8")


# ---------------------------------------------------------------- 详情页

def build_species():
    (OUT / "species").mkdir(exist_ok=True)
    for i, p in enumerate(PLANTS):
        cat = CATMAP[p["cat"]]
        prev_p = PLANTS[i - 1]
        next_p = PLANTS[(i + 1) % len(PLANTS)]
        tags = "".join(f'<span class="tag">{esc(t)}</span>' for t in p["tags"])
        shots = PHOTOS.get(p["slug"], [])
        field = ""
        if shots:
            figs = []
            for i, ph in enumerate(shots[:2]):
                cls = "field__item--wide" if i == 0 else "field__item--tall"
                figs.append(f'''
        <figure class="field__item {cls}">
          <div class="field__frame">
            <img src="/assets/img/field/{ph['file']}" alt="{esc(p['name'])} 实景" loading="lazy">
          </div>
          <figcaption class="field__cap">
            <span>{esc(ph['caption'])}</span>
            <span>{esc(ph['credit'])}</span>
          </figcaption>
        </figure>''')
            field = f'''
    <section class="field">
      <div class="field__head">
        <h2 class="field__title">野 外</h2>
        <span class="field__sub">In the field</span>
      </div>
      <div class="field__grid">{''.join(figs)}
      </div>
    </section>'''
        habit_note = "常绿" if p["evergreen"] else "落叶 / 半落叶"

        html = head(
            f"{p['name']} {p['latin']} · 珠海草木志", "/",
            f"{p['name']}（{p['latin']}），{p['family']}{p['genus']}，{p['habit']}，花期{flower_text(p['months'])}。{p['lead']}",
            "atlas", f"/species/{p['slug']}")
        html += f"""
<main class="detail">
  <div class="wrap">
    <div class="crumbs">
      <a href="/">封面</a><span>/</span>
      <a href="/atlas?cat={p['cat']}">{cat['name']}</a><span>/</span>
      <span style="color:var(--ink-soft)">{p['name']}</span>
    </div>

    <div class="detail__grid">
      <div>
        <div class="plate reveal">
          <div class="plate__frame">
            <img src="../assets/img/{p['slug']}.webp" alt="{esc(p['name'])}（{esc(p['latin'])}）风格化植物图谱" width="900" height="1125">
          </div>
          <div class="plate__cap">
            <span>PLATE {p['no']}</span>
            <span>{esc(p['latin'])} · 风格化图谱</span>
          </div>
        </div>
        <div class="tagrow">{tags}</div>
      </div>

      <div>
        <div class="detail__head">
          <div class="detail__no">No. {p['no']} — {cat['name']}</div>
          <h1 class="detail__name">{esc(p['name'])}</h1>
          <div class="detail__latin">{esc(p['latin'])}</div>
          <div class="detail__alias">{esc(p['family'])} · {esc(p['genus'])} · 别名 {esc(p['alias'])}</div>
          <p class="detail__lead">{esc(p['lead'])}</p>
          <p class="detail__body">{esc(p['body'])}</p>
        </div>

        <dl class="facts">
          <div class="facts__item"><dt>生活型</dt><dd>{esc(p['habit'])}</dd></div>
          <div class="facts__item"><dt>株 高</dt><dd>{esc(p['height'])}</dd></div>
          <div class="facts__item"><dt>花 期</dt><dd>{flower_text(p['months'])}<a class="factlink" href="/calendar">花历</a></dd></div>
          <div class="facts__item"><dt>花 色</dt><dd>{esc(p['color'])}</dd></div>
          <div class="facts__item"><dt>原产地</dt><dd style="font-size:15px;line-height:1.7">{esc(p['origin'])}</dd></div>
          <div class="facts__item"><dt>常绿性</dt><dd>{habit_note}</dd></div>
        </dl>

        <div class="parts">
          <div class="parts__row"><div class="parts__k">叶</div><div class="parts__v">{esc(p['leaf'])}</div></div>
          <div class="parts__row"><div class="parts__k">花</div><div class="parts__v">{esc(p['flower'])}</div></div>
          <div class="parts__row"><div class="parts__k">珠海</div><div class="parts__v">{esc(p['where'])}</div></div>
        </div>

        <div class="note">
          <b>观察笔记</b>
          {esc(p['note'])}
        </div>
      </div>
    </div>
{field}
    <div class="adjacent">
      <a href="/species/{prev_p['slug']}">
        <div class="adjacent__k">← 上一则</div>
        <div class="adjacent__n">{prev_p['name']}</div>
        <div class="adjacent__l">{prev_p['latin']}</div>
      </a>
      <a href="/species/{next_p['slug']}">
        <div class="adjacent__k">下一则 →</div>
        <div class="adjacent__n">{next_p['name']}</div>
        <div class="adjacent__l">{next_p['latin']}</div>
      </a>
    </div>
  </div>
</main>
"""
        html += foot("/")
        (OUT / "species" / f"{p['slug']}.html").write_text(html, encoding="utf-8")


# ---------------------------------------------------------------- 名录

PINYIN = {
    "白兰": "bailan", "扁桃": "biantao", "长春花": "changchunhua", "垂叶榕": "chuiyerong",
    "葱兰": "conglan", "非洲楝": "feizhoulian", "宫粉羊蹄甲": "gongfenyangtijia", "桂花": "guihua",
    "海南蒲桃": "hainanputao", "荷花": "hehua", "红绒球": "hongrongqiu", "胡椒木": "hujiaomu",
    "黄葛树": "huanggeshu", "黄槿": "huangjin", "黄杨": "huangyang", "鸡蛋花": "jidanhua",
    "假槟榔": "jiabinglang", "假连翘": "jialianqiao", "夹竹桃": "jiazhutao", "芒果": "mangguo",
    "美人蕉": "meirenjiao", "米兰": "milan", "软枝黄蝉": "ruanzhihuangchan", "睡莲": "shuilian",
    "水翁": "shuiweng", "苏铁": "sutie", "台湾相思": "taiwanxiangsi", "糖胶树": "tangjiaoshu",
    "文殊兰": "wenshulan", "希茉莉": "ximoli", "银海枣": "yinhaizao", "再力花": "zailihua",
    "栀子": "zhizi", "朱槿": "zhujin", "紫花风铃木": "zihuafenglingmu", "紫花马缨丹": "zihuamayingdan",
}


def build_roster():
    rows = []
    for a in sorted(ARCHIVE, key=lambda x: PINYIN.get(x["name"], x["name"])):
        rows.append(
            f"""        <tr>
          <td>{esc(a['name'])}</td>
          <td class="lat">{esc(a['latin'])}</td>
          <td>{esc(a['family'])}</td>
          <td style="white-space:nowrap">{esc(a['flower'])}</td>
          <td>{esc(a['note'])}</td>
        </tr>"""
        )

    html = head("补充名录 · 珠海草木志", "/", "珠海常见园林植物补充名录，三十六种植物的科属、花期与形态要点。", "roster", "/roster")
    html += f"""
<main>
  <section class="section section--tight">
    <div class="wrap">
      <div class="eyebrow">Appendix · Roster</div>
      <h1 style="margin:12px 0 14px;font-size:clamp(32px,5vw,52px);font-weight:400;letter-spacing:.1em">补充名录</h1>
      <p style="margin:0;max-width:640px;font-size:15.5px;line-height:2;color:var(--ink-soft)">以下 {len(ARCHIVE)} 种在珠海同样常见，但尚未单独成篇。按中文名音序排列，附学名、科属、花期与一句话辨识要点。文中标注「有毒」者，请勿采食或让儿童接触汁液。</p>
    </div>
  </section>

  <section class="section" style="padding-top:10px">
    <div class="wrap">
      <table class="roster">
        <thead>
          <tr><th style="width:15%">中文名</th><th style="width:20%">学名</th><th style="width:10%">科</th><th style="width:11%">花期</th><th>要点</th></tr>
        </thead>
        <tbody>
{chr(10).join(rows)}
        </tbody>
      </table>
    </div>
  </section>
</main>
"""
    html += foot("/")
    (OUT / "roster.html").write_text(html, encoding="utf-8")


# ---------------------------------------------------------------- 关于

def build_about():
    html = head("编例与说明 · 珠海草木志", "/", "珠海草木志的编写说明：分类方式、花期判定、插画来源与参考依据。", "about", "/about")
    html += """
<main>
  <section class="section">
    <div class="wrap" style="max-width:820px">
      <div class="eyebrow">About this guide</div>
      <h1 style="margin:12px 0 30px;font-size:clamp(32px,5vw,52px);font-weight:400;letter-spacing:.1em">编例</h1>

      <div style="font-size:16.5px;line-height:2.1;color:var(--ink-soft)">
        <p style="margin-top:0">本志收录珠海市城区（香洲、吉大、拱北、横琴、唐家湾、金湾）道路、公园、居住区与海岸带最常见的园林植物七十余种。其中四十种单独成篇，其余著录于名录。</p>

        <h2 style="font-size:22px;font-weight:400;letter-spacing:.08em;color:var(--ink);margin:2.2em 0 .7em">一 · 分类</h2>
        <p style="margin:0">卷次的划分依据植物在城市中的角色，而非分类学亲缘：<strong>行道树</strong>指承担遮荫与街道骨架的乔木；<strong>观花乔木</strong>指以花期观赏为主要功能的乔木；<strong>绿篱灌木</strong>指用于分隔、围合、修剪成形的灌木；<strong>地被与草花</strong>指贴地覆盖的草本；<strong>棕榈与滨海</strong>指棕榈科及典型海岸带植物。因此凤凰木属观花乔木而不属行道树，尽管它同样种在路边。</p>

        <h2 style="font-size:22px;font-weight:400;letter-spacing:.08em;color:var(--ink);margin:2.2em 0 .7em">二 · 学名与科属</h2>
        <p style="margin:0">学名采用现行接受名。科级分类依 APG IV 系统，部分传统科名（如木棉科、八角金盘科）已并入锦葵科、五加科，文中统一使用新科名，并在必要处注明旧名沿革。属名与种加词以斜体排印，命名人缩写从略。</p>

        <h2 style="font-size:22px;font-weight:400;letter-spacing:.08em;color:var(--ink);margin:2.2em 0 .7em">三 · 花期</h2>
        <p style="margin:0">所标月份为珠海城区的常见花期区间，来自本地观察记录的归纳，而非植物志的全国性数据。同一物种在珠海的花期往往比其在长江流域的记载提前一个月以上；遇暖冬或冷春，前后浮动两至三周属正常。花历中的柱状条数代表当月开花的物种数量；另设独立的<strong>十二月花历</strong>页，以逐月色带呈现全部物种的花期分布。</p>

        <h2 style="font-size:22px;font-weight:400;letter-spacing:.08em;color:var(--ink);margin:2.2em 0 .7em">四 · 插图</h2>
        <p style="margin:0">页内图谱为风格化植物插画，模仿十八至十九世纪植物学图谱的水彩与墨线风格，用于呈现叶序、叶形、花序与花冠结构等辨识要点。它们<strong>不是实景照片</strong>，细节（如绒毛、腺点、脉序）经过简化，不能替代野外观察。若要确认物种，请以实物形态、气味与生境为准。</p>

        <h2 style="font-size:22px;font-weight:400;letter-spacing:.08em;color:var(--ink);margin:2.2em 0 .7em">五 · 安全</h2>
        <p style="margin:0">名录中标注「有毒」的物种（夹竹桃、软枝黄蝉、长春花、文殊兰等）含强心苷或生物碱，误食可致中毒；修剪或折断时流出的白色乳汁亦可能引起皮肤过敏。观赏即可，勿采、勿食、勿让儿童含咬。</p>

        <h2 style="font-size:22px;font-weight:400;letter-spacing:.08em;color:var(--ink);margin:2.2em 0 .7em">六 · 参考</h2>
        <p style="margin:0">《中国植物志》《广东植物志》《中国景观植物》（邢福武等）、Flora of China（eFloras）、《华南常见园林植物图谱》，以及珠海市城市管理和综合执法局公布的园林绿化树种名录。物种在珠海的具体分布位置，来自编写者的实地观察。</p>

        <div class="note" style="margin-top:44px">
          <b>一处提醒</b>
          本志是一份个人观察笔记，不是鉴定手册。若用于教学、工程或科研用途，请以权威植物志与标本记录为准。发现错漏，欢迎指正。
        </div>
      </div>
    </div>
  </section>
</main>
"""
    html += foot("/")
    (OUT / "about.html").write_text(html, encoding="utf-8")


# ---------------------------------------------------------------- 花历

def month_runs(months):
    """把月份列表压成连续区间 [(起, 止), ...]，跨年不合并（视觉上贴着两端即可）"""
    if not months:
        return []
    ms = sorted(months)
    if len(ms) == 12:
        return [(1, 12)]
    out, s, p = [], ms[0], ms[0]
    for m in ms[1:]:
        if m == p + 1:
            p = m
            continue
        out.append((s, p))
        s = p = m
    out.append((s, p))
    return out


CATCOLOR = {"street": "#3D5C4D", "blossom": "#B25C45", "shrub": "#B18F46",
            "ground": "#7E8F5B", "palm": "#4C7B87"}


def build_calendar():
    by_month = {m: [] for m in range(1, 13)}
    for p in PLANTS:
        for m in p["months"]:
            by_month[m].append(p)
    counts = [len(by_month[m]) for m in range(1, 13)]

    legend = "".join(
        f'<span><i style="background:{CATCOLOR[c["id"]]}"></i>{c["name"]}</span>' for c in CATS
    )

    head_month = "".join(
        f'<span data-m="{m}">{ROMAN[m-1]}</span>' for m in range(1, 13)
    )

    rows = []
    for c in CATS:
        grp = [p for p in PLANTS if p["cat"] == c["id"]]
        rows.append(
            f'      <div class="bloom__group"><span>{c["no"]} · {c["name"]}</span>'
            f'<span>{len(grp):02d} 种</span></div>'
        )
        for p in grp:
            bars = "".join(
                f'<span class="bloom__bar" style="grid-column:{a} / {b+1}"></span>'
                for a, b in month_runs(p["months"])
            )
            rows.append(f"""      <div class="bloom__row" data-cat="{p['cat']}" data-months="{','.join(map(str, p['months']))}">
        <a class="bloom__name" href="/species/{p['slug']}"><span class="bloom__cn">{esc(p['name'])}</span><span class="bloom__lat">{esc(p['latin'])}</span></a>
        <div class="bloom__track">{bars}</div>
        <span class="bloom__f">{flower_text(p['months'])}</span>
      </div>""")

    tail = "".join(f"<span>{n}</span>" for n in counts)

    html = head("十二月花历 · 珠海草木志", "/",
                f"珠海 {len(PLANTS)} 种常见园林植物的逐月花期表，一月到十二月，按月查看当月开花的物种。",
                "calendar", "/calendar")
    html += f"""
<main>
  <section class="section section--tight" style="padding-bottom:30px">
    <div class="wrap">
      <div class="eyebrow">Almanac · Bloom Calendar</div>
      <h1 style="margin:12px 0 16px;font-size:clamp(32px,5vw,52px);font-weight:400;letter-spacing:.1em">十二月花历</h1>
      <p style="margin:0;max-width:640px;font-size:15.5px;line-height:2.05;color:var(--ink-soft)">横轴是一年，纵轴是 {len(PLANTS)} 种植物。色块出现的月份，就是它在珠海开花的月份。南方的花期不以春天为限——这里几乎每个月都有东西在开，真正的空档，只有八月的台风天。</p>
      <p id="nowline" style="margin:22px 0 0;font-family:var(--font-sans);font-size:12.5px;letter-spacing:.14em;color:var(--clay)"></p>
    </div>
  </section>

  <section class="section" style="padding-top:26px">
    <div class="wrap">
      <div class="bloom__legend">{legend}</div>
      <p class="scrollhint">← 左右滑动查看全年十二个月 →</p>
      <p class="scrollhint">← 左右滑动查看全年十二个月 →</p>
      <div class="bloom" data-counts="{','.join(map(str, counts))}">
        <div class="bloom__scroll">
          <div class="bloom__inner">
            <div class="bloom__head">
              <div class="bloom__cap">SPECIES</div>
              <div class="bloom__months">{head_month}</div>
              <div class="bloom__cap">花期</div>
            </div>
{chr(10).join(rows)}
            <div class="bloom__tail">
              <div class="bloom__cap">当月<br>种数</div>
              <div class="bloom__n">{tail}</div>
              <div class="bloom__cap"></div>
            </div>
          </div>
        </div>
      </div>
      <p style="margin:26px 0 0;font-size:13.5px;line-height:1.95;color:var(--ink-faint);max-width:660px">表中所列为珠海城区的常见花期，来自本地观察归纳。同一物种在珠海的花期，通常比长江流域的记载提前一个月以上；遇暖冬或冷春，前后浮动两三周属正常。占满十二格的两种——朱槿与长春花——是真正全年不休的。</p>
    </div>
  </section>
</main>
"""
    html += foot("/")
    (OUT / "calendar.html").write_text(html, encoding="utf-8")


# ---------------------------------------------------------------- 分布示意

PLACES = [
    {"no": "I", "name": "唐家湾", "en": "Tangjiawan", "x": 824, "y": 118,
     "lx": 804, "ly": 122, "anchor": "end",
     "kw": ["唐家", "淇澳"],
     "desc": "珠海北端的老镇。青砖巷、祠堂前的百年榕树，往东是淇澳岛的红树林与海岸防风林。中山大学珠海校区也在这里，校园里的树种几乎是半部图鉴。"},
    {"no": "II", "name": "老香洲", "en": "Old Xiangzhou", "x": 758, "y": 238,
     "lx": 738, "ly": 242, "anchor": "end",
     "kw": ["香洲", "凤凰路", "南坑", "柠溪", "前山", "人民东", "人民西"],
     "desc": "城市最早的一批街道。凤凰路的骑楼、南坑的市场、柠溪与南屏的老小区，行道树种得最密，树冠把整条街盖成隧道。"},
    {"no": "III", "name": "情侣路", "en": "Lovers' Road", "x": 700, "y": 330,
     "lx": 680, "ly": 334, "anchor": "end",
     "kw": ["情侣路", "海滨"],
     "desc": "全长约五十公里的滨海大道。海风、盐雾、台风与烈日同时作用，留下的都是些硬骨头：榕、棕榈、木麻黄与露兜。"},
    {"no": "IV", "name": "吉大", "en": "Jida", "x": 618, "y": 404,
     "lx": 598, "ly": 408, "anchor": "end",
     "kw": ["吉大", "九洲"],
     "desc": "商业与旧宅混杂的一段。庭院树与行道树在这里几乎分不出界线——糖胶树的塔形、假槟榔的灰白柱子，都长在离人行道两米的地方。"},
    {"no": "V", "name": "拱北", "en": "Gongbei", "x": 512, "y": 452,
     "lx": 512, "ly": 430, "anchor": "middle", "above": True,
     "kw": ["拱北", "湾仔", "南屏"],
     "desc": "口岸一带，人流与车流最急。这里种的都是最耐活的花木：高山榕、糖胶树、黄金榕——被反复修剪，依然认真地长。"},
    {"no": "VI", "name": "横琴", "en": "Hengqin", "x": 388, "y": 466,
     "lx": 388, "ly": 430, "anchor": "middle", "above": True,
     "kw": ["横琴"],
     "desc": "新填海的新城。树几乎都是近十年种下的：小叶榄仁、美丽异木棉、紫花风铃木。它们长得快，也还在长——一座新城的植被，要几十年才定型。"},
    {"no": "VII", "name": "金湾", "en": "Jinwan", "x": 214, "y": 424,
     "lx": 214, "ly": 386, "anchor": "middle", "above": True,
     "kw": ["金湾", "斗门"],
     "desc": "西侧的海岸与湿地。防风林、滩涂与咸淡水交界处的植物在这里占主导，城市化的痕迹要稀薄得多。"},
]

COAST_PTS = [(884, 16), (824, 118), (758, 238), (700, 330), (618, 404),
             (512, 452), (388, 466), (214, 424), (128, 402), (24, 392)]


def smooth_path(pts, tension=1.0):
    d = f"M {pts[0][0]} {pts[0][1]}"
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i > 0 else pts[i]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < len(pts) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6 * tension, p1[1] + (p2[1] - p0[1]) / 6 * tension)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6 * tension, p2[1] - (p3[1] - p1[1]) / 6 * tension)
        d += f" C {c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
    return d


def build_map():
    for pl in PLACES:
        pl["plants"] = [p for p in PLANTS if any(k in p["where"] for k in pl["kw"])]

    matched = {p["slug"] for pl in PLACES for p in pl["plants"]}
    citywide = [p for p in PLANTS if p["slug"] not in matched]
    total_seen = len(matched)

    coast = smooth_path(COAST_PTS)
    sea = coast + " L 24 392 L 24 540 L 900 540 L 900 16 Z"
    land = coast + " L 24 392 L 24 16 L 884 16 Z"

    waves = "".join(
        f'<path d="{coast}" fill="none" stroke="#4C7B87" stroke-width="1" '
        f'stroke-dasharray="1 9" stroke-linecap="round" opacity="{0.30 - i*0.07:.2f}" '
        f'transform="translate({22 + i*26},{14 + i*11})" />'
        for i in range(4)
    )

    contours = "".join(
        f'<path d="{d}" fill="none" stroke="#3D5C4D" stroke-width=".9" opacity="{o}"/>'
        for d, o in [
            ("M 60 118 C 170 96 286 122 372 92", ".12"),
            ("M 54 178 C 168 150 300 180 410 148", ".11"),
            ("M 70 238 C 190 210 318 240 440 208", ".10"),
            ("M 96 296 C 214 268 344 296 470 268", ".09"),
            ("M 150 348 C 262 320 384 344 500 318", ".08"),
            ("M 214 394 C 300 372 400 388 496 368", ".07"),
            ("M 250 158 C 330 132 420 150 486 122", ".08"),
            ("M 430 74 C 530 52 620 70 700 46", ".07"),
            ("M 560 120 C 640 100 706 112 760 92", ".06"),
        ]
    )

    # 陆地点状纹理（固定随机种子，示意性点缀，不对应真实地物）
    import random as _rnd
    _rnd.seed(20261118)

    def _coast_y(x):
        for i in range(len(COAST_PTS) - 1):
            x1, y1 = COAST_PTS[i]
            x2, y2 = COAST_PTS[i + 1]
            if x1 <= x <= x2 or x2 <= x <= x1:
                t = (x - x1) / (x2 - x1)
                return y1 + (y2 - y1) * t
        return 400

    stipple = []
    tries = 0
    while len(stipple) < 130 and tries < 4000:
        tries += 1
        x = _rnd.uniform(46, 852)
        y = _rnd.uniform(36, 500)
        if y < _coast_y(x) - 34:
            r = _rnd.choice([0.7, 0.9, 1.0, 1.2])
            stipple.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="#3D5C4D" opacity=".13"/>')
    stipple = "".join(stipple)

    # 陆地点状纹理（固定随机种子，示意性点缀，不对应真实地物）
    import random as _rnd
    _rnd.seed(20261118)

    def _coast_y(x):
        for i in range(len(COAST_PTS) - 1):
            x1, y1 = COAST_PTS[i]
            x2, y2 = COAST_PTS[i + 1]
            if x1 <= x <= x2 or x2 <= x <= x1:
                t = (x - x1) / (x2 - x1)
                return y1 + (y2 - y1) * t
        return 400

    stipple = []
    tries = 0
    while len(stipple) < 130 and tries < 4000:
        tries += 1
        x = _rnd.uniform(46, 852)
        y = _rnd.uniform(36, 500)
        if y < _coast_y(x) - 34:
            r = _rnd.choice([0.7, 0.9, 1.0, 1.2])
            stipple.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="#3D5C4D" opacity=".13"/>')
    stipple = "".join(stipple)

    nodes = "".join(
        f'<g><circle cx="{pl["x"]}" cy="{pl["y"]}" r="14" fill="#3D5C4D" opacity=".07"/>'
        f'<circle cx="{pl["x"]}" cy="{pl["y"]}" r="5.4" fill="#F8F4EB" stroke="#3D5C4D" stroke-width="1.6"/>'
        f'<circle cx="{pl["x"]}" cy="{pl["y"]}" r="1.9" fill="#B25C45"/>'
        f'<text x="{pl["lx"]}" y="{pl["ly"]}" text-anchor="{pl["anchor"]}" '
        f'font-family="Songti SC, serif" font-size="18.5" fill="#1E2A25" letter-spacing="2.6">{pl["name"]}</text>'
        f'<text x="{pl["lx"]}" y="{pl["ly"] + -17}" text-anchor="{pl["anchor"]}" '
        f'font-family="PingFang SC, sans-serif" font-size="9.6" fill="#8B968E" letter-spacing="1.4">'
        f'{pl["no"]} · {len(pl["plants"])} 种</text></g>'
        for pl in PLACES
    )

    compass = (
        '<g transform="translate(70,74)" opacity=".55">'
        '<path d="M 0 20 L 0 -20" stroke="#3D5C4D" stroke-width="1"/>'
        '<path d="M 0 -20 L -5.5 -6 L 0 -10.5 L 5.5 -6 Z" fill="#3D5C4D"/>'
        '<text x="0" y="-28" text-anchor="middle" font-family="Georgia, serif" '
        'font-size="12" fill="#3D5C4D" letter-spacing="1">N</text></g>'
    )

    svg = f"""<svg viewBox="0 0 900 540" role="img" aria-label="珠海各片区植物分布示意图，非比例尺" xmlns="http://www.w3.org/2000/svg">
  <rect width="900" height="540" fill="#DCE9E9"/>
  <path d="{land}" fill="#F3ECDD"/>
  <path d="{sea}" fill="#CFE1E1" opacity=".45"/>
  {waves}
  {contours}
  {stipple}
  {stipple}
  <path d="{coast}" fill="none" stroke="#3D5C4D" stroke-width="2" stroke-linecap="round"/>
  <text transform="translate(866,250) rotate(-90)" text-anchor="middle"
        font-family="Songti SC, serif" font-size="19" fill="#4C7B87" opacity=".34" letter-spacing="10">伶 仃 洋</text>
  <text x="600" y="512" text-anchor="middle" font-family="Songti SC, serif" font-size="16"
        fill="#4C7B87" opacity=".32" letter-spacing="12">南 海</text>
  {compass}
  {nodes}
</svg>"""

    cards = []
    for pl in PLACES:
        cards.append(place_card(pl, pl["name"], pl["en"], pl["desc"], pl["plants"]))
    if citywide:
        cards.append(place_card(
            {"no": "VIII"}, "全城", "Citywide",
            "还有一些不挑地段的：种在每一条分车带、每一座天桥、每一个小区的围墙里。它们不专属于某个片区，而是这座城市绿化的底板。",
            citywide))

    html = head("分布示意 · 珠海草木志", "/",
                "珠海七个片区的植物分布示意图：唐家湾、老香洲、情侣路、吉大、拱北、横琴、金湾，各区常见物种一览。",
                "map", "/map")
    html += f"""
<main>
  <section class="section section--tight" style="padding-bottom:16px">
    <div class="wrap">
      <div class="eyebrow">Distribution · A Schematic View</div>
      <h1 style="margin:12px 0 16px;font-size:clamp(32px,5vw,52px);font-weight:400;letter-spacing:.1em">分布示意</h1>
      <p style="margin:0;max-width:640px;font-size:15.5px;line-height:2.05;color:var(--ink-soft)">同一座城市里，草木也分地段。海边的树种抗盐，老街的树种耐修剪，新区的树种要长得快。这张图画的是七个片区的位置关系与各自的常见物种——它不是地图，只是一份关系示意图。</p>
    </div>
  </section>

  <section class="section" style="padding-top:8px;padding-bottom:34px">
    <div class="wrap">
      <figure class="mapfig">
        <div class="mapfig__scroll">{svg}</div>
        <figcaption class="mapfig__note">
          <span>位置关系示意 · 非比例尺 · 不作导航使用</span>
          <span>七个片区共记录 {total_seen} 种，另 {len(citywide)} 种全城可见</span>
        </figcaption>
        <p class="scrollhint">← 左右滑动查看全图 →</p>
      </figure>
    </div>
  </section>

  <section class="section" style="padding-top:0">
    <div class="wrap">
      <div class="placegrid">
{chr(10).join(cards)}
      </div>
      <p style="margin:26px 0 0;font-size:13.5px;line-height:1.95;color:var(--ink-faint);max-width:680px">片区划分依日常称呼，与行政区划不完全对应。「可见于」表示该物种在片区内的道路、公园或庭院中被记录到，并不意味它只生长于此。</p>
    </div>
  </section>
</main>
"""
    html += foot("/")
    (OUT / "map.html").write_text(html, encoding="utf-8")


def place_card(pl, name, en, desc, plants):
    chips = "".join(
        f'<a href="/species/{p["slug"]}">{esc(p["name"])}</a>' for p in plants[:10]
    )
    more = ""
    if len(plants) > 10:
        more = (f'<span style="font-family:var(--font-sans);font-size:11px;color:var(--ink-faint);'
                f'padding:4px 2px">等 {len(plants)} 种</span>')
    return f"""      <div class="place">
        <div class="place__no">{pl['no']}</div>
        <h3 class="place__name">{name}</h3>
        <div class="place__en">{esc(en)}</div>
        <p class="place__desc">{esc(desc)}</p>
        <div class="place__plants">{chips}{more}</div>
      </div>"""


# ---------------------------------------------------------------- 静态资源

FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<rect width="64" height="64" fill="#F8F4EB"/>
<path d="M32 54V22" stroke="#3D5C4D" stroke-width="2" fill="none"/>
<path d="M32 30c-9 0-14-5-14-13 9 0 14 5 14 13z" fill="#3D5C4D" opacity=".85"/>
<path d="M32 26c9 0 14-5 14-13-9 0-14 5-14 13z" fill="#B25C45" opacity=".8"/>
<circle cx="32" cy="16" r="3" fill="#B18F46"/>
</svg>
"""

JS = r"""/* 珠海草木志 */
(function () {
  // 入场
  var io = new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); }
    });
  }, { rootMargin: '0px 0px -8% 0px', threshold: 0.06 });
  document.querySelectorAll('.reveal').forEach(function (el, i) {
    el.style.transitionDelay = (Math.min(i, 8) * 45) + 'ms';
    io.observe(el);
  });

  // 花历 → 图鉴
  document.querySelectorAll('.almanac__col').forEach(function (col) {
    function go() { location.href = '/atlas?month=' + col.dataset.month; }
    col.addEventListener('click', go);
    col.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); go(); } });
  });

  // 花历：高亮当月
  var bloom = document.querySelector('.bloom');
  if (bloom) {
    var counts = (bloom.dataset.counts || '').split(',').map(Number);
    var now = new Date().getMonth() + 1;
    document.querySelectorAll('.bloom__head .bloom__months span').forEach(function (el) {
      if (+el.dataset.m === now) el.classList.add('is-now');
    });
    var line = document.getElementById('nowline');
    if (line && counts.length === 12) {
      line.textContent = now + ' 月 · 全城 ' + counts[now - 1] + ' 种正在开花';
    }
  }

  // 花历：高亮当月
  var bloom = document.querySelector('.bloom');
  if (bloom) {
    var counts = (bloom.dataset.counts || '').split(',').map(Number);
    var now = new Date().getMonth() + 1;
    document.querySelectorAll('.bloom__head .bloom__months span').forEach(function (el) {
      if (+el.dataset.m === now) el.classList.add('is-now');
    });
    var line = document.getElementById('nowline');
    if (line && counts.length === 12) {
      line.textContent = now + ' 月 · 全城 ' + counts[now - 1] + ' 种正在开花';
    }
  }

  // 小屏：地图横向滚动到海岸线一带
  document.querySelectorAll('.mapfig__scroll').forEach(function (box) {
    if (box.scrollWidth > box.clientWidth + 4) {
      box.scrollLeft = Math.round((box.scrollWidth - box.clientWidth) * 0.42);
    }
  });

  // 小屏：地图横向滚动到海岸线一带
  document.querySelectorAll('.mapfig__scroll').forEach(function (box) {
    if (box.scrollWidth > box.clientWidth + 4) {
      box.scrollLeft = Math.round((box.scrollWidth - box.clientWidth) * 0.42);
    }
  });

  // 图鉴筛选
  var grid = document.getElementById('grid');
  if (!grid) return;
  var cards = Array.prototype.slice.call(grid.querySelectorAll('.card'));
  var chips = Array.prototype.slice.call(document.querySelectorAll('.chip[data-cat]'));
  var q = document.getElementById('q');
  var countEl = document.getElementById('count');
  var emptyEl = document.getElementById('empty');
  var resetEl = document.getElementById('reset');
  var params = new URLSearchParams(location.search);

  var state = {
    cat: params.get('cat') || 'all',
    month: params.get('month') || '',
    text: ''
  };

  function apply() {
    var shown = 0;
    cards.forEach(function (c) {
      var okCat = state.cat === 'all' || c.dataset.cat === state.cat;
      var okMon = !state.month || (',' + c.dataset.months + ',').indexOf(',' + state.month + ',') > -1;
      var okTxt = !state.text || c.dataset.name.toLowerCase().indexOf(state.text) > -1;
      var ok = okCat && okMon && okTxt;
      c.style.display = ok ? '' : 'none';
      if (ok) { shown++; c.classList.add('is-in'); }
    });
    chips.forEach(function (b) { b.classList.toggle('is-on', b.dataset.cat === state.cat); });
    var bits = [];
    if (state.cat !== 'all') {
      var t = document.querySelector('.chip[data-cat="' + state.cat + '"]');
      if (t) bits.push(t.textContent);
    }
    if (state.month) bits.push(state.month + ' 月开花');
    countEl.textContent = '共 ' + shown + ' 种' + (bits.length ? ' · ' + bits.join(' · ') : '');
    emptyEl.style.display = shown ? 'none' : 'block';
    resetEl.style.display = (state.cat !== 'all' || state.month || state.text) ? '' : 'none';
  }

  chips.forEach(function (b) {
    b.addEventListener('click', function () {
      state.cat = b.dataset.cat;
      state.month = '';
      apply();
      history.replaceState(null, '', state.cat === 'all' ? location.pathname : '?cat=' + state.cat);
    });
  });
  if (q) {
    q.addEventListener('input', function () {
      state.text = q.value.trim().toLowerCase();
      apply();
    });
  }
  if (resetEl) {
    resetEl.addEventListener('click', function () {
      state = { cat: 'all', month: '', text: '' };
      if (q) q.value = '';
      apply();
      history.replaceState(null, '', location.pathname);
    });
  }
  apply();
})();
"""


def build_404():
    html = head("页面走失 · 珠海草木志", "/", "这一页不见踪迹。", "", "/404")
    html += """
<main class="section" style="min-height:60vh;display:flex;align-items:center">
  <div class="wrap" style="text-align:center">
    <div class="eyebrow">Error 404</div>
    <h1 style="margin:20px 0 16px;font-size:clamp(30px,5vw,46px);font-weight:400;letter-spacing:.1em">这一页，落进了草丛里</h1>
    <p style="margin:0 auto;max-width:440px;font-size:15.5px;line-height:2;color:var(--ink-soft)">你要找的页面大概被风带走了。不如回到封面，从一棵榕树重新开始。</p>
    <div style="margin-top:34px;display:flex;gap:12px;justify-content:center;flex-wrap:wrap">
      <a href="/" class="chip" style="padding:11px 26px">回到封面</a>
      <a href="/atlas" class="chip" style="padding:11px 26px">翻看图鉴</a>
    </div>
  </div>
</main>
"""
    html += foot("/")
    (OUT / "404.html").write_text(html, encoding="utf-8")


def build_meta_files():
    urls = ["", "atlas", "calendar", "map", "roster", "about"]
    urls += [f"species/{p['slug']}" for p in PLANTS]
    entries = []
    for u in urls:
        loc = f"{SITE}/{u}"
        pri = "1.0" if u == "" else ("0.8" if u in ("atlas", "calendar", "map", "roster") else "0.7")
        entries.append(
            f"  <url><loc>{loc}</loc><changefreq>monthly</changefreq><priority>{pri}</priority></url>"
        )
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(entries) + "\n</urlset>\n", encoding="utf-8")
    (OUT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "assets" / "css").mkdir(parents=True)
    (OUT / "assets" / "js").mkdir(parents=True)
    shutil.copy(ROOT / "assets/css/style.css", OUT / "assets/css/style.css")
    (OUT / "assets" / "js" / "site.js").write_text(JS, encoding="utf-8")
    (OUT / "assets" / "favicon.svg").write_text(FAVICON, encoding="utf-8")
    if (ROOT / "assets" / "og.png").exists():
        shutil.copy(ROOT / "assets" / "og.png", OUT / "assets" / "og.png")
    if (ROOT / "assets" / "og.png").exists():
        shutil.copy(ROOT / "assets" / "og.png", OUT / "assets" / "og.png")

    # 图片
    src_img = ROOT / "assets" / "img"
    dst_img = OUT / "assets" / "img"
    dst_img.mkdir(parents=True)
    missing = []
    for p in PLANTS:
        f = src_img / "opt" / f"{p['slug']}.webp"
        if f.exists():
            shutil.copy(f, dst_img / f.name)
        else:
            missing.append(p["slug"])

    fsrc = src_img / "field"
    if fsrc.exists():
        fdst = dst_img / "field"
        fdst.mkdir(parents=True, exist_ok=True)
        for f in fsrc.glob("*.webp"):
            shutil.copy(f, fdst / f.name)

    build_index()
    build_atlas()
    build_calendar()
    build_map()
    build_species()
    build_roster()
    build_about()
    build_404()
    build_meta_files()

    print(f"built: {len(PLANTS)} species pages, {len(PLANTS)+len(ARCHIVE)} taxa")
    if missing:
        print("MISSING IMAGES:", ", ".join(missing))


if __name__ == "__main__":
    main()
