-- Create follows table if it doesn't exist
create table if not exists public.follows (
  id uuid default uuid_generate_v4() primary key,
  follower_id uuid references public.profiles(id) on delete cascade not null,
  following_id uuid references public.profiles(id) on delete cascade not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  unique(follower_id, following_id)
);

-- Enable RLS for follows
alter table public.follows enable row level security;

-- Follows Policies
drop policy if exists "Follows are viewable by everyone" on public.follows;
create policy "Follows are viewable by everyone" on public.follows for select using (true);

drop policy if exists "Authenticated users can follow others" on public.follows;
create policy "Authenticated users can follow others" on public.follows for insert with check (auth.uid() = follower_id);

drop policy if exists "Users can unfollow" on public.follows;
create policy "Users can unfollow" on public.follows for delete using (auth.uid() = follower_id);

-- Create follows_history table to track events
create table if not exists public.follows_history (
  id uuid default uuid_generate_v4() primary key,
  follower_id uuid references public.profiles(id) on delete cascade not null,
  following_id uuid references public.profiles(id) on delete cascade not null,
  event_type text check (event_type in ('follow', 'unfollow')) not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS for follows_history
alter table public.follows_history enable row level security;

-- Follows History Policies
drop policy if exists "History viewable by involved users" on public.follows_history;
create policy "History viewable by involved users" on public.follows_history for select using (auth.uid() = follower_id or auth.uid() = following_id);

drop policy if exists "System can insert history" on public.follows_history;
-- This policy is not needed as insertion happens via trigger with security definer
-- If direct insertion is needed, it should be restricted
-- create policy "System can insert history" on public.follows_history for insert with check (false);

-- Create trigger to automatically log history
create or replace function public.handle_follows_history()
returns trigger as $$
begin
  if (TG_OP = 'INSERT') then
    insert into public.follows_history (follower_id, following_id, event_type)
    values (NEW.follower_id, NEW.following_id, 'follow');
    return NEW;
  elsif (TG_OP = 'DELETE') then
    insert into public.follows_history (follower_id, following_id, event_type)
    values (OLD.follower_id, OLD.following_id, 'unfollow');
    return OLD;
  end if;
  return null;
end;
$$ language plpgsql security definer set search_path = public;

-- Drop trigger if exists to avoid duplication
drop trigger if exists on_follows_change on public.follows;

-- Create trigger
create trigger on_follows_change
after insert or delete on public.follows
for each row execute procedure public.handle_follows_history();
