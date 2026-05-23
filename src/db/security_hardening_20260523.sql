-- Security hardening for community content and media.
-- Run in the Supabase SQL editor after the base schema exists.

begin;

alter table public.posts enable row level security;
alter table public.comments enable row level security;
alter table public.profiles enable row level security;

alter table public.profiles
  add column if not exists role text default 'user';

update public.profiles
set role = 'user'
where role is null;

alter table public.profiles
  alter column role set default 'user';

alter table public.comments
  add column if not exists is_deleted boolean not null default false,
  add column if not exists deleted_at timestamp with time zone,
  add column if not exists deleted_by uuid references public.profiles(id);

drop policy if exists "Public profiles are viewable by everyone" on public.profiles;
drop policy if exists "Public profiles are viewable by everyone." on public.profiles;
create policy "Public profiles are viewable by everyone"
on public.profiles for select
using (true);

drop policy if exists "Users can insert their own profile" on public.profiles;
drop policy if exists "Users can insert their own profile." on public.profiles;
create policy "Users can insert their own profile"
on public.profiles for insert
with check (
  auth.uid() = id
  and coalesce(role, 'user') = 'user'
);

drop policy if exists "Users can update own profile" on public.profiles;
drop policy if exists "Users can update own profile." on public.profiles;
create policy "Users can update own profile"
on public.profiles for update
using (auth.uid() = id)
with check (auth.uid() = id);

create or replace function public.prevent_profile_role_self_update()
returns trigger
language plpgsql
security definer
set search_path = public, auth
as $$
begin
  if auth.uid() = new.id and new.role is distinct from old.role then
    raise exception 'profile role cannot be changed by the profile owner';
  end if;

  return new;
end;
$$;

drop trigger if exists prevent_profile_role_self_update on public.profiles;
create trigger prevent_profile_role_self_update
before update of role on public.profiles
for each row execute function public.prevent_profile_role_self_update();

revoke execute on function public.prevent_profile_role_self_update() from anon, authenticated;

drop policy if exists "Posts are viewable by everyone" on public.posts;
drop policy if exists "Posts are viewable by everyone." on public.posts;
create policy "Posts are viewable by everyone"
on public.posts for select
using (true);

drop policy if exists "Users can insert their own posts" on public.posts;
drop policy if exists "Users can insert their own posts." on public.posts;

drop policy if exists "Users can update their own posts" on public.posts;

drop policy if exists "Users and staff can delete posts" on public.posts;

-- Browser clients should not write posts directly to Supabase. The Django
-- community API sanitizes rich text, validates media URLs and checks
-- ownership/staff permissions before writing with the service role.

drop policy if exists "Comments are viewable by everyone" on public.comments;
drop policy if exists "Comments are viewable by everyone." on public.comments;
create policy "Comments are viewable by everyone"
on public.comments for select
using (coalesce(is_deleted, false) = false);

drop policy if exists "Comment owners and staff can soft delete comments" on public.comments;
drop policy if exists "Authenticated users can insert comments" on public.comments;
drop policy if exists "Authenticated users can insert comments." on public.comments;

drop policy if exists "Users can delete their own comments" on public.comments;
drop policy if exists "Users can delete their own comments." on public.comments;

-- Browser clients should not write or delete comments directly. The Django
-- community API sanitizes comment text and soft-deletes comments only after
-- checking owner/staff permissions.

insert into storage.buckets (id, name, public)
values ('media', 'media', true)
on conflict (id) do update
set public = excluded.public;

drop policy if exists "Public Access" on storage.objects;
create policy "Public Access"
on storage.objects for select
using (bucket_id = 'media');

drop policy if exists "Users can replace their own media" on storage.objects;
drop policy if exists "Authenticated users can upload" on storage.objects;

-- Browser clients should not upload directly to Supabase Storage. The Django
-- community media API validates file type, size and content, then stores files
-- with the trusted service role.

commit;
