-- Enable RLS for all tables
alter table public.profiles enable row level security;
alter table public.posts enable row level security;
alter table public.comments enable row level security;
alter table public.interactions enable row level security;

-- 1. Profiles Policies
drop policy if exists "Public profiles are viewable by everyone" on public.profiles;
create policy "Public profiles are viewable by everyone" on public.profiles for select using (true);

drop policy if exists "Users can insert their own profile" on public.profiles;
create policy "Users can insert their own profile" on public.profiles for insert with check (auth.uid() = id);

drop policy if exists "Users can update own profile" on public.profiles;
create policy "Users can update own profile" on public.profiles for update using (auth.uid() = id);

-- 2. Posts Policies
drop policy if exists "Posts are viewable by everyone" on public.posts;
create policy "Posts are viewable by everyone" on public.posts for select using (true);

drop policy if exists "Users can insert their own posts" on public.posts;
create policy "Users can insert their own posts" on public.posts for insert with check (auth.uid() = user_id);

-- 3. Comments Policies
drop policy if exists "Comments are viewable by everyone" on public.comments;
create policy "Comments are viewable by everyone" on public.comments for select using (true);

drop policy if exists "Authenticated users can insert comments" on public.comments;
create policy "Authenticated users can insert comments" on public.comments for insert with check (auth.uid() = user_id);

drop policy if exists "Users can delete their own comments" on public.comments;
create policy "Users can delete their own comments" on public.comments for delete using (auth.uid() = user_id);

-- 4. Interactions Policies
drop policy if exists "Interactions are viewable by everyone" on public.interactions;
create policy "Interactions are viewable by everyone" on public.interactions for select using (true);

drop policy if exists "Authenticated users can insert interactions" on public.interactions;
create policy "Authenticated users can insert interactions" on public.interactions for insert with check (auth.uid() = user_id);

drop policy if exists "Users can delete their own interactions" on public.interactions;
create policy "Users can delete their own interactions" on public.interactions for delete using (auth.uid() = user_id);
