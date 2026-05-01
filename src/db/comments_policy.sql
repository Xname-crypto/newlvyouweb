-- RLS Policies for Comments
alter table public.comments enable row level security;

-- Everyone can view comments
create policy "Comments are viewable by everyone." 
on public.comments for select 
using (true);

-- Authenticated users can insert comments
create policy "Authenticated users can insert comments." 
on public.comments for insert 
with check (auth.uid() = user_id);

-- Users can delete their own comments
create policy "Users can delete their own comments." 
on public.comments for delete 
using (auth.uid() = user_id);
