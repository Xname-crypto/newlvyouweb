-- Fix for existing users without profiles
insert into public.profiles (id, username, avatar_url)
select id, raw_user_meta_data->>'full_name', raw_user_meta_data->>'avatar_url'
from auth.users
where id not in (select id from public.profiles);

-- Create storage bucket if not exists
insert into storage.buckets (id, name, public) 
values ('media', 'media', true)
on conflict (id) do nothing;

-- Storage policies
drop policy if exists "Public Access" on storage.objects;
create policy "Public Access"
on storage.objects for select
using ( bucket_id = 'media' );

drop policy if exists "Authenticated users can upload" on storage.objects;

drop policy if exists "Users can replace their own media" on storage.objects;
