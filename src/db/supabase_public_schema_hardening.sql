-- Supabase public schema hardening for Django-managed tables.
-- Run this after Django migrations in the Supabase SQL editor.
--
-- Supabase exposes the public schema through PostgREST. Django internal tables
-- must therefore have RLS enabled and no browser role access unless a table has
-- an explicit client-side use case.

begin;

-- Fix Supabase Advisor: security_definer_view on api_providers_public.
-- Postgres 15+ supports security_invoker views, so the view uses the caller's
-- permissions/RLS rather than the view owner's.
do $$
begin
  if to_regclass('public.api_providers') is not null then
    drop view if exists public.api_providers_public;

    create view public.api_providers_public
    with (security_invoker = true)
    as
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
  end if;
end $$;

-- Lock down Django/Auth/internal tables that should never be accessed directly
-- from browser clients. Service-role/Django connections are not limited by RLS.
do $$
declare
  table_name text;
  table_names text[] := array[
    'embedding_profile',
    'auth_group',
    'auth_group_permissions',
    'auth_permission',
    'auth_user',
    'auth_user_groups',
    'auth_user_user_permissions',
    'django_admin_log',
    'django_content_type',
    'django_migrations',
    'django_session',
    'admin_qa_test_session',
    'admin_qa_test_message',
    'datasource_manager_datasource',
    'payment_events'
  ];
begin
  foreach table_name in array table_names loop
    if to_regclass(format('public.%I', table_name)) is not null then
      execute format('alter table public.%I enable row level security', table_name);
      execute format('revoke all on table public.%I from anon', table_name);
      execute format('revoke all on table public.%I from authenticated', table_name);
    end if;
  end loop;
end $$;

-- Travel tables are written/read through Django APIs. Frontend direct access is
-- intentionally denied unless later policies are added for a specific feature.
do $$
declare
  table_name text;
  table_names text[] := array[
    'travel_booking_intent',
    'travel_discovery_signal',
    'travel_itinerary_item'
  ];
begin
  foreach table_name in array table_names loop
    if to_regclass(format('public.%I', table_name)) is not null then
      execute format('alter table public.%I enable row level security', table_name);
      execute format('revoke all on table public.%I from anon', table_name);
      execute format('revoke all on table public.%I from authenticated', table_name);
    end if;
  end loop;
end $$;

commit;
