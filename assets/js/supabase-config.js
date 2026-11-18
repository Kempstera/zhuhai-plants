/* 珠海草木志 · 留言板配置
 *
 * 填了这两行，构建时才会生成 /guestbook 页面，并在导航与页脚挂上「留言」入口。
 * 留空时整站照旧，不会出现一个打不开的链接。
 *
 *   url     —— Supabase 项目地址，形如 https://abcdefghijk.supabase.co
 *              （Project Settings → Data API → Project URL）
 *   anonKey —— Project Settings → API Keys → anon public
 *
 * 这里放的是 anon key，本来就是给浏览器用的公开钥匙，
 * 真正的权限由 supabase/schema.sql 里的 RLS 策略把关。
 * 千万不要把 service_role key 写进这个文件。
 */
window.SUPABASE_CONFIG = {
  url: "",
  anonKey: ""
};
