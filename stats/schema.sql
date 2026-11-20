-- ============================================================================
-- zhplants-stats · D1 表结构（v2）
--
-- 新建项目时整段执行即可；已有库用文末的 migrate 段增量补列。
-- 原则：不存 IP、不存完整 UA；城市与接入商来自 Cloudflare 边缘，同样不含 IP。
-- ============================================================================

CREATE TABLE IF NOT EXISTS hits (
  id      INTEGER PRIMARY KEY AUTOINCREMENT,
  ts      INTEGER NOT NULL,               -- 毫秒时间戳
  day     TEXT    NOT NULL,               -- 北京时间日期 YYYY-MM-DD
  uv      TEXT    NOT NULL,               -- 逐日去重用的哈希，16 位
  sid     TEXT    NOT NULL DEFAULT '',    -- 前端生成的访问标识，用于回填停留数据
  path    TEXT    NOT NULL,               -- 规范化路径，无查询串
  ref     TEXT    NOT NULL DEFAULT '',    -- 来源域名，站内为空
  country TEXT    NOT NULL DEFAULT '',    -- Cloudflare 国家码
  region  TEXT    NOT NULL DEFAULT '',    -- 省 / 州
  city    TEXT    NOT NULL DEFAULT '',    -- 城市
  asn     INTEGER NOT NULL DEFAULT 0,     -- 接入商编号
  asorg   TEXT    NOT NULL DEFAULT '',    -- 接入商名称
  device  TEXT    NOT NULL DEFAULT '',    -- desktop / mobile / tablet
  browser TEXT    NOT NULL DEFAULT '',    -- Chrome / Safari / ...
  os      TEXT    NOT NULL DEFAULT '',    -- macOS / iOS / ...
  lang    TEXT    NOT NULL DEFAULT 'en',  -- zh / en
  dur     INTEGER NOT NULL DEFAULT -1,    -- 停留秒数，-1 表示未上报
  scroll  INTEGER NOT NULL DEFAULT -1     -- 最大滚动百分比，-1 表示未上报
);

CREATE INDEX IF NOT EXISTS idx_hits_day  ON hits (day);
CREATE INDEX IF NOT EXISTS idx_hits_ts   ON hits (ts);
CREATE INDEX IF NOT EXISTS idx_hits_uv   ON hits (day, uv);
CREATE INDEX IF NOT EXISTS idx_hits_sid  ON hits (sid);
CREATE INDEX IF NOT EXISTS idx_hits_city ON hits (day, city);

-- ----------------------------------------------------------------------------
-- 已有 v1 库（缺少 sid / region / city / asn / asorg / browser / os / dur / scroll）
-- 时，跑这一段补列：
--
--   ALTER TABLE hits ADD COLUMN sid     TEXT    NOT NULL DEFAULT '';
--   ALTER TABLE hits ADD COLUMN region  TEXT    NOT NULL DEFAULT '';
--   ALTER TABLE hits ADD COLUMN city    TEXT    NOT NULL DEFAULT '';
--   ALTER TABLE hits ADD COLUMN asn     INTEGER NOT NULL DEFAULT 0;
--   ALTER TABLE hits ADD COLUMN asorg   TEXT    NOT NULL DEFAULT '';
--   ALTER TABLE hits ADD COLUMN browser TEXT    NOT NULL DEFAULT '';
--   ALTER TABLE hits ADD COLUMN os      TEXT    NOT NULL DEFAULT '';
--   ALTER TABLE hits ADD COLUMN dur     INTEGER NOT NULL DEFAULT -1;
--   ALTER TABLE hits ADD COLUMN scroll  INTEGER NOT NULL DEFAULT -1;
--   CREATE INDEX IF NOT EXISTS idx_hits_sid  ON hits (sid);
--   CREATE INDEX IF NOT EXISTS idx_hits_city ON hits (day, city);
--
-- 老行的 dur/scroll 是 -1，表示「未上报」，统计时排除在平均值之外。
-- ----------------------------------------------------------------------------
