-- Supabase Advisor WARN hardening.
-- Run after supabase_public_schema_hardening.sql.
--
-- This script intentionally avoids revoking broad authenticated access from
-- existing community/profile tables because the current frontend uses direct
-- Supabase reads for those features.

begin;

-- Fix function_search_path_mutable. These statements preserve existing function
-- bodies and only pin name resolution to trusted schemas.
alter function if exists public.handle_new_user() set search_path = public, auth;
alter function if exists public.delete_user(uuid) set search_path = public, auth;
alter function if exists public.update_user_role(uuid, text) set search_path = public, auth;
alter function if exists public.match_knowledge_base(vector, float, int) set search_path = public, extensions;

-- SECURITY DEFINER functions should not be callable by anonymous users.
revoke execute on function public.delete_user(uuid) from anon;
revoke execute on function public.force_logout_user(uuid) from anon;
revoke execute on function public.get_daily_user_growth(timestamptz, timestamptz) from anon;
revoke execute on function public.get_top_searched_cities(integer) from anon;
revoke execute on function public.handle_follows_history() from anon;
revoke execute on function public.handle_new_comment() from anon;
revoke execute on function public.handle_new_follow() from anon;
revoke execute on function public.handle_new_interaction() from anon;
revoke execute on function public.handle_new_user() from anon;
revoke execute on function public.is_banned() from anon;
revoke execute on function public.update_user_role(uuid, text) from anon;

-- Keep admin dashboard RPCs callable only by signed-in users; their function
-- bodies should still verify admin role before returning sensitive data.
grant execute on function public.delete_user(uuid) to authenticated;
grant execute on function public.force_logout_user(uuid) to authenticated;
grant execute on function public.get_daily_user_growth(timestamptz, timestamptz) to authenticated;
grant execute on function public.get_top_searched_cities(integer) to authenticated;
grant execute on function public.update_user_role(uuid, text) to authenticated;

-- Trigger functions are invoked by triggers, not directly by clients.
revoke execute on function public.handle_follows_history() from authenticated;
revoke execute on function public.handle_new_comment() from authenticated;
revoke execute on function public.handle_new_follow() from authenticated;
revoke execute on function public.handle_new_interaction() from authenticated;
revoke execute on function public.handle_new_user() from authenticated;

-- Payment data should only go through the Django API. The payment_orders RLS
-- policy is still the main data guard; revoking anon SELECT removes GraphQL
-- schema discovery for public users.
revoke select on table public.payment_orders from anon;

-- api_providers_public is not needed by the browser because the Django backend
-- already exposes /api/api-providers/public/. Hide the view from GraphQL.
revoke select on public.api_providers_public from anon;
revoke select on public.api_providers_public from authenticated;

-- Prevent anonymous GraphQL discovery for admin logs and usage logs. The admin
-- UI currently reads these as authenticated users, so authenticated SELECT is
-- left untouched here.
revoke select on table public.admin_logs from anon;
revoke select on table public.api_usage_logs from anon;

commit;
