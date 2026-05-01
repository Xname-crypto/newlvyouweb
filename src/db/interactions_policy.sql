-- RLS Policies for Interactions
alter table public.interactions enable row level security;

-- Everyone can view interactions (to count them)
create policy "Interactions are viewable by everyone." 
on public.interactions for select 
using (true);

-- Authenticated users can insert interactions (like/collect)
create policy "Authenticated users can insert interactions." 
on public.interactions for insert 
with check (auth.uid() = user_id);

-- Users can delete their own interactions (unlike/uncollect)
create policy "Users can delete their own interactions." 
on public.interactions for delete 
using (auth.uid() = user_id);
