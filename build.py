#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""珠海草木志 / Flora of Zhuhai —— static site builder (bilingual)"""
import json, shutil, re
from pathlib import Path

ROOT = Path(__file__).parent
DATA = json.loads((ROOT / "data" / "plants.json").read_text(encoding="utf-8"))
OUT_ZH = ROOT / "dist"
OUT_EN = OUT_ZH / "en"
OUT = OUT_ZH

LANG = "zh"

EN_FILE = ROOT / "data" / "en.json"
EN = json.loads(EN_FILE.read_text(encoding="utf-8")) if EN_FILE.exists() else {}

META = DATA["meta"]
CATS = DATA["categories"]
PLANTS = DATA["plants"]
ARCHIVE = DATA.get("archive", [])
PHOTO_FILE = ROOT / "data" / "photos.json"
PHOTOS = json.loads(PHOTO_FILE.read_text(encoding="utf-8")) if PHOTO_FILE.exists() else {}
ZH_CATS, ZH_PLANTS, ZH_PHOTOS = CATS, PLANTS, PHOTOS
CATMAP = {c["id"]: c for c in CATS}

SITE = "https://plants.signupeverywhere.cc"

MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]


# ---------------------------------------------------------------- 界面文案
# 每条为 (中文, English)。调用 t("键") 取当前语言；带占位符的用 .format()

TXT = {
    # —— 品牌与导航
    "brand": ("珠海草木志", "Flora of Zhuhai"),
    "brand_sub": ("Flora of Zhuhai", "A guide to the city's plants"),
    "nav_home": ("封面", "Home"),
    "nav_atlas": ("图鉴", "Atlas"),
    "nav_calendar": ("花历", "Almanac"),
    "nav_map": ("分布", "Places"),
    "nav_roster": ("索引", "Index"),
    "nav_about": ("关于", "About"),

    # —— 页脚
    "foot_p": ("一份关于暖亚热带与热带过渡型海洋性气候城市的植物观察笔记。收录珠海街头、公园与海岸线上最寻常、也最容易被忽略的七十六种植物。",
               "Field notes on a city in the warm subtropical–tropical maritime transition: the seventy-six plants of Zhuhai's streets, parks and shoreline — the commonest ones, and the easiest to walk past."),
    "foot_atlas": ("图鉴总览", "The Atlas"),
    "foot_calendar": ("十二月花历", "Bloom Calendar"),
    "foot_map": ("分布示意", "Distribution"),
    "foot_roster": ("科属索引", "Index by Family"),
    "foot_about": ("编例与说明", "About this Guide"),
    "foot_note": ("花期因年份、纬度和局部小气候而异，文中月份为珠海城区的常见区间。插图均为风格化植物图谱，用于辨识形态要点，非实景照片。",
                  "Flowering months shift with the year, the latitude and the local microclimate; the months given here are the usual window in urban Zhuhai. The plates are stylised botanical drawings made to show the points that matter for recognition — they are not photographs."),
    "foot_where": ("珠海 · 北纬 22°14′ — 22°37′", "Zhuhai · 22°14′–22°37′ N"),
    "foot_count": ("共 {} 种 · {} 科", "{} species · {} families"),

    # —— 卡片
    "card_alt": ("{}（{}）植物图谱", "{} ({}) — botanical plate"),
    "card_bloom": ("花期 {}", "Bloom {}"),
    "card_plate": ("风格化图谱", "stylised plate"),
    "card_no": ("No. {}", "No. {}"),

    # —— 首页
    "home_title": ("珠海草木志 · 暖亚热带与热带过渡型海洋性气候城市的植物观察",
                   "Flora of Zhuhai · Plants of a warm subtropical–tropical maritime city"),
    "home_desc": ("珠海常见行道树、绿化带植物与园林花卉图鉴。细叶榕的荫凉、凤凰木的火、簕杜鹃的市中花色，七十六种草木的形态、花期与故事。",
                  "A guide to the street trees, planting-strip shrubs and garden flowers of Zhuhai: the shade of the Chinese banyan, the fire of the flamboyant, the bougainvillea that colours the middle of the city. Seventy-six plants, their forms, their seasons and their stories."),
    "hero_h1": ("城市日新，<br>草木<em>常在</em>。", "Cities change;<br>the <em>plants</em> remain."),
    "hero_note": ("收录珠海常见园林花木、行道树图鉴与四季赏花路线",
                  "Garden trees, street trees and a year-round calendar of bloom"),
    "hero_sub": ("珠海是一座长在植物里的城市。北回归线以南、伶仃洋以西，长夏无冬，雨热同期——于是榕树的气根垂成帘，凤凰木在五月点着整条街，簕杜鹃从天桥一路开到海堤。这里收录它们当中的七十六种：行道树、绿篱灌木、地被草花，与海岸线上的棕榈。",
                 "Zhuhai is a city that lives inside its plants. South of the Tropic of Cancer and west of the Lingding Channel, it has a long summer and no winter, rain and heat arriving together — so banyan aerial roots hang down in curtains, the flamboyant sets a whole street alight in May, and bougainvillea runs from the footbridges all the way to the seawall. Here are seventy-six of them: street trees, hedge shrubs, groundcover flowers, and the palms along the coast."),
    "stat_species": ("收录物种", "species"),
    "stat_vols": ("分卷", "volumes"),
    "stat_temp": ("年均气温", "mean temp."),
    "stat_sun": ("日照小时", "hours of sun"),
    "vol_h": ("五卷", "Five Volumes"),
    "vol_p": ("依植物在城中承担的角色而分，而非严格的分类学。同一种树，可能既是行道树，也是夏天的花。",
              "Divided by the part each plant plays in the city rather than by strict taxonomy. The same tree can be both a street tree and a summer flower."),
    "cal_h": ("十二月花历", "Bloom Calendar"),
    "cal_p": ("点选月份，查看当月开花的物种。南方的花期不以春天为限——真正的空档，其实只有八月的台风天。",
              "Pick a month to see what is flowering then. In the south the season does not stop at spring — the only real gap is the typhoon weeks of August."),
    "cal_more": ("查 看 完 整 花 历 &nbsp;→", "See the full calendar →"),
    "pick_h": ("十种读懂珠海的方式", "Ten Ways to Read Zhuhai"),
    "pick_p": ("如果只有半天时间认识这座城市的植物，从这里开始。",
               "If you have half a day to meet the plants of this city, start here."),
    "why_h": ("为什么是这些植物", "Why These Plants"),
    "why_p": ("风、盐、雨、热——四种力量共同筛选出珠海的行道树名单。",
              "Wind, salt, rain, heat — four forces that between them draw up the list of Zhuhai's street trees."),
    "why_1": ("珠海地处暖亚热带与热带过渡型的海洋性气候区——北回归线以南、南海之滨，年均气温约 22.5℃，年降水量 1,700–2,300 毫米，全年无霜。夏季漫长而湿热，冬季短暂温和，海风终年不断，每年平均还要承受 3–4 个热带气旋过境。这样的气候给植物出了一道苛刻的考题：既要耐得住长时间的高温高湿，又要在台风过境时不被连根拔起；既要扛住海风的盐雾，也要适应填海地带偏碱、偏浅的土层。",
              "Zhuhai sits in a maritime climate at the transition between warm subtropical and tropical — south of the Tropic of Cancer, on the shore of the South China Sea, with a mean annual temperature of about 22.5 °C, 1,700–2,300 mm of rain and no frost at all. The summer is long, hot and humid; the winter short and mild; the sea wind never stops; and three or four tropical cyclones pass through in an average year. That climate sets the plants a hard examination: they must endure months of heat and moisture, and survive being torn out by the roots when a typhoon comes; they must shrug off salt-laden spray, and tolerate the shallow, alkaline fill soil of the reclaimed land."),
    "why_2": ("于是名单被反复筛过。榕属以气生根与柔韧的枝干胜出，樟科以深根与芳香油脂胜出，棕榈科以能屈能伸的羽叶胜出。凤凰木、木棉、黄花风铃木则代表了另一种策略：在风季到来之前完成开花结实，把一年中最好的几周押在一个短促的季节里。",
              "So the list has been sifted again and again. Ficus wins with aerial roots and supple timber; the laurels with deep roots and aromatic oils; the palms with fronds that bend instead of breaking. The flamboyant, the kapok and the golden trumpet tree stand for another strategy altogether: flower and set seed before the windy season, staking the best few weeks of the year on one short window."),
    "why_3": ("这座城市的绿，因此不是一种颜色，而是一套被气候反复修改过的答案。",
              "The green of this city is therefore not a single colour but a set of answers that the climate has revised over and over."),
    "idx_h": ("七十六种，按 {} 科索引", "Seventy-six species, indexed by {} families"),
    "idx_p": ("豆科 9 种、桑科与锦葵科各 5 种……看看同一科的植物，是怎么共享一套形态的。",
              "Nine legumes, five figs, five mallows… look at how plants of one family share a single grammar of form."),
    "idx_more": ("翻 阅 名 录 &nbsp;→", "Browse the index →"),

    # —— 图鉴
    "atlas_title": ("图鉴总览 · 珠海草木志", "The Atlas · Flora of Zhuhai"),
    "atlas_desc": ("珠海常见园林植物图鉴，共 {} 种详解，可按类别、花期与名称检索。",
                   "A guide to the common garden plants of Zhuhai: {} entries, searchable by category, flowering month or name."),
    "atlas_h": ("图鉴总览", "The Atlas"),
    "atlas_p": ("{} 种详解，每一种都附有形态图谱、花期区间、实景摄影与在珠海的具体观察位置。按类别筛选，或直接输入名字。",
                "{} entries, each with a botanical plate, its flowering months, photographs taken in the city, and the places in Zhuhai where it is actually found. Filter by category, or simply type a name."),
    "atlas_all": ("全部", "All"),
    "atlas_search": ("搜索名称 / 学名 / 科属", "Search name, Latin or family"),
    "atlas_search_aria": ("搜索植物", "Search plants"),
    "atlas_count": ("共 {} 种", "{} species"),
    "atlas_reset": ("清除筛选", "Clear filters"),
    "atlas_empty": ("没有符合条件的植物。<br><span style=\"font-size:13px\">换一个月份，或清除筛选试试。</span>",
                    "Nothing matches.<br><span style=\"font-size:13px\">Try another month, or clear the filters.</span>"),

    # —— 详情页
    "sp_title": ("{} {} · 珠海草木志", "{} · {} · Flora of Zhuhai"),
    "sp_desc": ("{}（{}），{}{}，{}，花期{}。{}", "{0} ({1}), {2}, {3}. {4}. Bloom: {5}. {6}"),
    "sp_alt": ("{}（{}）风格化植物图谱", "{} ({}) — stylised botanical plate"),
    "sp_img_alt": ("{} 实景", "{}, photographed in the city"),
    "crumb_home": ("封面", "Home"),
    "field_title": ("城 中", "In the City"),
    "field_sub": ("In the City", "Photographs"),
    "alias": ("别名 {}", "also known as {}"),
    "evergreen": ("常绿", "Evergreen"),
    "deciduous": ("落叶 / 半落叶", "Deciduous / semi-deciduous"),
    "f_habit": ("生活型", "Habit"),
    "f_height": ("株 高", "Height"),
    "f_bloom": ("花 期", "Bloom"),
    "f_color": ("花 色", "Colour"),
    "f_origin": ("原产地", "Native to"),
    "f_leaf": ("常绿性", "Foliage"),
    "f_cal": ("花历", "calendar"),
    "p_leaf": ("叶", "Leaf"),
    "p_flower": ("花", "Flower"),
    "p_where": ("珠海", "Zhuhai"),
    "note": ("观察笔记", "Field note"),
    "prev": ("← 上一则", "← Previous"),
    "next": ("下一则 →", "Next →"),

    # —— 索引
    "roster_title": ("科属索引 · 珠海草木志", "Index by Family · Flora of Zhuhai"),
    "roster_desc": ("珠海 {} 种常见园林植物按科索引，含学名、花期与详情入口。",
                    "The {} common garden plants of Zhuhai, indexed by family, with scientific names, flowering months and links."),
    "roster_h": ("科属索引", "Index by Family"),
    "roster_p": ("七十六种全部单独成篇，此处按科归并，共 {} 科。同一科的植物往往共享一套形态语言——看到豆科的荚果、锦葵科的雄蕊柱，就知道它们在亲缘上是一家人。点选任一名字即可进入详解。",
                 "All seventy-six stand alone as full entries; here they are gathered by family — {} in all. Plants of one family tend to share a grammar of form: see a legume's pod, a mallow's staminal column, and you know they are kin. Click any name for the full entry."),

    # —— 花历
    "cal_title": ("十二月花历 · 珠海草木志", "Bloom Calendar · Flora of Zhuhai"),
    "cal_desc": ("珠海 {} 种常见园林植物的逐月花期表，一月到十二月，按月查看当月开花的物种。",
                 "A month-by-month bloom chart for the {} common garden plants of Zhuhai: what is flowering in each of the twelve months."),
    "cal_h1": ("十二月花历", "Bloom Calendar"),
    "cal_lead": ("横轴是一年，纵轴是 {} 种植物。色块出现的月份，就是它在珠海开花的月份。南方的花期不以春天为限——这里几乎每个月都有东西在开，真正的空档，只有八月的台风天。",
                 "The horizontal axis is the year; the vertical axis is {} species. Where a bar appears is when that plant flowers in Zhuhai. The season here does not stop at spring — something is in bloom almost every month, and the only real gap is the typhoon weeks of August."),
    "cal_sh": ("← 左右滑动查看全年十二个月 →", "← Scroll sideways for all twelve months →"),
    "cal_f": ("花期", "Bloom"),
    "cal_n": ("当月<br>种数", "In bloom"),
    "cal_note": ("表中所列为珠海城区的常见花期，来自本地观察归纳。同一物种在珠海的花期，通常比长江流域的记载提前一个月以上；遇暖冬或冷春，前后浮动两三周属正常。占满十二格的两种——朱槿与长春花——是真正全年不休的。",
                 "The months shown are the usual flowering window in urban Zhuhai, summarised from local observation. The same species flowers here a month or more earlier than records from the Yangtze basin suggest; a drift of two or three weeks in a warm winter or a cold spring is normal. Two of them — the China rose and the Madagascar periwinkle — fill all twelve columns and truly never stop."),
    "cal_group_n": ("{} 种", "{}"),

    # —— 分布
    "map_title": ("分布示意 · 珠海草木志", "Distribution · Flora of Zhuhai"),
    "map_desc": ("珠海七个片区的植物分布示意图：唐家湾、老香洲、情侣路、吉大、拱北、横琴、金湾，各区常见物种一览。",
                 "What grows where in Zhuhai: seven districts — Tangjiawan, Old Xiangzhou, Lovers' Road, Jida, Gongbei, Hengqin, Jinwan — and the plants recorded in each."),
    "map_h": ("分布示意", "Distribution"),
    "map_p": ("同一座城市里，草木也分地段。海边的树种抗盐，老街的树种耐修剪，新区的树种要长得快。这张图画的是七个片区的位置关系与各自的常见物种——它不是地图，只是一份关系示意图。",
              "Within a single city, plants keep to their own districts. Seaside trees must tolerate salt; old-town trees must tolerate pruning; new-town trees must grow fast. What follows is where seven districts sit in relation to one another and what grows in each — not a map, only a diagram of relationships."),
    "map_cap1": ("位置关系示意 · 非比例尺 · 不作导航使用", "Schematic · not to scale · not for navigation"),
    "map_cap2": ("七个片区共记录 {} 种，另 {} 种全城可见", "Seven districts, {} species recorded; {} more occur citywide"),
    "map_sh": ("← 左右滑动查看全图 →", "← Scroll sideways for the whole diagram →"),
    "map_note": ("片区划分依日常称呼，与行政区划不完全对应。「可见于」表示该物种在片区内的道路、公园或庭院中被记录到，并不意味它只生长于此。",
                 "The districts follow everyday usage and do not match administrative boundaries exactly. 'Recorded in' means the species has been noted on roads, in parks or in gardens there; it does not mean it grows nowhere else."),
    "map_more": ("等 {} 种", "…{} species"),
    "map_node": ("{} · {} 种", "{} · {} spp."),
    "map_citywide": ("全城", "Citywide"),
    "map_sea": ("伶 仃 洋", "Lingding"),
    "map_sea2": ("南 海", "South China Sea"),
    "map_aria": ("珠海各片区植物分布示意图，非比例尺", "Schematic diagram of plant distribution across the districts of Zhuhai; not to scale"),

    # —— 关于
    "about_title": ("编例与说明 · 珠海草木志", "About this Guide · Flora of Zhuhai"),
    "about_desc": ("珠海草木志的编写说明：分类方式、花期判定、插画来源与参考依据。",
                   "How this guide is put together: the classification, how flowering months are decided, where the plates come from, and the works consulted."),
    "about_h": ("编例", "Editorial Notes"),

    # —— 404
    "nf_title": ("页面走失 · 珠海草木志", "Page not found · Flora of Zhuhai"),
    "nf_desc": ("这一页不见踪迹。", "This page is missing."),
    "nf_h": ("这一页，落进了草丛里", "This page has fallen into the undergrowth"),
    "nf_p": ("你要找的页面大概被风带走了。不如回到封面，从一棵榕树重新开始。",
             "Whatever you were looking for has most likely been carried off by the wind. Go back to the beginning and start again from a banyan."),
    "nf_home": ("回到封面", "Back to the cover"),
    "nf_atlas": ("翻看图鉴", "Open the atlas"),
}


def t(key, *args):
    zh, en = TXT[key]
    s = en if LANG == "en" else zh
    return s.format(*args) if args else s


# ---------------------------------------------------------------- helpers

def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def flower_text(months):
    if not months:
        return "—" if LANG == "en" else "——"
    groups, cur = [], [months[0]]
    for m in months[1:]:
        if m == cur[-1] + 1:
            cur.append(m)
        else:
            groups.append(cur)
            cur = [m]
    groups.append(cur)
    if LANG == "en":
        if len(months) == 12:
            return "All year"
        if len(months) >= 8:
            return f"{MON[months[0] - 1]}–{MON[months[-1] - 1]}"
        parts = [MON[g[0] - 1] if len(g) == 1 else f"{MON[g[0] - 1]}–{MON[g[-1] - 1]}"
                 for g in groups]
        return ", ".join(parts)
    if len(months) == 12:
        return "全年"
    if len(months) >= 8:
        return f"{months[0]}–{months[-1]} 月"
    out = []
    for g in groups:
        out.append(str(g[0]) if len(g) == 1 else f"{g[0]}–{g[-1]}")
    return "、".join(out) + " 月"


def localize(html):
    """英文站：站内链接改到 /en，并收紧拉丁字母的字距"""
    html = html.replace('href="/"', 'href="__ROOT__"')
    html = re.sub(r'href="/(?!/|en/|assets/)', 'href="/en/', html)
    html = html.replace('href="__ROOT__"', 'href="/en"')
    html = html.replace('src="../assets/', 'src="/assets/')
    # 拉丁字母不需要汉字的字距
    html = html.replace("letter-spacing:.1em", "letter-spacing:.02em")
    html = html.replace("letter-spacing:.08em", "letter-spacing:.01em")
    html = html.replace("letter-spacing:.14em", "letter-spacing:.08em")
    html = html.replace('<html lang="zh-CN">', '<html lang="en">')
    html = html.replace('content="zh_CN"', 'content="en_GB"')
    return html


def write_page(rel, html):
    if LANG == "en":
        html = localize(html)
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(html, encoding="utf-8")


def nav(prefix, active, alt_href="/en", alt_label="EN"):
    items = [
        ("", "nav_home", "home"),
        ("atlas", "nav_atlas", "atlas"),
        ("calendar", "nav_calendar", "calendar"),
        ("map", "nav_map", "map"),
        ("roster", "nav_roster", "roster"),
        ("about", "nav_about", "about"),
    ]
    lis = []
    for href, key, k in items:
        cls = ' class="is-active"' if k == active else ""
        lis.append(f'<a href="{prefix}{href}"{cls}>{t(key)}</a>')
    lang_attr = "zh-CN" if LANG == "en" else "en"
    lis.append(f'<a class="nav__lang" href="{alt_href}" hreflang="{lang_attr}">{alt_label}</a>')
    return "\n        ".join(lis)


def head(title, prefix, desc, active, path="/", extra_css=""):
    zh_path = path
    en_path = "/en" if zh_path == "/" else "/en" + zh_path
    if LANG == "zh":
        self_path, alt_href, alt_label = zh_path, en_path, "EN"
    else:
        self_path, alt_href, alt_label = en_path, zh_path, "中文"
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
<meta property="og:site_name" content="{t('brand')}">
<meta property="og:locale" content="zh_CN">
<meta property="og:url" content="{SITE}{self_path}">
<meta property="og:image" content="{SITE}/assets/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{SITE}{self_path}">
<link rel="alternate" hreflang="zh-CN" href="{SITE}{zh_path}">
<link rel="alternate" hreflang="en" href="{SITE}{en_path}">
<link rel="alternate" hreflang="x-default" href="{SITE}{zh_path}">
<link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{prefix}assets/css/style.css">
{extra_css}
</head>
<body>
<header class="site-head">
  <div class="site-head__inner">
    <a class="brand" href="{prefix}">
      <span class="brand__name">{t('brand')}</span>
      <span class="brand__latin">{t('brand_sub')}</span>
    </a>
    <nav class="nav">
        {nav(prefix, active, alt_href, alt_label)}
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
        <h3 class="foot__title">{t('brand')}</h3>
        <p class="foot__p">{t('foot_p')}</p>
      </div>
      <div>
        <div class="foot__k">BROWSE</div>
        <div class="foot__links">
          <a href="{prefix}atlas">{t('foot_atlas')}</a>
          <a href="{prefix}calendar">{t('foot_calendar')}</a>
          <a href="{prefix}map">{t('foot_map')}</a>
          <a href="{prefix}roster">{t('foot_roster')}</a>
          <a href="{prefix}about">{t('foot_about')}</a>
        </div>
      </div>
      <div>
        <div class="foot__k">NOTE</div>
        <div class="foot__links">
          <span style="color:var(--ink-faint);font-size:13.5px;line-height:1.9">{t('foot_note')}</span>
        </div>
      </div>
    </div>
    <div class="foot__end">
      <span>{t('foot_where')}</span>
      <span>{t('foot_count', len(PLANTS), len({p['family'] for p in PLANTS}))}</span>
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
    alt = t("card_alt", esc(p["name"]), esc(p["latin"]))
    return f"""      <a class="card reveal" href="{prefix}species/{p['slug']}" data-cat="{p['cat']}" data-months="{','.join(map(str, p['months']))}" data-name="{esc(p['name'])} {esc(p['latin'])} {esc(p['alias'])} {esc(p['family'])}">
        <div class="card__plate">
          <img src="{img}" alt="{alt}" loading="lazy" width="900" height="1125">
        </div>
        <div class="card__body">
          <div class="card__no">No. {p['no']} · {cat['name']}</div>
          <h3 class="card__name">{esc(p['name'])}</h3>
          <div class="card__latin">{esc(p['latin'])}</div>
          {lead}
          <div class="card__foot">
            <span>{t('card_bloom', flower_text(p['months']))}</span>
            <span>{esc(p['family'])}</span>
          </div>
        </div>
      </a>"""


# ---------------------------------------------------------------- 首页

def build_index():
    by_month = {m: [] for m in range(1, 13)}
    for p in PLANTS:
        for m in p["months"]:
            by_month[m].append(p)
    maxn = max(len(v) for v in by_month.values())

    cols = []
    for m in range(1, 13):
        n = len(by_month[m])
        pct = int(round(n / maxn * 100))
        if LANG == "en":
            aria = f"{MON[m-1]} almanac, {n} species in bloom"
        else:
            aria = f"{m} 月花历，{n} 种植物开花"
        cols.append(
            f"""      <div class="almanac__col" data-month="{m}" role="button" tabindex="0" aria-label="{aria}">
        <div class="almanac__m">{ROMAN[m-1]}</div>
        <div class="almanac__plot"><span style="height:{pct}%"></span></div>
        <div class="almanac__n">{n}</div>
      </div>"""
        )

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

    picks = ["delonix-regia", "ficus-microcarpa", "plumeria-rubra", "mangifera-indica",
             "bauhinia-blakeana", "handroanthus-chrysanthus", "bombax-ceiba",
             "roystonea-regia", "bougainvillea-spectabilis", "ixora-chinensis"]
    pickmap = {p["slug"]: p for p in PLANTS}
    cards = "\n".join(card_html(pickmap[s], show_lead=False) for s in picks)

    stats = f"""        <div><b>{len(PLANTS) + len(ARCHIVE)}</b>{t('stat_species')}</div>
        <div><b>{len(CATS)}</b>{t('stat_vols')}</div>
        <div><b>22.5{'°' if LANG == 'en' else '℃'}</b>{t('stat_temp')}</div>
        <div><b>2,300</b>{t('stat_sun')}</div>"""

    nfam = len({p["family"] for p in PLANTS})

    html = head(t("home_title"), "/", t("home_desc"), "home", "/")
    html += f"""
<main>
  <section class="hero">
    <div class="wrap hero__inner">
      <div class="hero__line">
        <span class="tick"></span>
        <span class="eyebrow">Zhuhai · Guangdong<span class="hide-sm"> · 22°16′N 113°34′E</span></span>
      </div>
      <h1>{t('hero_h1')}</h1>
      <p class="hero__note">{t('hero_note')}</p>
      <p class="hero__sub">{t('hero_sub')}</p>
      <div class="hero__latin">A warm subtropical–tropical maritime transition, evergreen all year round.</div>
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
          <h2>{t('vol_h')}</h2>
        </div>
        <p>{t('vol_p')}</p>
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
          <h2>{t('cal_h')}</h2>
        </div>
        <p>{t('cal_p')}</p>
      </div>
      <div class="almanac">
{chr(10).join(cols)}
      </div>
      <div style="margin-top:30px;display:flex;justify-content:flex-end">
        <a href="/calendar" class="chip" style="padding:10px 24px;font-size:12.5px">{t('cal_more')}</a>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="wrap">
      <div class="section__head">
        <div>
          <div class="eyebrow">Selected</div>
          <h2>{t('pick_h')}</h2>
        </div>
        <p>{t('pick_p')}</p>
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
          <h2>{t('why_h')}</h2>
        </div>
        <p>{t('why_p')}</p>
      </div>
      <div style="display:grid;grid-template-columns:1fr;gap:28px;max-width:760px;font-size:16px;line-height:2.05;color:var(--ink-soft)">
        <p style="margin:0">{t('why_1')}</p>
        <p style="margin:0">{t('why_2')}</p>
        <p style="margin:0">{t('why_3')}</p>
      </div>
    </div>
  </section>

  <section class="section section--tight">
    <div class="wrap" style="border-top:1px solid var(--rule);padding-top:44px;display:flex;flex-wrap:wrap;gap:24px;justify-content:space-between;align-items:center">
      <div>
        <div class="eyebrow">Appendix</div>
        <h2 style="margin:10px 0 6px;font-size:26px;font-weight:400;letter-spacing:.08em">{t('idx_h', nfam)}</h2>
        <p style="margin:0;font-size:14px;color:var(--ink-faint)">{t('idx_p')}</p>
      </div>
      <a href="/roster" class="chip" style="padding:12px 26px;font-size:13px">{t('idx_more')}</a>
    </div>
  </section>
</main>
"""
    html += foot("/")
    write_page("index.html", html)


# ---------------------------------------------------------------- 图鉴

def build_atlas():
    cards = "\n".join(card_html(p) for p in PLANTS)
    chips = [f'<button class="chip is-on" data-cat="all">{t("atlas_all")}</button>']
    for c in CATS:
        chips.append(f'<button class="chip" data-cat="{c["id"]}">{c["name"]}</button>')

    html = head(t("atlas_title"), "/", t("atlas_desc", len(PLANTS)), "atlas", "/atlas")
    html += f"""
<main>
  <section class="section section--tight" style="padding-bottom:28px">
    <div class="wrap">
      <div class="eyebrow">Atlas</div>
      <h1 style="margin:12px 0 14px;font-size:clamp(32px,5vw,52px);font-weight:400;letter-spacing:.1em">{t('atlas_h')}</h1>
      <p style="margin:0;max-width:600px;font-size:15.5px;line-height:2;color:var(--ink-soft)">{t('atlas_p', len(PLANTS))}</p>
    </div>
  </section>

  <div class="filters">
    <div class="wrap filters__inner">
      {''.join(chips)}
      <div class="search">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color:var(--ink-faint);flex:none"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/></svg>
        <input type="search" id="q" placeholder="{t('atlas_search')}" aria-label="{t('atlas_search_aria')}">
      </div>
    </div>
  </div>

  <section class="section" style="padding-top:44px">
    <div class="wrap">
      <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:26px">
        <div class="count" id="count">{t('atlas_count', len(PLANTS))}</div>
        <button class="chip" id="reset" style="display:none">{t('atlas_reset')}</button>
      </div>
      <div class="grid" id="grid">
{cards}
      </div>
      <div class="empty" id="empty" style="display:none">{t('atlas_empty')}</div>
    </div>
  </section>
</main>
"""
    html += foot("/")
    write_page("atlas.html", html)


# ---------------------------------------------------------------- 详情页

def build_species():
    (OUT / "species").mkdir(exist_ok=True)
    for n, p in enumerate(PLANTS):
        cat = CATMAP[p["cat"]]
        prev_p = PLANTS[n - 1]
        next_p = PLANTS[(n + 1) % len(PLANTS)]
        tags = "".join(f'<span class="tag">{esc(x)}</span>' for x in p["tags"])
        shots = PHOTOS.get(p["slug"], [])
        field = ""
        if shots:
            figs = []
            for k, ph in enumerate(shots[:2]):
                cls = "field__item--wide" if k == 0 else "field__item--tall"
                figs.append(f'''
        <figure class="field__item {cls}">
          <div class="field__frame">
            <img src="/assets/img/field/{ph['file']}" alt="{t('sp_img_alt', esc(p['name']))}" loading="lazy">
          </div>
          <figcaption class="field__cap">
            <span>{esc(ph['caption'])}</span>
            <span>{esc(ph['credit'])}</span>
          </figcaption>
        </figure>''')
            field = f'''
    <section class="field">
      <div class="field__head">
        <h2 class="field__title">{t('field_title')}</h2>
        <span class="field__sub">{t('field_sub')}</span>
      </div>
      <div class="field__grid">{''.join(figs)}
      </div>
    </section>'''
        habit_note = t("evergreen") if p["evergreen"] else t("deciduous")

        if LANG == "en":
            desc = t("sp_desc", p["name"], p["latin"], p["family"], p["genus"],
                     p["habit"], flower_text(p["months"]), p["lead"])
        else:
            desc = (f"{p['name']}（{p['latin']}），{p['family']}{p['genus']}，"
                    f"{p['habit']}，花期{flower_text(p['months'])}。{p['lead']}")

        html = head(t("sp_title", p["name"], p["latin"]), "/", desc,
                    "atlas", f"/species/{p['slug']}")
        html += f"""
<main class="detail">
  <div class="wrap">
    <div class="crumbs">
      <a href="/">{t('crumb_home')}</a><span>/</span>
      <a href="/atlas?cat={p['cat']}">{cat['name']}</a><span>/</span>
      <span style="color:var(--ink-soft)">{p['name']}</span>
    </div>

    <div class="detail__grid">
      <div>
        <div class="plate reveal">
          <div class="plate__frame">
            <img src="../assets/img/{p['slug']}.webp" alt="{t('sp_alt', esc(p['name']), esc(p['latin']))}" width="900" height="1125">
          </div>
          <div class="plate__cap">
            <span>PLATE {p['no']}</span>
            <span>{esc(p['latin'])} · {t('card_plate')}</span>
          </div>
        </div>
        <div class="tagrow">{tags}</div>
      </div>

      <div>
        <div class="detail__head">
          <div class="detail__no">No. {p['no']} — {cat['name']}</div>
          <h1 class="detail__name">{esc(p['name'])}</h1>
          <div class="detail__latin">{esc(p['latin'])}</div>
          <div class="detail__alias">{esc(p['family'])} · {esc(p['genus'])} · {t('alias', esc(p['alias']))}</div>
          <p class="detail__lead">{esc(p['lead'])}</p>
          <p class="detail__body">{esc(p['body'])}</p>
        </div>

        <dl class="facts">
          <div class="facts__item"><dt>{t('f_habit')}</dt><dd>{esc(p['habit'])}</dd></div>
          <div class="facts__item"><dt>{t('f_height')}</dt><dd>{esc(p['height'])}</dd></div>
          <div class="facts__item"><dt>{t('f_bloom')}</dt><dd>{flower_text(p['months'])}<a class="factlink" href="/calendar">{t('f_cal')}</a></dd></div>
          <div class="facts__item"><dt>{t('f_color')}</dt><dd>{esc(p['color'])}</dd></div>
          <div class="facts__item"><dt>{t('f_origin')}</dt><dd style="font-size:15px;line-height:1.7">{esc(p['origin'])}</dd></div>
          <div class="facts__item"><dt>{t('f_leaf')}</dt><dd>{habit_note}</dd></div>
        </dl>

        <div class="parts">
          <div class="parts__row"><div class="parts__k">{t('p_leaf')}</div><div class="parts__v">{esc(p['leaf'])}</div></div>
          <div class="parts__row"><div class="parts__k">{t('p_flower')}</div><div class="parts__v">{esc(p['flower'])}</div></div>
          <div class="parts__row"><div class="parts__k">{t('p_where')}</div><div class="parts__v">{esc(p['where'])}</div></div>
        </div>

        <div class="note">
          <b>{t('note')}</b>
          {esc(p['note'])}
        </div>
      </div>
    </div>
{field}
    <div class="adjacent">
      <a href="/species/{prev_p['slug']}">
        <div class="adjacent__k">{t('prev')}</div>
        <div class="adjacent__n">{esc(prev_p['name'])}</div>
        <div class="adjacent__l">{esc(prev_p['latin'])}</div>
      </a>
      <a href="/species/{next_p['slug']}">
        <div class="adjacent__k">{t('next')}</div>
        <div class="adjacent__n">{esc(next_p['name'])}</div>
        <div class="adjacent__l">{esc(next_p['latin'])}</div>
      </a>
    </div>
  </div>
</main>
"""
        html += foot("/")
        write_page(f"species/{p['slug']}.html", html)


# ---------------------------------------------------------------- 科属索引

FAMILY_LATIN = {
    "豆科": "Fabaceae", "桑科": "Moraceae", "夹竹桃科": "Apocynaceae",
    "锦葵科": "Malvaceae", "棕榈科": "Arecaceae", "紫葳科": "Bignoniaceae",
    "石蒜科": "Amaryllidaceae", "漆树科": "Anacardiaceae", "楝科": "Meliaceae",
    "茜草科": "Rubiaceae", "桃金娘科": "Myrtaceae", "千屈菜科": "Lythraceae",
    "芸香科": "Rutaceae", "马鞭草科": "Verbenaceae", "樟科": "Lauraceae",
    "叶下珠科": "Phyllanthaceae", "使君子科": "Combretaceae", "木兰科": "Magnoliaceae",
    "金缕梅科": "Hamamelidaceae", "紫草科": "Boraginaceae", "黄杨科": "Buxaceae",
    "马钱科": "Loganiaceae", "五加科": "Araliaceae", "大戟科": "Euphorbiaceae",
    "紫茉莉科": "Nyctaginaceae", "木樨科": "Oleaceae", "菊科": "Asteraceae",
    "美人蕉科": "Cannaceae", "莲科": "Nelumbonaceae", "睡莲科": "Nymphaeaceae",
    "竹芋科": "Marantaceae", "天南星科": "Araceae", "鹤望兰科": "Strelitziaceae",
    "苏铁科": "Cycadaceae", "露兜树科": "Pandanaceae", "木麻黄科": "Casuarinaceae",
}


def build_roster():
    groups = {}
    for p in PLANTS:
        groups.setdefault(p["family"], []).append(p)

    blocks = []
    for fam, ps in sorted(groups.items(),
                          key=lambda kv: (-len(kv[1]), -max(int(x["no"]) for x in kv[1]))):
        items = "".join(
            f'<li><a href="/species/{p["slug"]}"><span class="fam__sp">{esc(p["name"])}</span>'
            f'<span class="fam__sci">{esc(p["latin"])}</span>'
            f'<span class="fam__f">{flower_text(p["months"])}</span></a></li>'
            for p in sorted(ps, key=lambda x: x["no"])
        )
        blocks.append(f"""      <section class="fam">
        <div class="fam__head">
          <h2 class="fam__cn">{esc(fam)}</h2>
          <span class="fam__lat">{esc(FAMILY_LATIN.get(fam, ""))}</span>
          <span class="fam__n">{len(ps):02d}</span>
        </div>
        <ul class="fam__list">{items}</ul>
      </section>""")

    html = head(t("roster_title"), "/", t("roster_desc", len(PLANTS)),
                "roster", "/roster")
    html += f"""
<main>
  <section class="section section--tight">
    <div class="wrap">
      <div class="eyebrow">Index · By Family</div>
      <h1 style="margin:12px 0 14px;font-size:clamp(32px,5vw,52px);font-weight:400;letter-spacing:.1em">{t('roster_h')}</h1>
      <p style="margin:0;max-width:660px;font-size:15.5px;line-height:2.05;color:var(--ink-soft)">{t('roster_p', len(groups))}</p>
    </div>
  </section>

  <section class="section" style="padding-top:16px">
    <div class="wrap">
      <div class="famgrid">
{chr(10).join(blocks)}
      </div>
    </div>
  </section>
</main>
"""
    html += foot("/")
    write_page("roster.html", html)


# ---------------------------------------------------------------- 关于

ABOUT = [
    (None, None,
     ["本志收录珠海市城区（香洲、吉大、拱北、横琴、唐家湾、金湾）道路、公园、居住区与海岸带最常见的园林植物七十六种，全部单独成篇。"],
     ["This guide covers the seventy-six commonest ornamental plants of urban Zhuhai — Xiangzhou, Jida, Gongbei, Hengqin, Tangjiawan and Jinwan — along its roads, parks, housing estates and coast. Every one of them has an entry of its own."]),
    ("一 · 分类", "I. Classification",
     ["卷次的划分依据植物在城市中的角色，而非分类学亲缘：<strong>行道树</strong>指承担遮荫与街道骨架的乔木；<strong>观花乔木</strong>指以花期观赏为主要功能的乔木；<strong>绿篱灌木</strong>指用于分隔、围合、修剪成形的灌木；<strong>地被与草花</strong>指贴地覆盖的草本；<strong>棕榈与滨海</strong>指棕榈科及典型海岸带植物。因此凤凰木属观花乔木而不属行道树，尽管它同样种在路边。"],
     ["The volumes are divided by the part a plant plays in the city, not by taxonomic kinship. <strong>Street Trees</strong> are the trees that carry the shade and the armature of the street; <strong>Flowering Trees</strong> are grown chiefly for their bloom; <strong>Hedges &amp; Shrubs</strong> are used to divide, enclose and be clipped into shape; <strong>Groundcover &amp; Flowers</strong> are the herbs that cover the ground; <strong>Palms &amp; the Coast</strong> covers the Arecaceae and the characteristic plants of the shoreline. That is why the flamboyant is filed as a flowering tree rather than a street tree, although it is planted along the road just the same."]),
    ("二 · 学名与科属", "II. Names and Families",
     ["学名采用现行接受名。科级分类依 APG IV 系统，部分传统科名（如木棉科、八角金盘科）已并入锦葵科、五加科，文中统一使用新科名，并在必要处注明旧名沿革。属名与种加词以斜体排印，命名人缩写从略。"],
     ["Scientific names follow currently accepted usage. Families follow APG IV; several traditional ones — the Bombacaceae, the Araliaceae's former segregates — have been sunk into the Malvaceae and the Araliaceae, and the modern names are used throughout, with the older usage noted where it matters. Genus and specific epithet are italicised; author abbreviations are omitted."]),
    ("三 · 花期", "III. Flowering Seasons",
     ["所标月份为珠海城区的常见花期区间，来自本地观察记录的归纳，而非植物志的全国性数据。同一物种在珠海的花期往往比其在长江流域的记载提前一个月以上；遇暖冬或冷春，前后浮动两至三周属正常。花历中的柱状条数代表当月开花的物种数量；另设独立的<strong>十二月花历</strong>页，以逐月色带呈现全部物种的花期分布。"],
     ["The months given are the usual flowering window in urban Zhuhai, generalised from local observation rather than from nationwide flora accounts. A species here often flowers a month or more earlier than Yangtze-basin records suggest; two or three weeks of drift in a warm winter or a cold spring is normal. The bars in the almanac on the front page show how many species are in bloom in each month; the separate <strong>Bloom Calendar</strong> page lays out every species as a band of colour across the year."]),
    ("四 · 插图", "IV. Plates and Photographs",
     ["页内图谱为风格化植物插画，模仿十八至十九世纪植物学图谱的水彩与墨线风格，用于呈现叶序、叶形、花序与花冠结构等辨识要点。它们<strong>不是实景照片</strong>，细节（如绒毛、腺点、脉序）经过简化，不能替代实地观察。若要确认物种，请以实物形态、气味与生境为准。",
      "每页另附两张实景摄影，取自 Wikimedia Commons 与 iNaturalist 的开放授权作品，拍摄地点不限于珠海，多为城市绿地中的栽培个体。摄影师与授权方式随图标注，可据此回溯原图。"],
     ["The plates are stylised botanical drawings in the manner of eighteenth- and nineteenth-century watercolour and ink plates, made to show the points that matter for recognition: leaf arrangement, leaf shape, inflorescence and corolla structure. They are <strong>not photographs</strong>. Detail — hairs, glands, venation — has been simplified, and they are no substitute for looking at the plant. To confirm an identification, go by the living form, the scent and the habitat.",
      "Each entry also carries two photographs, taken from openly licensed work on Wikimedia Commons and iNaturalist. They were not necessarily shot in Zhuhai, and mostly show cultivated individuals in urban green space. Photographer and licence are credited with each image so that the original can be traced."]),
    ("五 · 安全", "V. Safety",
     ["名录中标注「有毒」的物种（夹竹桃、软枝黄蝉、长春花、文殊兰等）含强心苷或生物碱，误食可致中毒；修剪或折断时流出的白色乳汁亦可能引起皮肤过敏。观赏即可，勿采、勿食、勿让儿童含咬。"],
     ["The species marked poisonous — oleander, golden trumpet, Madagascar periwinkle, the spider lily — contain cardiac glycosides or alkaloids and will poison you if eaten. The white latex that runs when they are cut or broken can also bring out a skin reaction. Look, and leave them: do not pick, do not taste, and keep them out of children's mouths."]),
    ("六 · 参考", "VI. References",
     ["《中国植物志》《广东植物志》《中国景观植物》（邢福武等）、Flora of China（eFloras）、《华南常见园林植物图谱》，以及珠海市城市管理和综合执法局公布的园林绿化树种名录。物种在珠海的具体分布位置，来自编写者的实地观察。"],
     ["<em>Flora Reipublicae Popularis Sinicae</em>; <em>Flora of Guangdong</em>; <em>Landscape Plants of China</em> (Xing Fuwu et al.); <em>Flora of China</em> (eFloras); <em>A Guide to Common Garden Plants of South China</em>; and the list of approved landscape trees published by the Zhuhai Urban Management Bureau. The specific locations given for each species come from the compiler's own field observation."]),
]

ABOUT_NOTE = ("一处提醒", "A caveat",
              "本志是一份个人观察笔记，不是鉴定手册。若用于教学、工程或科研用途，请以权威植物志与标本记录为准。发现错漏，欢迎指正。",
              "This is a personal book of observations, not an identification manual. For teaching, engineering or research, rely on the standard floras and on herbarium records. Corrections are welcome.")


def build_about():
    body = []
    for item in ABOUT:
        zh_h, en_h = item[0], item[1]
        zh_ps, en_ps = item[2], item[3]
        h = en_h if LANG == "en" else zh_h
        ps = en_ps if LANG == "en" else zh_ps
        if h:
            body.append(
                f'<h2 style="font-size:22px;font-weight:400;letter-spacing:.08em;'
                f'color:var(--ink);margin:2.2em 0 .7em">{h}</h2>')
        for k, p in enumerate(ps):
            mt = ' style="margin-top:0"' if (not h and k == 0) else ' style="margin:0"'
            body.append(f'<p{mt}>{p}</p>')
    note_zh, note_en, note_pzh, note_pen = ABOUT_NOTE
    note_head = note_en if LANG == "en" else note_zh
    note_p = note_pen if LANG == "en" else note_pzh

    html = head(t("about_title"), "/", t("about_desc"), "about", "/about")
    html += f"""
<main>
  <section class="section">
    <div class="wrap" style="max-width:820px">
      <div class="eyebrow">About this guide</div>
      <h1 style="margin:12px 0 30px;font-size:clamp(32px,5vw,52px);font-weight:400;letter-spacing:.1em">{t('about_h')}</h1>

      <div style="font-size:16.5px;line-height:2.1;color:var(--ink-soft)">
        {chr(10).join('        ' + b for b in body)}

        <div class="note" style="margin-top:44px">
          <b>{note_head}</b>
          {note_p}
        </div>
      </div>
    </div>
  </section>
</main>
"""
    html += foot("/")
    write_page("about.html", html)


# ---------------------------------------------------------------- 花历

def month_runs(months):
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
            f'<span>{t("cal_group_n", len(grp))}</span></div>'
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

    tail = "".join(f"<span>{x}</span>" for x in counts)

    html = head(t("cal_title"), "/", t("cal_desc", len(PLANTS)), "calendar", "/calendar")
    html += f"""
<main>
  <section class="section section--tight" style="padding-bottom:30px">
    <div class="wrap">
      <div class="eyebrow">Almanac · Bloom Calendar</div>
      <h1 style="margin:12px 0 16px;font-size:clamp(32px,5vw,52px);font-weight:400;letter-spacing:.1em">{t('cal_h1')}</h1>
      <p style="margin:0;max-width:640px;font-size:15.5px;line-height:2.05;color:var(--ink-soft)">{t('cal_lead', len(PLANTS))}</p>
      <p id="nowline" style="margin:22px 0 0;font-family:var(--font-sans);font-size:12.5px;letter-spacing:.14em;color:var(--clay)"></p>
    </div>
  </section>

  <section class="section" style="padding-top:26px">
    <div class="wrap">
      <div class="bloom__legend">{legend}</div>
      <p class="scrollhint">{t('cal_sh')}</p>
      <div class="bloom" data-counts="{','.join(map(str, counts))}">
        <div class="bloom__scroll">
          <div class="bloom__inner">
            <div class="bloom__head">
              <div class="bloom__cap">SPECIES</div>
              <div class="bloom__months">{head_month}</div>
              <div class="bloom__cap">{t('cal_f')}</div>
            </div>
{chr(10).join(rows)}
            <div class="bloom__tail">
              <div class="bloom__cap">{t('cal_n')}</div>
              <div class="bloom__n">{tail}</div>
              <div class="bloom__cap"></div>
            </div>
          </div>
        </div>
      </div>
      <p style="margin:26px 0 0;font-size:13.5px;line-height:1.95;color:var(--ink-faint);max-width:660px">{t('cal_note')}</p>
    </div>
  </section>
</main>
"""
    html += foot("/")
    write_page("calendar.html", html)


# ---------------------------------------------------------------- 分布示意

PLACES = [
    {"no": "I", "name": "唐家湾", "en": "Tangjiawan", "x": 824, "y": 118,
     "lx": 804, "ly": 122, "anchor": "end",
     "kw": ["唐家", "淇澳"],
     "desc": "珠海北端的老镇。青砖巷、祠堂前的百年榕树，往东是淇澳岛的红树林与海岸防风林。中山大学珠海校区也在这里，校园里的树种几乎是半部图鉴。",
     "desc_en": "The old town at the northern tip of the city. Grey-brick lanes, century-old banyans before the ancestral halls, and to the east the mangroves and coastal shelterbelt of Qi'ao Island. Sun Yat-sen University's Zhuhai campus is here too, and its planting is very nearly half of this atlas."},
    {"no": "II", "name": "老香洲", "en": "Old Xiangzhou", "x": 758, "y": 238,
     "lx": 738, "ly": 242, "anchor": "end",
     "kw": ["香洲", "凤凰路", "南坑", "柠溪", "前山", "人民东", "人民西"],
     "desc": "城市最早的一批街道。凤凰路的骑楼、南坑的市场、柠溪与南屏的老小区，行道树种得最密，树冠把整条街盖成隧道。",
     "desc_en": "Among the city's first streets. The arcades of Fenghuang Road, the market at Nankeng, the old estates of Ningxi and Nanping — the street trees here are planted more densely than anywhere else, their crowns closing the road into a tunnel."},
    {"no": "III", "name": "情侣路", "en": "Lovers' Road", "x": 700, "y": 330,
     "lx": 680, "ly": 334, "anchor": "end",
     "kw": ["情侣路", "海滨"],
     "desc": "全长约五十公里的滨海大道。海风、盐雾、台风与烈日同时作用，留下的都是些硬骨头：榕、棕榈、木麻黄与露兜。",
     "desc_en": "Some fifty kilometres of coastal boulevard. Sea wind, salt spray, typhoon and hard sun all at once, and what survives is tough: figs, palms, casuarinas and screw pines."},
    {"no": "IV", "name": "吉大", "en": "Jida", "x": 618, "y": 404,
     "lx": 598, "ly": 408, "anchor": "end",
     "kw": ["吉大", "九洲"],
     "desc": "商业与旧宅混杂的一段。庭院树与行道树在这里几乎分不出界线——糖胶树的塔形、假槟榔的灰白柱子，都长在离人行道两米的地方。",
     "desc_en": "Commerce and old houses mixed together. Garden trees and street trees are barely separable here: the tiered crown of the blackboard tree and the grey column of the Alexandra palm both stand two metres from the pavement."},
    {"no": "V", "name": "拱北", "en": "Gongbei", "x": 512, "y": 452,
     "lx": 512, "ly": 430, "anchor": "middle", "above": True,
     "kw": ["拱北", "湾仔", "南屏"],
     "desc": "口岸一带，人流与车流最急。这里种的都是最耐活的花木：高山榕、糖胶树、黄金榕——被反复修剪，依然认真地长。",
     "desc_en": "The border crossing, where people and traffic move fastest. What is planted is the hardiest flowering stock — banyans, blackboard trees, golden figs — cut back over and over, and still growing in earnest."},
    {"no": "VI", "name": "横琴", "en": "Hengqin", "x": 388, "y": 466,
     "lx": 388, "ly": 430, "anchor": "middle", "above": True,
     "kw": ["横琴"],
     "desc": "新填海的新城。树几乎都是近十年种下的：小叶榄仁、美丽异木棉、紫花风铃木。它们长得快，也还在长——一座新城的植被，要几十年才定型。",
     "desc_en": "A new town on reclaimed land. Almost every tree went in within the last ten years: Indian almond, white silk floss, pink trumpet tree. They grow fast and are still growing — the planting of a new town takes decades to settle."},
    {"no": "VII", "name": "金湾", "en": "Jinwan", "x": 214, "y": 424,
     "lx": 214, "ly": 386, "anchor": "middle", "above": True,
     "kw": ["金湾", "斗门"],
     "desc": "西侧的海岸与湿地。防风林、滩涂与咸淡水交界处的植物在这里占主导，城市化的痕迹要稀薄得多。",
     "desc_en": "The western shore, its wetlands and mudflats. Shelterbelts, tidal flats and the brackish margins dominate out here; the marks of the city are much fainter."},
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
    # 关键词是中文地名，统一拿中文原文匹配，两种语言结果才一致
    zh_where = {p["slug"]: p["where"] for p in ZH_PLANTS}
    for pl in PLACES:
        pl["plants"] = [p for p in PLANTS
                        if any(k in zh_where.get(p["slug"], "") for k in pl["kw"])]

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

    label_font = "Georgia, serif" if LANG == "en" else "Songti SC, serif"
    nodes = "".join(
        f'<g><circle cx="{pl["x"]}" cy="{pl["y"]}" r="14" fill="#3D5C4D" opacity=".07"/>'
        f'<circle cx="{pl["x"]}" cy="{pl["y"]}" r="5.4" fill="#F8F4EB" stroke="#3D5C4D" stroke-width="1.6"/>'
        f'<circle cx="{pl["x"]}" cy="{pl["y"]}" r="1.9" fill="#B25C45"/>'
        f'<text x="{pl["lx"]}" y="{pl["ly"]}" text-anchor="{pl["anchor"]}" '
        f'font-family="{label_font}" font-size="18.5" fill="#1E2A25" letter-spacing="2.6">{pl["en"] if LANG == "en" else pl["name"]}</text>'
        f'<text x="{pl["lx"]}" y="{pl["ly"] + -17}" text-anchor="{pl["anchor"]}" '
        f'font-family="PingFang SC, sans-serif" font-size="9.6" fill="#8B968E" letter-spacing="1.4">'
        f'{t("map_node", pl["no"], len(pl["plants"]))}</text></g>'
        for pl in PLACES
    )

    compass = (
        '<g transform="translate(70,74)" opacity=".55">'
        '<path d="M 0 20 L 0 -20" stroke="#3D5C4D" stroke-width="1"/>'
        '<path d="M 0 -20 L -5.5 -6 L 0 -10.5 L 5.5 -6 Z" fill="#3D5C4D"/>'
        '<text x="0" y="-28" text-anchor="middle" font-family="Georgia, serif" '
        'font-size="12" fill="#3D5C4D" letter-spacing="1">N</text></g>'
    )

    svg = f"""<svg viewBox="0 0 900 540" role="img" aria-label="{t('map_aria')}" xmlns="http://www.w3.org/2000/svg">
  <rect width="900" height="540" fill="#DCE9E9"/>
  <path d="{land}" fill="#F3ECDD"/>
  <path d="{sea}" fill="#CFE1E1" opacity=".45"/>
  {waves}
  {contours}
  {stipple}
  <path d="{coast}" fill="none" stroke="#3D5C4D" stroke-width="2" stroke-linecap="round"/>
  <text transform="translate(866,250) rotate(-90)" text-anchor="middle"
        font-family="{label_font}" font-size="{14 if LANG == 'en' else 19}" fill="#4C7B87" opacity=".34" letter-spacing="{6 if LANG == 'en' else 10}">{t('map_sea')}</text>
  <text x="600" y="512" text-anchor="middle" font-family="{label_font}" font-size="{13 if LANG == 'en' else 16}"
        fill="#4C7B87" opacity=".32" letter-spacing="{7 if LANG == 'en' else 12}">{t('map_sea2')}</text>
  {compass}
  {nodes}
</svg>"""

    cards = []
    for pl in PLACES:
        if LANG == "en":
            cards.append(place_card(pl, pl["en"], "", pl["desc_en"], pl["plants"]))
        else:
            cards.append(place_card(pl, pl["name"], pl["en"], pl["desc"], pl["plants"]))
    if citywide:
        cards.append(place_card(
            {"no": "VIII"}, t("map_citywide"), "Citywide",
            ("还有一些不挑地段的：种在每一条分车带、每一座天桥、每一个小区的围墙里。它们不专属于某个片区，而是这座城市绿化的底板。"
             if LANG == "zh" else
             "Then there are the ones that do not mind where they are put: in every central reservation, on every footbridge, inside every compound wall. They belong to no district in particular — they are the base coat of the city's planting."),
            citywide))

    html = head(t("map_title"), "/", t("map_desc"), "map", "/map")
    html += f"""
<main>
  <section class="section section--tight" style="padding-bottom:16px">
    <div class="wrap">
      <div class="eyebrow">Distribution · A Schematic View</div>
      <h1 style="margin:12px 0 16px;font-size:clamp(32px,5vw,52px);font-weight:400;letter-spacing:.1em">{t('map_h')}</h1>
      <p style="margin:0;max-width:640px;font-size:15.5px;line-height:2.05;color:var(--ink-soft)">{t('map_p')}</p>
    </div>
  </section>

  <section class="section" style="padding-top:8px;padding-bottom:34px">
    <div class="wrap">
      <figure class="mapfig">
        <div class="mapfig__scroll">{svg}</div>
        <figcaption class="mapfig__note">
          <span>{t('map_cap1')}</span>
          <span>{t('map_cap2', total_seen, len(citywide))}</span>
        </figcaption>
        <p class="scrollhint">{t('map_sh')}</p>
      </figure>
    </div>
  </section>

  <section class="section" style="padding-top:0">
    <div class="wrap">
      <div class="placegrid">
{chr(10).join(cards)}
      </div>
      <p style="margin:26px 0 0;font-size:13.5px;line-height:1.95;color:var(--ink-faint);max-width:680px">{t('map_note')}</p>
    </div>
  </section>
</main>
"""
    html += foot("/")
    write_page("map.html", html)


def place_card(pl, name, en, desc, plants):
    chips = "".join(
        f'<a href="/species/{p["slug"]}">{esc(p["name"])}</a>' for p in plants[:10]
    )
    more = ""
    if len(plants) > 10:
        more = (f'<span style="font-family:var(--font-sans);font-size:11px;color:var(--ink-faint);'
                f'padding:4px 2px">{t("map_more", len(plants))}</span>')
    sub = esc(en) if LANG == "zh" else ""
    sub_html = f'<div class="place__en">{sub}</div>' if sub else ""
    return f"""      <div class="place">
        <div class="place__no">{pl['no']}</div>
        <h3 class="place__name">{name}</h3>
        {sub_html}
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

JS = r"""/* 珠海草木志 / Flora of Zhuhai */
(function () {
  var EN = document.documentElement.lang === 'en';
  var BASE = EN ? '/en' : '';
  var MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
             'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

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
    function go() { location.href = BASE + '/atlas?month=' + col.dataset.month; }
    col.addEventListener('click', go);
    col.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); go(); }
    });
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
      line.textContent = EN
        ? MON[now - 1] + ' · ' + counts[now - 1] + ' species in bloom'
        : now + ' 月 · 全城 ' + counts[now - 1] + ' 种正在开花';
    }
  }

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
    if (state.month) bits.push(EN ? MON[state.month - 1] + ' bloom' : state.month + ' 月开花');
    countEl.textContent = EN
      ? shown + ' species' + (bits.length ? ' · ' + bits.join(' · ') : '')
      : '共 ' + shown + ' 种' + (bits.length ? ' · ' + bits.join(' · ') : '');
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
    html = head(t("nf_title"), "/", t("nf_desc"), "", "/404")
    html += f"""
<main class="section" style="min-height:60vh;display:flex;align-items:center">
  <div class="wrap" style="text-align:center">
    <div class="eyebrow">Error 404</div>
    <h1 style="margin:20px 0 16px;font-size:clamp(30px,5vw,46px);font-weight:400;letter-spacing:.1em">{t('nf_h')}</h1>
    <p style="margin:0 auto;max-width:440px;font-size:15.5px;line-height:2;color:var(--ink-soft)">{t('nf_p')}</p>
    <div style="margin-top:34px;display:flex;gap:12px;justify-content:center;flex-wrap:wrap">
      <a href="/" class="chip" style="padding:11px 26px">{t('nf_home')}</a>
      <a href="/atlas" class="chip" style="padding:11px 26px">{t('nf_atlas')}</a>
    </div>
  </div>
</main>
"""
    html += foot("/")
    write_page("404.html", html)


def build_meta_files():
    base = ["", "atlas", "calendar", "map", "roster", "about"]
    base += [f"species/{p['slug']}" for p in ZH_PLANTS]
    entries = []
    for u in base:
        for pre in ("", "en/"):
            loc = f"{SITE}/{pre}{u}"
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


def setup_assets():
    if OUT_ZH.exists():
        shutil.rmtree(OUT_ZH)
    (OUT_ZH / "assets" / "css").mkdir(parents=True)
    (OUT_ZH / "assets" / "js").mkdir(parents=True)
    shutil.copy(ROOT / "assets/css/style.css", OUT_ZH / "assets/css/style.css")
    (OUT_ZH / "assets" / "js" / "site.js").write_text(JS, encoding="utf-8")
    (OUT_ZH / "assets" / "favicon.svg").write_text(FAVICON, encoding="utf-8")
    if (ROOT / "assets" / "og.png").exists():
        shutil.copy(ROOT / "assets" / "og.png", OUT_ZH / "assets" / "og.png")

    src_img = ROOT / "assets" / "img"
    dst_img = OUT_ZH / "assets" / "img"
    dst_img.mkdir(parents=True)
    missing = []
    for p in ZH_PLANTS:
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

    for f in src_img.glob("*.webp"):
        shutil.copy(f, dst_img / f.name)
    return missing


def apply_en():
    """以中文数据为骨架，覆盖英文文案；科属改用拉丁名"""
    global PLANTS, ARCHIVE, CATS, CATMAP, PHOTOS
    en = EN.get("plants", {})
    out = []
    for p in ZH_PLANTS:
        q = dict(p)
        e = en.get(p["slug"], {})
        for k in ("name", "alias", "habit", "origin", "color", "where",
                  "lead", "body", "leaf", "flower", "note", "tags"):
            if k in e:
                q[k] = e[k]
        q["family"] = FAMILY_LATIN.get(p["family"], p["family"])
        q["genus"] = p["latin"].split()[0]
        q["height"] = (q.get("height") or "").replace("（攀援）", " (climbing)") \
                                                 .replace("（挺水）", " (emergent)") \
                                                 .replace("浮水", "Floating leaves")
        q["height"] = (q.get("height") or "").replace("（攀援）", " (climbing)") \
                                                 .replace("（挺水）", " (emergent)") \
                                                 .replace("浮水", "Floating leaves")
        out.append(q)
    PLANTS = out
    ARCHIVE = []
    cats = []
    for n, c in enumerate(ZH_CATS):
        d = dict(c)
        d["no"] = ROMAN[n] if n < 12 else c["no"]
        e = EN.get("cats", {}).get(c["id"], {})
        d["name"] = e.get("name", c["name"])
        d["lead"] = e.get("lead", c["lead"])
        d["desc"] = e.get("desc", c.get("desc", ""))
        cats.append(d)
    CATS = cats
    CATMAP = {c["id"]: c for c in cats}

    caps = EN.get("captions", {})
    PHOTOS = {}
    for k, v in ZH_PHOTOS.items():
        lst = []
        for im in v:
            d = dict(im)
            d["caption"] = caps.get(im["caption"], im["caption"])
            c = re.sub(r"^摄影 (.+)$", r"Photo: \1", im["credit"])
            d["credit"] = c.replace("示意图 · AI 生成", "Reconstruction · AI-generated")
            lst.append(d)
        PHOTOS[k] = lst


def build_lang(lang):
    global LANG, OUT
    LANG = lang
    OUT = OUT_ZH if lang == "zh" else OUT_EN
    if lang == "en":
        apply_en()
    build_index()
    build_atlas()
    build_calendar()
    build_map()
    build_species()
    build_roster()
    build_about()
    build_404()
    if lang == "zh":
        build_meta_files()


def main():
    missing = setup_assets()
    build_lang("zh")
    build_lang("en")
    print(f"built: {len(ZH_PLANTS)} species pages x 2 languages")
    if missing:
        print("MISSING IMAGES:", ", ".join(missing))


if __name__ == "__main__":
    main()
