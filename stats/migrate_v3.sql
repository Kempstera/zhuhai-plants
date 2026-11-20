-- v3：明细里要能看到访客的 IP 与完整 UA
-- 说明：只在这张表里存，接口必须带口令才能读；站点前端不读、不展示、不转发给任何第三方。
ALTER TABLE hits ADD COLUMN ip TEXT NOT NULL DEFAULT '';
ALTER TABLE hits ADD COLUMN ua TEXT NOT NULL DEFAULT '';

CREATE INDEX IF NOT EXISTS idx_hits_ip ON hits (ip);
