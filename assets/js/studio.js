/* 站长页：统计面板。口令只存在本机 localStorage，每次请求带在查询串上。 */

const API = "__API__";
const $ = (s) => document.querySelector(s);
const gate = $("#gate"), dash = $("#dash"), err = $("#gate-err");
let days = 30;
const KEY = "zhplants.stats.key";

function token() { try { return localStorage.getItem(KEY) || ""; } catch { return ""; } }

/* 支持 /studio#k=口令 这样的书签链接；口令留在浏览器本地，不上服务器 */
(function () {
  const m = location.hash.match(/^#k=(.+)$/);
  if (!m) return;
  try { localStorage.setItem(KEY, decodeURIComponent(m[1])); } catch {}
  history.replaceState(null, "", location.pathname);
})();

/* 支持 /studio#k=口令 这样的书签链接；口令留在浏览器本地，不上服务器 */
(function () {
  const m = location.hash.match(/^#k=(.+)$/);
  if (!m) return;
  try { localStorage.setItem(KEY, decodeURIComponent(m[1])); } catch {}
  history.replaceState(null, "", location.pathname);
})();
function showGate(msg) {
  dash.hidden = true; gate.hidden = false;
  if (msg) err.textContent = msg;
  const t = $("#tok"); if (t) { t.focus(); t.select(); }
}

$("#gate-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const v = $("#tok").value.trim();
  if (!v) return;
  try { localStorage.setItem(KEY, v); } catch {}
  err.textContent = "";
  load();
});

$("#signout").addEventListener("click", () => {
  try { localStorage.removeItem(KEY); } catch {}
  showGate("");
});

$("#reload").addEventListener("click", () => load());

document.querySelectorAll(".stu__seg button").forEach((b) => {
  b.addEventListener("click", () => {
    document.querySelectorAll(".stu__seg button").forEach((x) => x.classList.remove("is-on"));
    b.classList.add("is-on");
    days = parseInt(b.dataset.d, 10);
    load();
  });
});

async function load() {
  const k = token();
  if (!k) return showGate("");
  let res, data;
  try {
    res = await fetch(`${API}/stats?days=${days}&token=${encodeURIComponent(k)}`, { cache: "no-store" });
    data = await res.json();
  } catch (e) {
    return showGate("连不上统计服务，稍后再试。");
  }
  if (res.status === 403) { showGate("口令不对。"); return; }
  if (!res.ok) { showGate("读取失败：" + (data && data.error || res.status)); return; }
  gate.hidden = true; dash.hidden = false;
  render(data);
}

const fmt = (n) => (n || 0).toLocaleString("zh-CN");

function render(d) {
  const map = Object.fromEntries(d.daily.map((r) => [r.day, r]));
  const today = map[d.range.to] || { pv: 0, uv: 0 };
  const pv = d.daily.reduce((s, r) => s + r.pv, 0);
  const uvMax = d.daily.reduce((s, r) => Math.max(s, r.uv), 0);

  $("#kpis").innerHTML = [
    ["今日浏览", fmt(today.pv), "PV"],
    ["今日访客", fmt(today.uv), "按日去重"],
    [`${d.range.days} 日浏览`, fmt(pv), "PV"],
    [`${d.range.days} 日访客`, fmt(uvMax), "单日峰值"],
    ["累计浏览", fmt(d.lifetime && d.lifetime.n), (d.lifetime && d.lifetime.since ? d.lifetime.since + " 起" : "")],
  ].map(([k, v, s]) => `<dl class="stu__kpi"><dt>${k}</dt><dd>${v}</dd><small>${s}</small></dl>`).join("");

  $("#chart").innerHTML = pv ? chart(d, map) : empty("还没有记录，等第一位访客。");
  $("#pages").innerHTML = rank(d.pages.map((r) => [r.path === "/" ? "首页 /" : r.path, r.n]));
  $("#refs").innerHTML = d.refs.length ? rank(d.refs.map((r) => [r.ref, r.n])) : empty("还没有站外来源");
  $("#countries").innerHTML = d.countries.length
    ? rank(d.countries.map((r) => [countryName(r.country) + " · " + r.country, r.n])) : empty("暂无");
  const dev = d.devices.map((r) => [({ desktop: "桌面", mobile: "手机", tablet: "平板" })[r.device] || r.device, r.n]);
  const lg = d.langs.map((r) => ["中文站 / 英文站".split(" / ")[r.lang === "en" ? 1 : 0], r.n]);
  $("#devices").innerHTML = rank(dev) + `<div style="height:14px"></div>` + rank(lg);
  $("#hours").innerHTML = hours(d.hours);

  const life = d.lifetime || {};
  $("#lifetime").textContent =
    `记录自 ${life.since || "—"} 起，共 ${fmt(life.n)} 次浏览。不设 Cookie，不存 IP 与完整 UA；访客去重只在当天有效。`;
}

function empty(t) { return `<p style="font-size:13px;color:var(--ink-faint);margin:0">${t}</p>`; }

function rank(rows) {
  if (!rows.length) return empty("暂无数据");
  const max = Math.max(...rows.map((r) => r[1])) || 1;
  return rows.map(([name, n]) => `
    <div class="rank__row">
      <span class="rank__name" title="${esc(name)}">${esc(name)}</span>
      <span class="rank__n">${fmt(n)}</span>
      <span class="rank__bar"><i style="width:${Math.max(2, (n / max) * 100)}%"></i></span>
    </div>`).join("");
}

function hours(rows) {
  const m = Object.fromEntries((rows || []).map((r) => [r.h, r.n]));
  const max = Math.max(1, ...Object.values(m));
  const bars = Array.from({ length: 24 }, (_, h) => {
    const n = m[h] || 0;
    return `<i style="height:${Math.max(2, (n / max) * 100)}%" title="${h}:00 · ${n}"></i>`;
  }).join("");
  const axis = Array.from({ length: 24 }, (_, h) => `<span>${h % 3 === 0 ? h : ""}</span>`).join("");
  return `<div class="hours">${bars}</div><div class="hours__axis">${axis}</div>`;
}

function chart(d, map) {
  const W = 720, H = 200, P = 26;
  const days = [];
  // 用北京时间正午做基准，避免 toISOString 的 UTC 偏移把日期挪前一天
  const start = new Date(d.range.from + "T12:00:00+08:00");
  for (let i = 0; i < d.range.days; i++) {
    const t = new Date(start.getTime() + i * 86400000);
    const key = t.toISOString().slice(0, 10);
    days.push([key, map[key] || { pv: 0, uv: 0 }]);
  }
  const max = Math.max(1, ...days.map(([, v]) => v.pv));
  const x = (i) => P + (i * (W - P * 2)) / Math.max(1, days.length - 1);
  const y = (v) => H - P - (v / max) * (H - P * 2);

  const line = days.map(([, v], i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v.pv).toFixed(1)}`).join(" ");
  const area = `${line} L${x(days.length - 1).toFixed(1)},${H - P} L${x(0).toFixed(1)},${H - P} Z`;
  const dots = days.map(([, v], i) =>
    (v.pv ? `<circle cx="${x(i).toFixed(1)}" cy="${y(v.pv).toFixed(1)}" r="2.4" fill="#3D5C4D"><title>${days[i][0]} · ${v.pv} PV / ${v.uv} UV</title></circle>` : "")
  ).join("");

  const ticks = [...new Set([0, Math.round(max / 2), max])];
  const grid = ticks.map((v) => {
    const yy = (H - P - (v / max) * (H - P * 2)).toFixed(1);
    return `<line x1="${P}" x2="${W - P}" y1="${yy}" y2="${yy}" stroke="#E9E2D3" stroke-width="1"/>
            <text x="${P - 8}" y="${(+yy + 4).toFixed(1)}" text-anchor="end" font-size="10" fill="#8B968E" font-family="system-ui">${v}</text>`;
  }).join("");

  const lab = (i) => `<text x="${x(i).toFixed(1)}" y="${H - 6}" text-anchor="middle" font-size="10" fill="#8B968E" font-family="system-ui">${days[i][0].slice(5).replace("-", "/")}</text>`;
  const labels = lab(0) + lab(Math.floor((days.length - 1) / 2)) + lab(days.length - 1);

  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="每日浏览量">
    ${grid}
    <path d="${area}" fill="#3D5C4D" fill-opacity="0.07"/>
    <path d="${line}" fill="none" stroke="#3D5C4D" stroke-width="1.6" stroke-linejoin="round"/>
    ${dots}${labels}
  </svg>`;
}

function countryName(c) {
  const m = { CN: "中国", HK: "中国香港", MO: "中国澳门", TW: "中国台湾", US: "美国", JP: "日本",
    SG: "新加坡", GB: "英国", DE: "德国", FR: "法国", CA: "加拿大", AU: "澳大利亚", MY: "马来西亚",
    KR: "韩国", NL: "荷兰", RU: "俄罗斯", IN: "印度", TH: "泰国", VN: "越南", PH: "菲律宾" };
  return m[c] || c;
}

function esc(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

showGate("");
load();
