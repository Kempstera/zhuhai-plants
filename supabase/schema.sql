-- ============================================================================
-- 珠海草木志 · 留言板
-- 在 Supabase 控制台 → SQL Editor 里整段粘贴执行（可重复执行）。
--
-- 表名用 plants_guestbook：这个项目里已经有一张 public.guestbook（电台站的），
-- 用 guestbook 会撞名 —— create table if not exists 会静默跳过，策略却会加到
-- 别人那张表上。
--
-- 权限模型：
--   读：任何人（包括未登录）
--   写：只有登录用户，且 user_id 必须等于自己的 auth.uid()
--   删：只能删自己那条
-- 触发器限制同一账号 30 秒内只能发一条，挡住手滑与刷屏。
-- ============================================================================

-- 0) 清理：早前误加到 public.guestbook（电台站）上的对象
drop trigger if exists trg_guestbook_rate on public.guestbook;
drop function if exists public.guestbook_rate_limit();
drop policy if exists "guestbook readable by all" on public.guestbook;
drop policy if exists "guestbook insert own" on public.guestbook;
drop policy if exists "guestbook delete own" on public.guestbook;
drop index if exists public.guestbook_created_idx;
drop index if exists public.guestbook_user_idx;

-- 1) 表
create table if not exists public.plants_guestbook (
  id         bigint generated always as identity primary key,
  user_id    uuid not null references auth.users (id) on delete cascade,
  nickname   text not null check (char_length(btrim(nickname)) between 1 and 20),
  body       text not null check (char_length(btrim(body)) between 1 and 600),
  created_at timestamptz not null default now()
);

create index if not exists plants_guestbook_created_idx on public.plants_guestbook (created_at desc);
create index if not exists plants_guestbook_user_idx on public.plants_guestbook (user_id);

-- 2) 权限
alter table public.plants_guestbook enable row level security;

drop policy if exists "plants guestbook readable by all" on public.plants_guestbook;
create policy "plants guestbook readable by all"
  on public.plants_guestbook for select
  using (true);

drop policy if exists "plants guestbook insert own" on public.plants_guestbook;
create policy "plants guestbook insert own"
  on public.plants_guestbook for insert
  to authenticated
  with check (auth.uid() = user_id);

drop policy if exists "plants guestbook delete own" on public.plants_guestbook;
create policy "plants guestbook delete own"
  on public.plants_guestbook for delete
  to authenticated
  using (auth.uid() = user_id);

-- 3) 同一账号 30 秒内只允许一条
create or replace function public.plants_guestbook_rate_limit()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  if exists (
    select 1 from public.plants_guestbook
    where user_id = new.user_id
      and created_at > now() - interval '30 seconds'
  ) then
    raise exception 'rate_limited' using errcode = 'P0001';
  end if;
  return new;
end;
$$;

drop trigger if exists trg_plants_guestbook_rate on public.plants_guestbook;
create trigger trg_plants_guestbook_rate
  before insert on public.plants_guestbook
  for each row execute function public.plants_guestbook_rate_limit();

-- 4) 角色授权
grant select on public.plants_guestbook to anon, authenticated;
grant insert, delete on public.plants_guestbook to authenticated;
grant usage, select on sequence public.plants_guestbook_id_seq to authenticated;

-- 5) 自检：应返回
--    table_exists=t, policies=3, triggers=1, rls=t, on_old=t(电台站原策略仍在)
select
  to_regclass('public.plants_guestbook') is not null as table_exists,
  (select count(*) from pg_policy where polrelid = 'public.plants_guestbook'::regclass) as policies,
  (select count(*) from pg_trigger where tgrelid = 'public.plants_guestbook'::regclass and not tgisinternal) as triggers,
  (select relrowsecurity from pg_class where oid = 'public.plants_guestbook'::regclass) as rls;
