/* 珠海草木志 · 访客数据
 * 数据来自 stats.signupeverywhere.cc；口令只存在本机 localStorage
 */
(function () {
  "use strict";

  var API = "__API__";
  var KEY = "zhplants.stats.key";
  var state = { days: 7, limit: 25, offset: 0, total: 0, data: null, busy: false };

  var $ = function (id) { return document.getElementById(id); };
  var gate = $("gate"), dash = $("dash"), gateErr = $("gate-err"), gateInput = $("gate-input");

  /* 支持 /visits#k=口令 这样的书签链接 */
  (function () {
    var m = location.hash.match(/^#k=(.+)$/);
    if (!m) return;
    try { localStorage.setItem(KEY, decodeURIComponent(m[1])); } catch (e) {}
    history.replaceState(null, "", location.pathname);
  })();

  function token() {
    try { return localStorage.getItem(KEY) || ""; } catch (e) { return ""; }
  }

  function showGate(msg) {
    dash.hidden = true;
    gate.hidden = false;
    gateErr.textContent = msg || "";
    gateInput.focus();
  }

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  var regionNames = null;
  try {
    regionNames = new Intl.DisplayNames(["zh-CN"], { type: "region" });
  } catch (e) {}

  function countryName(code) {
    if (!code) return "—";
    try { return regionNames ? regionNames.of(code) || code : code; } catch (e) { return code; }
  }

  function nf(n) {
    return (n || 0).toLocaleString("zh-CN");
  }

  function durText(sec) {
    if (sec == null || sec < 0) return "—";
    if (sec < 60) return sec + " 秒";
    var m = Math.floor(sec / 60), s = sec % 60;
    if (m < 60) return s ? m + " 分 " + s + " 秒" : m + " 分";
    return Math.floor(m / 60) + " 时 " + (m % 60) + " 分";
  }

  /* ------------------------------------------------------------ 取数 */

  function load() {
    var k = token();
    if (!k) return showGate("");
    if (state.busy) return;
    state.busy = true;
    var url = API + "/stats?days=" + state.days +
      "&limit=" + state.limit + "&offset=" + state.offset +
      "&token=" + encodeURIComponent(k);
    fetch(url, { cache: "no-store" })
      .then(function (r) {
        if (r.status === 403) throw new Error("forbidden");
        if (!r.ok) throw new Error("http " + r.status);
        return r.json();
      })
      .then(function (d) {
        state.busy = false;
        state.data = d;
        state.total = d.detailTotal || 0;
        gate.hidden = true;
        dash.hidden = false;
        render(d);
      })
      .catch(function (e) {
        state.busy = false;
        if (e.message === "forbidden") showGate("口令不对。");
        else showGate("连不上统计服务，稍后再试。");
      });
  }

  /* ------------------------------------------------------------ 渲染 */

  function render(d) {
    kpis(d.totals || {});
    trend(d.daily || []);
    hours(d.hours || []);
    bars("devices", (d.devices || []).map(function (x) { return [devName(x.b), x.n]; }));
    bars("browsers", (d.browsers || []).map(function (x) { return [x.b || "未知", x.n]; }));
    bars("oses", (d.oses || []).map(function (x) { return [x.b || "未知", x.n]; }));
    bars("langs", (d.langs || []).map(function (x) { return [x.b === "zh" ? "中文" : "English", x.n]; }));
    bars("pages", (d.pages || []).slice(0, 10).map(function (x) { return [x.path, x.n, x.u]; }), true);
    bars("refs", (d.refs || []).map(function (x) { return [x.ref, x.n]; }));
    bars("countries", (d.countries || []).map(function (x) { return [countryName(x.country), x.n]; }));
    bars("cities", (d.cities || []).map(function (x) {
      return [x.city + (x.country ? " · " + countryName(x.country) : ""), x.n];
    }));
    bars("asns", (d.asns || []).map(function (x) { return [x.asorg + (x.asn ? " · AS" + x.asn : ""), x.n]; }));
    bars("durs", durBuckets(d.durations || []));
    bars("scrolls", scrollBuckets(d.scrolls || []));
    detail(d.detail || []);
    $("dcount").textContent = state.total ? "共 " + nf(state.total) + " 条" : "";
    pager();
    var life = d.lifetime || {};
    $("lifetime").textContent = life.n
      ? "自 " + life.since + " 起累计 " + nf(life.n) + " 次浏览、"
        + nf(life.uv) + " 位访客"
      : "还没有任何记录";
  }

  var rzTimer = null;
  window.addEventListener("resize", function () {
    if (!state.data) return;
    clearTimeout(rzTimer);
    rzTimer = setTimeout(function () { trend(state.data.daily || []); }, 160);
  });

  function devName(b) {
    return { desktop: "桌面", mobile: "手机", tablet: "平板" }[b] || b || "未知";
  }

  var DUR_ORDER = [
    ["0-10", "10 秒以内"], ["10-30", "10–30 秒"], ["30-60", "30–60 秒"],
    ["1-3", "1–3 分钟"], ["3-10", "3–10 分钟"], ["10+", "10 分钟以上"],
    ["na", "未上报"]
  ];

  function durBuckets(rows) {
    var m = {};
    rows.forEach(function (r) { m[r.b] = r.n; });
    return DUR_ORDER.filter(function (k) { return m[k[0]]; })
      .map(function (k) { return [k[1], m[k[0]]]; });
  }

  var SCROLL_ORDER = [
    ["0-25", "不到四分之一"], ["25-50", "约四分之一到一半"],
    ["50-75", "一半到四分之三"], ["75-100", "几乎读到底"], ["na", "未上报"]
  ];

  function scrollBuckets(rows) {
    var m = {};
    rows.forEach(function (r) { m[r.b] = r.n; });
    return SCROLL_ORDER.filter(function (k) { return m[k[0]]; })
      .map(function (k) { return [k[1], m[k[0]]]; });
  }

  function kpis(t) {
    var avg = t.avgdur == null ? null : Math.round(t.avgdur);
    $("kpis").innerHTML = [
      cell("浏览量", nf(t.pv)),
      cell("访客", nf(t.uv)),
      cell("会话", nf(t.sess)),
      cell("平均停留", avg == null ? "—" : durText(avg)),
      cell("上报停留", t.withdur ? nf(t.withdur) : "0"),
    ].join("");
  }

  function cell(k, v) {
    return '<div class="kpi"><dt>' + k + '</dt><dd>' + v + "</dd></div>";
  }

  /* 把缺的日期补成 0，否则「7 天」里只有 3 天有数据时柱子会被拉得很宽 */
  function fillDays(rows) {
    var map = {};
    rows.forEach(function (r) { map[r.day] = r; });

    function parse(d) { var p = d.split("-"); return Date.UTC(+p[0], +p[1] - 1, +p[2]); }
    function fmt(t) {
      var d = new Date(t);
      return d.getUTCFullYear() + "-" +
        ("0" + (d.getUTCMonth() + 1)).slice(-2) + "-" +
        ("0" + d.getUTCDate()).slice(-2);
    }

    var start, end;
    if (state.days > 0) {
      end = Date.now();
      // 服务器按北京时间切日，这里也用 +08:00 的今天
      end = new Date(new Date(end + 8 * 3600e3).toISOString().slice(0, 10)).getTime();
      start = end - (state.days - 1) * 86400e3;
    } else if (rows.length) {
      start = parse(rows[0].day);
      end = parse(rows[rows.length - 1].day);
    } else {
      return [];
    }

    // 全部区间太长时截到最近 180 天，免得柱子细成线
    if (end - start > 179 * 86400e3) start = end - 179 * 86400e3;

    var out = [];
    for (var t = start; t <= end; t += 86400e3) {
      var k = fmt(t), r = map[k];
      out.push({ day: k, pv: r ? r.pv : 0, uv: r ? r.uv : 0 });
    }
    return out;
  }

  /* 柱＝浏览量，线＝访客 */
  function trend(raw) {
    var el = $("trend");
    var rows = fillDays(raw);
    if (!rows.length) { el.innerHTML = '<p class="vs__empty">这段时间还没有访问。</p>'; return; }

    var H = 210, P = 26, baseY = H - 30, top = 20;
    // 用容器实际宽度画，避免 viewBox 缩放把字和圆点一起拉伸
    var W = Math.max(300, el.clientWidth || 900);
    var maxPv = Math.max.apply(null, rows.map(function (r) { return r.pv; })) || 1;
    var slot = (W - P * 2) / rows.length;
    var bw = Math.max(2, Math.min(22, slot * 0.54));

    var bars = "", line = [], dots = "", labels = "";
    rows.forEach(function (r, i) {
      var x = P + slot * (i + 0.5);
      var h = r.pv ? Math.max(2, (r.pv / maxPv) * (baseY - top)) : 0;
      if (h) {
        bars += '<rect x="' + (x - bw / 2).toFixed(1) + '" y="' + (baseY - h).toFixed(1) +
          '" width="' + bw.toFixed(1) + '" height="' + h.toFixed(1) + '" rx="1.5" fill="#D9CFB8"/>';
      }
      var yv = baseY - (r.uv / maxPv) * (baseY - top);
      line.push(x.toFixed(1) + "," + yv.toFixed(1));
      dots += '<circle cx="' + x.toFixed(1) + '" cy="' + yv.toFixed(1) + '" r="2.6" fill="#3D5C4D"/>';
    });

    var every = Math.max(1, Math.ceil(rows.length / 9));
    rows.forEach(function (r, i) {
      if (i % every && i !== rows.length - 1) return;
      var x = P + slot * (i + 0.5);
      labels += '<text x="' + x.toFixed(1) + '" y="' + (H - 9) + '" text-anchor="middle" ' +
        'font-size="10" fill="#8B968E">' + r.day.slice(5) + "</text>";
    });

    el.innerHTML = '<svg width="' + W + '" height="' + H + '" class="chart" role="img">' +
      '<line x1="' + P + '" y1="' + baseY + '" x2="' + (W - P) + '" y2="' + baseY + '" stroke="#DCD3C1"/>' +
      bars +
      '<polyline points="' + line.join(" ") + '" fill="none" stroke="#3D5C4D" stroke-width="1.6"/>' +
      dots + labels + "</svg>";
  }

  function hours(rows) {
    var el = $("hours");
    var map = {};
    rows.forEach(function (r) { map[r.h] = r.n; });
    var max = 1;
    for (var i = 0; i < 24; i++) max = Math.max(max, map[i] || 0);
    var out = "";
    for (var h = 0; h < 24; h++) {
      var v = map[h] || 0;
      var pct = Math.round((v / max) * 100);
      out += '<div class="hours__col" title="' + h + ' 时 · ' + v + ' 次">' +
        '<div class="hours__bar" style="height:' + Math.max(v ? 4 : 1, pct) + '%"></div></div>';
    }
    el.innerHTML = '<div class="hours">' + out + "</div>" +
      '<div class="hours__axis">' + [0, 6, 12, 18, 23].map(function (h) {
        return "<span>" + h + " 时</span>";
      }).join("") + "</div>";
  }

  function bars(id, rows, showUv) {
    var el = $(id);
    if (!rows || !rows.length) { el.innerHTML = '<p class="vs__empty">暂无数据</p>'; return; }
    var max = Math.max.apply(null, rows.map(function (r) { return r[1]; })) || 1;
    var total = rows.reduce(function (a, r) { return a + r[1]; }, 0) || 1;
    el.innerHTML = '<ol class="rank">' + rows.map(function (r) {
      var w = Math.max(2, Math.round((r[1] / max) * 100));
      var pctv = Math.round((r[1] / total) * 100);
      return '<li class="rank__row"><span class="rank__k" title="' + esc(r[0]) + '">' + esc(r[0]) + "</span>" +
        '<span class="rank__bar"><i style="width:' + w + '%"></i></span>' +
        '<span class="rank__v">' + nf(r[1]) + (showUv && r[2] != null ? ' <em>/ ' + nf(r[2]) + "</em>" : "") +
        ' <b>' + pctv + "%</b></span></li>";
    }).join("") + "</ol>";
  }

  function detail(rows) {
    var tb = $("detail").querySelector("tbody");
    if (!rows.length) {
      tb.innerHTML = '<tr><td colspan="6" class="vs__empty">没有记录</td></tr>';
      return;
    }
    tb.innerHTML = rows.map(function (r) {
      var t = new Date(r.ts + 8 * 3600 * 1000).toISOString().slice(5, 16).replace("T", " ");
      var where = [countryName(r.country)];
      if (r.city) where.unshift(r.city);
      if (r.asorg) where.push(r.asorg);
      return "<tr>" +
        "<td class='mono' data-l='时间'>" + t + "</td>" +
        "<td class='mono vs__path' data-l='页面'>" + esc(r.path) + "</td>" +
        "<td data-l='来源'>" + (r.ref ? esc(r.ref) : '<span class="dim">直接访问</span>') + "</td>" +
        "<td data-l='位置'>" + esc(where.filter(Boolean).join(" · ")) + "</td>" +
        "<td data-l='设备'>" + esc([devName(r.device), r.browser, r.os].filter(function (x) { return x && x !== "未知"; }).join(" · ")) + "</td>" +
        "<td class='mono' data-l='停留'>" + (r.dur < 0 ? '<span class="dim">—</span>' : durText(r.dur)) +
        (r.scroll >= 0 ? " <span class='dim'>/" + r.scroll + "%</span>" : "") + "</td>" +
        "</tr>";
    }).join("");
  }

  function pager() {
    var page = Math.floor(state.offset / state.limit) + 1;
    var pages = Math.max(1, Math.ceil(state.total / state.limit));
    $("pager").innerHTML =
      '<button type="button" id="prev"' + (state.offset <= 0 ? " disabled" : "") + ">上一页</button>" +
      '<span class="vs__pageno">' + page + " / " + pages + "</span>" +
      '<button type="button" id="next"' + (state.offset + state.limit >= state.total ? " disabled" : "") + ">下一页</button>" +
      '<select id="psize">' + [25, 50, 100, 300].map(function (n) {
        return '<option value="' + n + '"' + (n === state.limit ? " selected" : "") + ">每页 " + n + "</option>";
      }).join("") + "</select>";
    $("prev").onclick = function () { state.offset = Math.max(0, state.offset - state.limit); load(); };
    $("next").onclick = function () { state.offset += state.limit; load(); };
    $("psize").onchange = function () {
      state.limit = parseInt(this.value, 10);
      state.offset = 0;
      load();
    };
  }

  /* ------------------------------------------------------------ 交互 */

  gate.hidden = false;

  $("gate-form").addEventListener("submit", function (e) {
    e.preventDefault();
    var v = gateInput.value.trim();
    if (!v) return;
    try { localStorage.setItem(KEY, v); } catch (err) {}
    gateErr.textContent = "";
    state.offset = 0;
    load();
  });

  document.querySelectorAll("[data-days]").forEach(function (b) {
    b.addEventListener("click", function () {
      document.querySelectorAll("[data-days]").forEach(function (x) { x.classList.remove("is-on"); });
      b.classList.add("is-on");
      state.days = parseInt(b.dataset.days, 10);
      state.offset = 0;
      load();
    });
  });

  $("refresh").addEventListener("click", load);

  $("export").addEventListener("click", function () {
    var k = token();
    if (!k) return;
    location.href = API + "/export.csv?days=" + state.days + "&token=" + encodeURIComponent(k);
  });

  $("signout").addEventListener("click", function () {
    try { localStorage.removeItem(KEY); } catch (e) {}
    state.data = null;
    showGate("");
  });

  if (token()) load(); else showGate("");
})();
