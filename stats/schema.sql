-- 访问记录：一条一次页面浏览，不含 Cookie 与原始 IP
CREATE TABLE IF NOT EXISTS hits (
  id      INTEGER PRIMARY KEY AUTOINCREMENT,
  ts      INTEGER NOT NULL,              -- 毫秒时间戳
  day     TEXT    NOT NULL,              -- 北京时间日期 YYYY-MM-DD
  path    TEXT    NOT NULL,              -- 规范化路径，无查询串
  ref     TEXT    NOT NULL DEFAULT '',   -- 来源域名，站内为空
  country TEXT    NOT NULL DEFAULT '',   -- Cloudflare 国家码
  device  TEXT    NOT NULL DEFAULT '',   -- desktop / mobile / tablet
  lang    TEXT    NOT NULL DEFAULT 'zh', -- zh / en
  uv      TEXT    NOT NULL               -- 逐日去重用的哈希，16 位
);

CREATE INDEX IF NOT EXISTS idx_hits_day ON hits (day);
CREATE INDEX IF NOT EXISTS idx_hits_ts  ON hits (ts);
CREATE INDEX IF NOT EXISTS idx_hits_uv  ON hits (day, uv);
