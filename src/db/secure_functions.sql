-- Secure handle_new_user function
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, username, full_name, avatar_url)
  values (new.id, new.raw_user_meta_data->>'username', new.raw_user_meta_data->>'full_name', new.raw_user_meta_data->>'avatar_url');
  return new;
end;
$$ language plpgsql security definer set search_path = public;

-- Secure handle_new_comment function
create or replace function public.handle_new_comment()
returns trigger as $$
begin
  -- Logic for handling new comment (e.g. notifications)
  return new;
end;
$$ language plpgsql security definer set search_path = public;

-- Secure handle_new_interaction function
create or replace function public.handle_new_interaction()
returns trigger as $$
begin
  -- Logic for handling new interaction
  return new;
end;
$$ language plpgsql security definer set search_path = public;

-- Secure handle_new_follow function
create or replace function public.handle_new_follow()
returns trigger as $$
begin
  -- Logic for handling new follow
  return new;
end;
$$ language plpgsql security definer set search_path = public;
