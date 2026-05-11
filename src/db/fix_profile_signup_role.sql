-- Fix Supabase signup failures caused by profiles.role being NOT NULL.
alter table public.profiles
  alter column role set default 'user';

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public, auth
as $$
begin
  insert into public.profiles (id, username, avatar_url, job, bio, role, updated_at)
  values (
    new.id,
    coalesce(nullif(new.raw_user_meta_data->>'username', ''), 'user_' || substr(new.id::text, 1, 8)),
    nullif(new.raw_user_meta_data->>'avatar_url', ''),
    nullif(new.raw_user_meta_data->>'job', ''),
    nullif(new.raw_user_meta_data->>'bio', ''),
    'user',
    now()
  )
  on conflict (id) do update set
    username = coalesce(excluded.username, public.profiles.username),
    avatar_url = coalesce(excluded.avatar_url, public.profiles.avatar_url),
    job = coalesce(excluded.job, public.profiles.job),
    bio = coalesce(excluded.bio, public.profiles.bio),
    role = coalesce(public.profiles.role, 'user'),
    updated_at = now();

  return new;
end;
$$;

alter function public.handle_new_user() owner to postgres;

update public.profiles
set role = 'user'
where role is null;
