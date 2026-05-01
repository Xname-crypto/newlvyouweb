begin;

alter table if exists public.api_providers enable row level security;

revoke all on table public.api_providers from anon;
revoke all on table public.api_providers from authenticated;

drop view if exists public.api_providers_public;
create view public.api_providers_public as
select
  id,
  capability,
  name,
  base_url,
  active,
  priority,
  (config->>'model_id') as model_id
from public.api_providers;

grant select on public.api_providers_public to anon;
grant select on public.api_providers_public to authenticated;

commit;

