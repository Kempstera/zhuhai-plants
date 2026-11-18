/* 珠海草木志 · 留言板
 * 依赖：assets/vendor/supabase.js（自托管，避免第三方 CDN 在境内不稳）
 * 数据：public.guestbook，RLS 见 supabase/schema.sql
 */
(function () {
  "use strict";

  var cfg = window.SUPABASE_CONFIG || {};
  var i18nEl = document.getElementById("gb-i18n");
  var I18N = i18nEl ? JSON.parse(i18nEl.textContent) : {};
  var PAGE = 20;

  function T(key) {
    var s = I18N[key] || key;
    for (var i = 1; i < arguments.length; i++) {
      s = s.replace("{" + (i - 1) + "}", arguments[i]);
    }
    return s;
  }

  var $ = function (id) { return document.getElementById(id); };
  var notice = $("gb-notice");
  var authCard = $("gb-auth");
  var meCard = $("gb-me");
  var listEl = $("gb-list");
  var emptyEl = $("gb-empty");
  var moreBtn = $("gb-more");
  var statusEl = $("gb-status");
  var errIn = $("gb-err-in");
  var errUp = $("gb-err-up");
  var postErr = $("gb-post-err");
  var bodyEl = $("gb-body");
  var nickEl = $("gb-nick");
  var charsEl = $("gb-chars");
  var postBtn = $("gb-post");

  if (!cfg.url || !cfg.anonKey) {
    if (notice) notice.hidden = false;
    return;
  }
  if (!window.supabase || !window.supabase.createClient) {
    if (notice) {
      notice.hidden = false;
      var p = notice.querySelector("p");
      if (p) p.textContent = T("gb_offline_script");
    }
    return;
  }

  var client = window.supabase.createClient(cfg.url, cfg.anonKey, {
    auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true }
  });

  var session = null;
  var offset = 0;
  var loading = false;

  /* ------------------------------------------------------------ 会话 */

  function nameOf(s) {
    if (!s || !s.user) return "";
    var m = s.user.user_metadata || {};
    return (m.nickname || "").trim() || (s.user.email || "").split("@")[0];
  }

  function render(s) {
    session = s || null;
    var on = !!session;
    authCard.hidden = on;
    meCard.hidden = !on;
    if (on) {
      $("gb-who").textContent = T("gb_signed", nameOf(session));
      if (!nickEl.value) nickEl.value = nameOf(session).slice(0, 20);
    }
  }

  function fmtTime(iso) {
    var d = new Date(iso);
    var diff = (Date.now() - d.getTime()) / 1000;
    if (diff < 60) return T("gb_just_now");
    if (diff < 3600) return T("gb_mins", Math.floor(diff / 60));
    if (diff < 86400) return T("gb_hours", Math.floor(diff / 3600));
    if (diff < 86400 * 7) return T("gb_days", Math.floor(diff / 86400));
    var y = d.getFullYear(), m = d.getMonth() + 1, day = d.getDate();
    return y + "." + (m < 10 ? "0" + m : m) + "." + (day < 10 ? "0" + day : day);
  }

  function mapError(err) {
    if (!err) return T("gb_err_generic");
    var msg = (err.message || "").toLowerCase();
    var code = err.code || "";
    if (code === "P0001" || msg.indexOf("rate_limited") > -1) return T("gb_err_rate");
    if (code === "23514" || msg.indexOf("check constraint") > -1) return T("gb_err_len");
    if (msg.indexOf("invalid login") > -1 || msg.indexOf("invalid credentials") > -1) return T("gb_err_creds");
    if (msg.indexOf("already registered") > -1 || msg.indexOf("already been registered") > -1) return T("gb_err_exists");
    if (msg.indexOf("password") > -1 && msg.indexOf("6") > -1) return T("gb_err_pwd");
    if (msg.indexOf("email not confirmed") > -1) return T("gb_err_unconfirmed");
    if (msg.indexOf("failed to fetch") > -1 || msg.indexOf("network") > -1) return T("gb_err_network");
    return T("gb_err_generic");
  }

  /* ------------------------------------------------------------ 列表 */

  function makeItem(row) {
    var li = document.createElement("li");
    li.className = "gb__item";
    li.dataset.id = row.id;

    var meta = document.createElement("div");
    meta.className = "gb__meta";

    var who = document.createElement("span");
    who.className = "gb__who";
    who.textContent = row.nickname;

    var when = document.createElement("span");
    when.className = "gb__when";
    when.textContent = fmtTime(row.created_at);

    var right = document.createElement("span");
    right.className = "gb__meta-right";
    right.appendChild(when);

    if (session && session.user && row.user_id === session.user.id) {
      var del = document.createElement("button");
      del.type = "button";
      del.className = "gb__del";
      del.textContent = T("gb_delete");
      del.addEventListener("click", function () { remove(row.id, li); });
      right.appendChild(del);
    }

    meta.appendChild(who);
    meta.appendChild(right);

    var body = document.createElement("div");
    body.className = "gb__body";
    body.textContent = row.body;

    li.appendChild(meta);
    li.appendChild(body);
    return li;
  }

  async function load(reset) {
    if (loading) return;
    loading = true;
    if (reset) { offset = 0; listEl.textContent = ""; }
    statusEl.textContent = T("gb_loading");

    var res;
    try {
      res = await client
        .from("guestbook")
        .select("id,user_id,nickname,body,created_at")
        .order("created_at", { ascending: false })
        .range(offset, offset + PAGE - 1);
    } catch (e) {
      res = { error: e, data: null };
    } finally {
      loading = false;
    }

    statusEl.textContent = res.error ? T("gb_err_load") : "";

    var rows = res.data || [];
    rows.forEach(function (r) { listEl.appendChild(makeItem(r)); });
    offset += rows.length;

    emptyEl.hidden = listEl.children.length > 0 || !!res.error;
    moreBtn.hidden = rows.length < PAGE;
    moreBtn.textContent = T("gb_more");
  }

  async function remove(id, node) {
    if (!window.confirm(T("gb_confirm"))) return;
    var res = await client.from("guestbook").delete().eq("id", id);
    if (res.error) { statusEl.textContent = mapError(res.error); return; }
    node.parentNode.removeChild(node);
    emptyEl.hidden = listEl.children.length > 0;
  }

  /* ------------------------------------------------------------ 交互 */

  function switchTab(which) {
    var isIn = which === "in";
    $("gb-tab-in").classList.toggle("is-on", isIn);
    $("gb-tab-up").classList.toggle("is-on", !isIn);
    $("gb-form-in").hidden = !isIn;
    $("gb-form-up").hidden = isIn;
    errIn.textContent = "";
    errUp.textContent = "";
    errUp.classList.remove("is-ok");
  }

  $("gb-tab-in").addEventListener("click", function () { switchTab("in"); });
  $("gb-tab-up").addEventListener("click", function () { switchTab("up"); });

  $("gb-form-in").addEventListener("submit", async function (e) {
    e.preventDefault();
    errIn.textContent = "";
    var email = $("gb-in-email").value.trim();
    var pwd = $("gb-in-pwd").value;
    var btn = $("gb-in-btn");
    btn.disabled = true;
    var res = await client.auth.signInWithPassword({ email: email, password: pwd });
    btn.disabled = false;
    if (res.error) { errIn.textContent = mapError(res.error); return; }
    render(res.data.session);
    load(true);
  });

  $("gb-form-up").addEventListener("submit", async function (e) {
    e.preventDefault();
    errUp.textContent = "";
    errUp.classList.remove("is-ok");
    var email = $("gb-up-email").value.trim();
    var pwd = $("gb-up-pwd").value;
    var nick = $("gb-up-nick").value.trim();
    if (pwd.length < 6) { errUp.textContent = T("gb_err_pwd"); return; }
    if (!nick) { errUp.textContent = T("gb_err_len"); return; }
    var btn = $("gb-up-btn");
    btn.disabled = true;
    var res = await client.auth.signUp({
      email: email,
      password: pwd,
      options: {
        data: { nickname: nick.slice(0, 20) },
        emailRedirectTo: location.origin + location.pathname
      }
    });
    btn.disabled = false;
    if (res.error) { errUp.textContent = mapError(res.error); return; }
    if (res.data.session) { render(res.data.session); load(true); }
    else { errUp.textContent = T("gb_check_mail"); errUp.classList.add("is-ok"); }
  });

  $("gb-signout").addEventListener("click", async function () {
    await client.auth.signOut();
    render(null);
    load(true);
  });

  bodyEl.addEventListener("input", function () {
    charsEl.textContent = bodyEl.value.length + " / 600";
  });

  $("gb-form-post").addEventListener("submit", async function (e) {
    e.preventDefault();
    postErr.textContent = "";
    if (!session) { postErr.textContent = T("gb_err_auth"); return; }
    var body = bodyEl.value.trim();
    var nick = (nickEl.value.trim() || nameOf(session)).slice(0, 20);
    if (body.length < 1 || body.length > 600) { postErr.textContent = T("gb_err_len"); return; }

    postBtn.disabled = true;
    var res = await client.from("guestbook").insert({
      user_id: session.user.id,
      nickname: nick,
      body: body
    }).select("id,user_id,nickname,body,created_at").single();
    postBtn.disabled = false;

    if (res.error) { postErr.textContent = mapError(res.error); return; }
    listEl.insertBefore(makeItem(res.data), listEl.firstChild);
    emptyEl.hidden = true;
    bodyEl.value = "";
    charsEl.textContent = "0 / 600";
  });

  moreBtn.addEventListener("click", function () { load(false); });

  /* ------------------------------------------------------------ 启动 */

  switchTab("in");
  load(true);

  client.auth.getSession().then(function (r) {
    render(r.data && r.data.session);
    load(true);
  }).catch(function () { render(null); });

  client.auth.onAuthStateChange(function (_evt, s) { render(s); });
})();
