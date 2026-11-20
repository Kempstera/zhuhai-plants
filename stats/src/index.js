/**
 * zhplants-stats v2 —— 珠海草木志的访问统计
 *
 * 设计取舍：
 *  - 无 Cookie、无第三方脚本；不保存原始 IP 与完整 UA
 *  - 唯一访客 = sha256(IP + UA + 密钥 + 日期) 的前 16 位，逐日过期，无法反查
 *  - 城市 / 地区 / 接入商来自 Cloudflare 的边缘信息，同样不落 IP
 *  - 停留时长与滚动深度由前端在离开页面时补报，按 sid 回填同一行
 */

const BOT = /bot|crawler|spider|crawling|headless|preview|monitor|curl|wget|python-requests|facebookexternalhit|slurp/i;

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    const cors = corsHeaders(req, env);

    if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: cors });

    try {
      if (url.pathname === "/hit" && req.method === "POST") return await hit(req, env, cors);
      if (url.pathname === "/stay" && req.method === "POST") return await stay(req, env, cors);
      if (url.pathname === "/stats" && req.method === "GET") return await stats(url, env, cors);
      if (url.pathname === "/export.csv" && req.method === "GET") return await exportCsv(url, env, cors);
      if (url.pathname === "/") return new Response("zhplants-stats v2\n", { headers: cors });
    } catch (e) {
      return json({ error: String((e && e.message) || e) }, 500, cors);
    }
    return json({ error: "not found" }, 404, cors);
  },
};

/* ---------------------------------------------------------------- 记录 */

async function hit(req, env, cors) {
  const ua = req.headers.get("user-agent") || "";
  if (!ua || BOT.test(ua)) return new Response(null, { status: 204, headers: cors });

  let body = {};
  try { body = await req.json(); } catch { return json({ error: "bad json" }, 400, cors); }

  const path = cleanPath(body.p);
  if (!path) return new Response(null, { status: 204, headers: cors });

  const ts = Date.now();
  const day = shanghaiDay(ts);
  const cf = req.cf || {};
  const ip = req.headers.get("cf-connecting-ip") || "0.0.0.0";
  const uv = (await sha256hex(`${ip}|${ua}|${env.UV_SALT || "zhplants"}|${day}`)).slice(0, 16);

  // 同一访客对同一页面的连续刷新，30 秒内只记一次
  const dup = await env.DB.prepare(
    "SELECT 1 FROM hits WHERE uv = ? AND path = ? AND ts > ? LIMIT 1"
  ).bind(uv, path, ts - 30000).first();
  if (dup) return new Response(null, { status: 204, headers: cors });

  await env.DB.prepare(
    `INSERT INTO hits
      (ts, day, uv, sid, path, ref, country, region, city, asn, asorg, device, browser, os, lang)
     VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`
  ).bind(
    ts, day, uv,
    cleanId(body.s),
    path,
    cleanRef(body.r),
    str(cf.country, 2), str(cf.region, 40), str(cf.city, 40),
    Number.isFinite(cf.asn) ? cf.asn : 0, str(cf.asOrganization, 60),
    deviceOf(ua), browserOf(ua), osOf(ua),
    langOf(body.l, path)
  ).run();

  return new Response(null, { status: 204, headers: cors });
}

/* 离开页面时补报停留时长与滚动深度 */
async function stay(req, env, cors) {
  let body = {};
  try { body = await req.json(); } catch { return json({ error: "bad json" }, 400, cors); }

  const sid = cleanId(body.s);
  if (!sid) return new Response(null, { status: 204, headers: cors });

  let dur = Math.round(Number(body.d));
  let scroll = Math.round(Number(body.y));
  if (!Number.isFinite(dur) || dur < 0) dur = -1;
  if (dur > 7200) dur = 7200;
  if (!Number.isFinite(scroll) || scroll < 0) scroll = -1;
  if (scroll > 100) scroll = 100;

  await env.DB.prepare(
    "UPDATE hits SET dur = ?, scroll = ? WHERE sid = ? AND dur < 0"
  ).bind(dur, scroll, sid).run();

  return new Response(null, { status: 204, headers: cors });
}

function str(v, max) {
  return typeof v === "string" ? v.trim().slice(0, max) : "";
}

function cleanId(v) {
  return typeof v === "string" && /^[a-z0-9]{6,24}$/i.test(v) ? v : "";
}

function cleanPath(p) {
  if (typeof p !== "string") return "";
  let s = p.split("?")[0].split("#")[0].trim();
  if (!s.startsWith("/") || s.length > 160) return "";
  // 去掉 .html，统一到规范路径
  s = s.replace(/\/index\.html$/, "/").replace(/\.html$/, "");
  if (s !== "/" && s.endsWith("/")) s = s.slice(0, -1);
  return s;
}

function cleanRef(r) {
  if (typeof r !== "string" || !r) return "";
  try {
    const host = new URL(r).hostname.replace(/^www\./, "");
    if (!host) return "";
    // 站内跳转不算来源
    if (host.endsWith("signupeverywhere.cc") || host.endsWith("zhuhai-plants.pages.dev")) return "";
    return host.slice(0, 60);
  } catch {
    return "";
  }
}

function deviceOf(ua) {
  if (/iPad|Tablet|PlayBook|Silk/i.test(ua)) return "tablet";
  if (/Mobile|Android|iPhone|iPod|HarmonyOS/i.test(ua)) return "mobile";
  return "desktop";
}

function browserOf(ua) {
  if (/Edg\//i.test(ua)) return "Edge";
  if (/OPR\/|Opera/i.test(ua)) return "Opera";
  if (/SamsungBrowser/i.test(ua)) return "Samsung";
  if (/Firefox\//i.test(ua)) return "Firefox";
  if (/CriOS|Chrome\//i.test(ua)) return "Chrome";
  if (/Safari\//i.test(ua)) return "Safari";
  return "Other";
}

function osOf(ua) {
  if (/iPhone|iPad|iPod/i.test(ua)) return "iOS";
  if (/Android/i.test(ua)) return "Android";
  if (/Windows/i.test(ua)) return "Windows";
  if (/Mac OS X|Macintosh/i.test(ua)) return "macOS";
  if (/Linux/i.test(ua)) return "Linux";
  return "Other";
}

function langOf(hint, path) {
  const h = String(hint || "").toLowerCase();
  if (h.startsWith("zh")) return "zh";
  if (h.startsWith("en")) return "en";
  return path.startsWith("/zh") ? "zh" : "en";
}

/* 以北京时间切日，避免凌晨的访问被算到前一天 */
function shanghaiDay(ts) {
  return new Date(ts + 8 * 3600 * 1000).toISOString().slice(0, 10);
}

async function sha256hex(s) {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

/* ---------------------------------------------------------------- 查询条件 */

function windowOf(url) {
  let days = parseInt(url.searchParams.get("days") || "30", 10);
  if (!Number.isFinite(days) || days < 0) days = 30;
  if (days > 365) days = 365;

  const today = shanghaiDay(Date.now());
  if (days === 0) return { days: 0, from: "", to: today, where: "1=1", args: [] };

  const from = shanghaiDay(Date.now() - (days - 1) * 86400000);
  return { days, from, to: today, where: "day >= ?", args: [from] };
}

/* ---------------------------------------------------------------- 读取 */

async function stats(url, env, cors) {
  const token = url.searchParams.get("token") || "";
  if (!okToken(token, env)) return json({ error: "forbidden" }, 403, cors);

  const w = windowOf(url);
  const W = w.where;

  let limit = parseInt(url.searchParams.get("limit") || "25", 10);
  if (!Number.isFinite(limit) || limit < 1 || limit > 500) limit = 25;
  let offset = parseInt(url.searchParams.get("offset") || "0", 10);
  if (!Number.isFinite(offset) || offset < 0) offset = 0;

  const [tot, daily, pages, refs, countries, cities, asns,
         devices, browsers, oses, langs, hours, durs, scrolls, detail, dcount] = await env.DB.batch([
    env.DB.prepare(
      `SELECT COUNT(*) pv, COUNT(DISTINCT uv) uv, COUNT(DISTINCT sid) sess,
              SUM(CASE WHEN dur >= 0 THEN 1 ELSE 0 END) withdur,
              AVG(CASE WHEN dur >= 0 THEN dur END) avgdur,
              MIN(ts) first, MAX(ts) last
         FROM hits WHERE ${W}`
    ).bind(...w.args),
    env.DB.prepare(
      `SELECT day, COUNT(*) pv, COUNT(DISTINCT uv) uv FROM hits WHERE ${W} GROUP BY day ORDER BY day`
    ).bind(...w.args),
    env.DB.prepare(
      `SELECT path, COUNT(*) n, COUNT(DISTINCT uv) u FROM hits WHERE ${W}
        GROUP BY path ORDER BY n DESC LIMIT 25`
    ).bind(...w.args),
    env.DB.prepare(
      `SELECT ref, COUNT(*) n FROM hits WHERE ${W} AND ref <> ''
        GROUP BY ref ORDER BY n DESC LIMIT 15`
    ).bind(...w.args),
    env.DB.prepare(
      `SELECT country, COUNT(*) n FROM hits WHERE ${W} AND country <> ''
        GROUP BY country ORDER BY n DESC LIMIT 20`
    ).bind(...w.args),
    env.DB.prepare(
      `SELECT city, country, COUNT(*) n FROM hits WHERE ${W} AND city <> ''
        GROUP BY city, country ORDER BY n DESC LIMIT 20`
    ).bind(...w.args),
    env.DB.prepare(
      `SELECT asorg, asn, COUNT(*) n FROM hits WHERE ${W} AND asorg <> ''
        GROUP BY asorg, asn ORDER BY n DESC LIMIT 15`
    ).bind(...w.args),
    env.DB.prepare(`SELECT device b, COUNT(*) n FROM hits WHERE ${W} GROUP BY device ORDER BY n DESC`).bind(...w.args),
    env.DB.prepare(`SELECT browser b, COUNT(*) n FROM hits WHERE ${W} GROUP BY browser ORDER BY n DESC`).bind(...w.args),
    env.DB.prepare(`SELECT os b, COUNT(*) n FROM hits WHERE ${W} GROUP BY os ORDER BY n DESC`).bind(...w.args),
    env.DB.prepare(`SELECT lang b, COUNT(*) n FROM hits WHERE ${W} GROUP BY lang ORDER BY n DESC`).bind(...w.args),
    env.DB.prepare(
      `SELECT CAST(strftime('%H', ts / 1000, 'unixepoch', '+8 hours') AS INTEGER) h, COUNT(*) n
         FROM hits WHERE ${W} GROUP BY h ORDER BY h`
    ).bind(...w.args),
    env.DB.prepare(
      `SELECT CASE
                WHEN dur < 0 THEN 'na'
                WHEN dur < 10 THEN '0-10'
                WHEN dur < 30 THEN '10-30'
                WHEN dur < 60 THEN '30-60'
                WHEN dur < 180 THEN '1-3'
                WHEN dur < 600 THEN '3-10'
                ELSE '10+'
              END b, COUNT(*) n
         FROM hits WHERE ${W} GROUP BY b`
    ).bind(...w.args),
    env.DB.prepare(
      `SELECT CASE
                WHEN scroll < 0 THEN 'na'
                WHEN scroll < 25 THEN '0-25'
                WHEN scroll < 50 THEN '25-50'
                WHEN scroll < 75 THEN '50-75'
                ELSE '75-100'
              END b, COUNT(*) n
         FROM hits WHERE ${W} GROUP BY b`
    ).bind(...w.args),
    env.DB.prepare(
      `SELECT ts, path, ref, country, region, city, asorg, device, browser, os, lang, dur, scroll
         FROM hits WHERE ${W} ORDER BY ts DESC LIMIT ? OFFSET ?`
    ).bind(...w.args, limit, offset),
    env.DB.prepare(`SELECT COUNT(*) n FROM hits WHERE ${W}`).bind(...w.args),
  ]);

  const all = await env.DB.prepare(
    "SELECT COUNT(*) n, COUNT(DISTINCT uv) uv, MIN(day) since, MAX(day) until FROM hits"
  ).first();

  return json({
    range: { from: w.from, to: w.to, days: w.days },
    totals: tot.results[0] || { pv: 0, uv: 0, sess: 0 },
    daily: daily.results,
    pages: pages.results,
    refs: refs.results,
    countries: countries.results,
    cities: cities.results,
    asns: asns.results,
    devices: devices.results,
    browsers: browsers.results,
    oses: oses.results,
    langs: langs.results,
    hours: hours.results,
    durations: durs.results,
    scrolls: scrolls.results,
    detail: detail.results,
    detailTotal: (dcount.results[0] || {}).n || 0,
    lifetime: all,
  }, 200, cors, 15);
}

/* ---------------------------------------------------------------- 导出 */

async function exportCsv(url, env, cors) {
  const token = url.searchParams.get("token") || "";
  if (!okToken(token, env)) return json({ error: "forbidden" }, 403, cors);

  const w = windowOf(url);
  const rows = await env.DB.prepare(
    `SELECT ts, path, ref, country, region, city, asorg, device, browser, os, lang, dur, scroll
       FROM hits WHERE ${w.where} ORDER BY ts DESC LIMIT 20000`
  ).bind(...w.args).all();

  const head = ["time", "path", "referrer", "country", "region", "city", "asn_org",
                "device", "browser", "os", "lang", "seconds", "scroll_pct"];
  const lines = [head.join(",")];
  for (const r of rows.results) {
    const cells = [
      new Date(r.ts + 8 * 3600 * 1000).toISOString().slice(0, 19).replace("T", " "),
      r.path, r.ref, r.country, r.region, r.city, r.asorg, r.device, r.browser, r.os, r.lang,
      r.dur < 0 ? "" : r.dur, r.scroll < 0 ? "" : r.scroll,
    ];
    lines.push(cells.map(csvCell).join(","));
  }

  return new Response("\uFEFF" + lines.join("\r\n"), {
    headers: {
      ...cors,
      "content-type": "text/csv; charset=utf-8",
      "content-disposition": `attachment; filename="zhplants-visits-${w.days}d.csv"`,
      "cache-control": "no-store",
    },
  });
}

function csvCell(v) {
  const s = v === null || v === undefined ? "" : String(v);
  return /[",\r\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
}

/* ---------------------------------------------------------------- 工具 */

// 口令只认 wrangler secret 里配的 ADMIN_TOKEN
function okToken(t, env) {
  return same(t, env.ADMIN_TOKEN || "");
}

function same(a, b) {
  if (!a || !b || a.length !== b.length) return false;
  let out = 0;
  for (let i = 0; i < a.length; i++) out |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return out === 0;
}

function corsHeaders(req, env) {
  const origin = req.headers.get("origin") || "";
  const allowed = (env.ALLOWED_HOSTS || "").split(",").map((s) => s.trim()).filter(Boolean);
  let host = "";
  try { host = new URL(origin).hostname; } catch {}
  const ok = host && (
    allowed.includes(host) ||
    /^[a-z0-9-]+\.zhuhai-plants\.pages\.dev$/.test(host)
  );
  const h = { "access-control-allow-methods": "GET,POST,OPTIONS", "access-control-allow-headers": "content-type" };
  if (ok) {
    h["access-control-allow-origin"] = origin;
    h["vary"] = "origin";
  }
  return h;
}

function json(obj, status, cors, cache) {
  const h = { "content-type": "application/json; charset=utf-8", ...cors };
  if (cache) h["cache-control"] = `public, max-age=${cache}`;
  return new Response(JSON.stringify(obj), { status, headers: h });
}
