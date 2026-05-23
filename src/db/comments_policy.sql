-- RLS policies for comments.
alter table public.comments enable row level security;

alter table public.comments
  add column if not exists is_deleted boolean not null default false,
  add column if not exists deleted_at timestamp with time zone,
  add column if not exists deleted_by uuid references public.profiles(id);

drop policy if exists "Comments are viewable by everyone." on public.comments;
drop policy if exists "Authenticated users can insert comments." on public.comments;
drop policy if exists "Users can delete their own comments." on public.comments;
drop policy if exists "Comments are viewable by everyone" on public.comments;
drop policy if exists "Authenticated users can insert comments" on public.comments;
drop policy if exists "Users can delete their own comments" on public.comments;
drop policy if exists "Comment owners and staff can soft delete comments" on public.comments;

create policy "Comments are viewable by everyone"
on public.comments for select
using (coalesce(is_deleted, false) = false);

-- Comment writes go through the Django community API, where content is
-- sanitized and owner/staff permissions are verified server-side.
