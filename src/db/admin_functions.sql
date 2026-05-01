
-- Function for admin to delete users from auth.users (requires security definer)
-- This cascades to public.profiles due to FK constraint
create or replace function public.delete_user(target_user_id uuid)
returns void as $$
begin
  -- Check if executing user is admin
  if not exists (
    select 1 from public.profiles
    where id = auth.uid() and role = 'admin'
  ) then
    raise exception 'Access denied. Only admins can delete users.';
  end if;

  -- Delete from auth.users
  delete from auth.users where id = target_user_id;
end;
$$ language plpgsql security definer;
