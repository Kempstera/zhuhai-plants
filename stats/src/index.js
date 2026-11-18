/**
 * zhplants-stats —— 珠海草木志的访问统计
 *
 * 设计取舍：
 *  - 无 Cookie、无第三方脚本；不保存原始 IP 与完整 UA
 *  - 唯一访客 = sha256(IP + UA + 密钥 + 日期) 的前 16 位，逐日过期，无法反查
 *  - 只记路径、来源域名、国家、设备类别，够回答「谁在看、从哪来、看什么」
 */

const BOT = /bot|crawler|spider|crawling|headless|preview|monitor|curl|wget|python-requests|facebookexternalhit|slurp/i;

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    const cors = corsHeaders(req, env);

    if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: cors });

    try {
      if (url.pathname === "/hit" && req.method === "POST") return await hit(req, env, cors);
      if (url.pathname === "/stats" && req.method === "GET") return await stats(url, env, cors);
      if (url.pathname === "/") return new Response("zhplants-stats\n", { headers: cors });
    } catch (e) {
      return json({ error: String(e && e.message || e) }, 500, cors);
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
  const country = (req.cf && req.cf.country) || "";
  const device = deviceOf(ua);
  const lang = path.startsWith("/en") ? "en" : "zh";
  const ref = cleanRef(body.r, req.headers.get("origin") || "");
  const ip = req.headers.get("cf-connecting-ip") || "0.0.0.0";
  const uv = (await sha256hex(`${ip}|${ua}|${env.UV_SALT || "zhplants"}|${day}`)).slice(0, 16);

  // 同一访客对同一页面的连续刷新，30 秒内只记一次
  const dup = await env.DB.prepare(
    "SELECT 1 FROM hits WHERE uv = ? AND path = ? AND ts > ? LIMIT 1"
  ).bind(uv, path, ts - 30000).first();
  if (dup) return new Response(null, { status: 204, headers: cors });

  await env.DB.prepare(
    "INSERT INTO hits (ts, day, path, ref, country, device, lang, uv) VALUES (?,?,?,?,?,?,?,?)"
  ).bind(ts, day, path, ref, country, device, lang, uv).run();

  return new Response(null, { status: 204, headers: cors });
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

function cleanRef(r, origin) {
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

/* 以北京时间切日，避免凌晨的访问被算到前一天 */
function shanghaiDay(ts) {
  return new Date(ts + 8 * 3600 * 1000).toISOString().slice(0, 10);
}

async function sha256hex(s) {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

/* ---------------------------------------------------------------- 读取 */

async function stats(url, env, cors) {
  const token = url.searchParams.get("token") || "";
  if (!same(token, env.ADMIN_TOKEN || "")) return json({ error: "forbidden" }, 403, cors);

  let days = parseInt(url.searchParams.get("days") || "30", 10);
  if (!Number.isFinite(days) || days < 1) days = 30;
  if (days > 180) days = 180;

  const today = shanghaiDay(Date.now());
  const from = shanghaiDay(Date.now() - (days - 1) * 86400000);
  const W = "day >= ?";

  const [tot, daily, pages, refs, countries, devices, langs, hours] = await env.DB.batch([
    env.DB.prepare(
      `SELECT COUNT(*) pv, COUNT(DISTINCT uv) uv, MIN(ts) first, MAX(ts) last FROM hits WHERE ${W}`
    ).bind(from),
    env.DB.prepare(
      `SELECT day, COUNT(*) pv, COUNT(DISTINCT uv) uv FROM hits WHERE ${W} GROUP BY day ORDER BY day`
    ).bind(from),
    env.DB.prepare(
      `SELECT path, COUNT(*) n, COUNT(DISTINCT uv) u FROM hits WHERE ${W} GROUP BY path ORDER BY n DESC LIMIT 20`
    ).bind(from),
    env.DB.prepare(
      `SELECT ref, COUNT(*) n FROM hits WHERE ${W} AND ref <> '' GROUP BY ref ORDER BY n DESC LIMIT 12`
    ).bind(from),
    env.DB.prepare(
      `SELECT country, COUNT(*) n FROM hits WHERE ${W} AND country <> '' GROUP BY country ORDER BY n DESC LIMIT 12`
    ).bind(from),
    env.DB.prepare(
      `SELECT device, COUNT(*) n FROM hits WHERE ${W} GROUP BY device ORDER BY n DESC`
    ).bind(from),
    env.DB.prepare(
      `SELECT lang, COUNT(*) n FROM hits WHERE ${W} GROUP BY lang ORDER BY n DESC`
    ).bind(from),
    env.DB.prepare(
      `SELECT CAST(strftime('%H', ts / 1000, 'unixepoch', '+8 hours') AS INTEGER) h, COUNT(*) n
         FROM hits WHERE ${W} GROUP BY h ORDER BY h`
    ).bind(from),
  ]);

  const all = await env.DB.prepare("SELECT COUNT(*) n, MIN(day) since, MAX(day) until FROM hits").first();

  return json({
    range: { from, to: today, days },
    totals: tot.results[0] || { pv: 0, uv: 0 },
    daily: daily.results,
    pages: pages.results,
    refs: refs.results,
    countries: countries.results,
    devices: devices.results,
    langs: langs.results,
    hours: hours.results,
    lifetime: all,
  }, 200, cors, 30);
}

/* ---------------------------------------------------------------- 工具 */

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
