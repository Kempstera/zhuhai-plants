-- ============================================================================
-- 珠海草木志 · 留言板
-- 在 Supabase 控制台 → SQL Editor 里整段粘贴执行即可（可重复执行）。
--
-- 权限模型：
--   读：任何人（包括未登录）
--   写：只有登录用户，且 user_id 必须等于自己的 auth.uid()
--   删：只能删自己那条
-- 另外用触发器限制同一账号 30 秒内只能发一条，挡住手滑与刷屏。
-- ============================================================================

create table if not exists public.guestbook (
  id         bigint generated always as identity primary key,
  user_id    uuid not null references auth.users (id) on delete cascade,
  nickname   text not null check (char_length(btrim(nickname)) between 1 and 20),
  body       text not null check (char_length(btrim(body)) between 1 and 600),
  created_at timestamptz not null default now()
);

create index if not exists guestbook_created_idx on public.guestbook (created_at desc);
create index if not exists guestbook_user_idx on public.guestbook (user_id);

alter table public.guestbook enable row level security;

drop policy if exists "guestbook readable by all" on public.guestbook;
create policy "guestbook readable by all"
  on public.guestbook for select
  using (true);

drop policy if exists "guestbook insert own" on public.guestbook;
create policy "guestbook insert own"
  on public.guestbook for insert
  to authenticated
  with check (auth.uid() = user_id);

drop policy if exists "guestbook delete own" on public.guestbook;
create policy "guestbook delete own"
  on public.guestbook for delete
  to authenticated
  using (auth.uid() = user_id);

-- 同一账号 30 秒内只允许一条
create or replace function public.guestbook_rate_limit()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  if exists (
    select 1 from public.guestbook
    where user_id = new.user_id
      and created_at > now() - interval '30 seconds'
  ) then
    raise exception 'rate_limited' using errcode = 'P0001';
  end if;
  return new;
end;
$$;

drop trigger if exists trg_guestbook_rate on public.guestbook;
create trigger trg_guestbook_rate
  before insert on public.guestbook
  for each row execute function public.guestbook_rate_limit();

-- 角色授权：Supabase 默认会授，这里写明，换项目重建时也不会漏
grant select on public.guestbook to anon, authenticated;
grant insert, delete on public.guestbook to authenticated;
grant usage, select on sequence public.guestbook_id_seq to authenticated;

-- 收尾自检：应该看到 3 条 policy、1 个 trigger
-- select polname from pg_policy where polrelid = 'public.guestbook'::regclass;

