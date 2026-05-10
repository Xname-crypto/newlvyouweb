-- Supabase RLS hardening for commerce tables.
-- Apply in the Supabase SQL editor after Django migrations create the tables.

do $$
begin
  if to_regclass('public.products') is null then
    raise exception 'Missing table public.products. Run Django migrations against the Supabase Postgres database before applying this RLS policy.';
  end if;

  if to_regclass('public.payment_orders') is null then
    raise exception 'Missing table public.payment_orders. Run Django migrations against the Supabase Postgres database before applying this RLS policy.';
  end if;

  if to_regclass('public.payment_events') is null then
    raise exception 'Missing table public.payment_events. Run Django migrations against the Supabase Postgres database before applying this RLS policy.';
  end if;

  if to_regclass('public.commerce_orders') is null then
    raise exception 'Missing table public.commerce_orders. Run Django migrations against the Supabase Postgres database before applying this RLS policy.';
  end if;

  if to_regclass('public.commerce_order_items') is null then
    raise exception 'Missing table public.commerce_order_items. Run Django migrations against the Supabase Postgres database before applying this RLS policy.';
  end if;
end $$;

alter table public.products enable row level security;
alter table public.payment_orders enable row level security;
alter table public.payment_events enable row level security;
alter table public.commerce_orders enable row level security;
alter table public.commerce_order_items enable row level security;

drop policy if exists "Active products are public" on public.products;
create policy "Active products are public"
on public.products
for select
to anon, authenticated
using (is_active = true);

drop policy if exists "Users can view own payment orders" on public.payment_orders;
create policy "Users can view own payment orders"
on public.payment_orders
for select
to authenticated
using ((select auth.uid())::text = user_id);

drop policy if exists "Users can view own commerce orders" on public.commerce_orders;
create policy "Users can view own commerce orders"
on public.commerce_orders
for select
to authenticated
using ((select auth.uid())::text = user_id);

drop policy if exists "Users can view own commerce order items" on public.commerce_order_items;
create policy "Users can view own commerce order items"
on public.commerce_order_items
for select
to authenticated
using (
  exists (
    select 1
    from public.commerce_orders
    where public.commerce_orders.id = public.commerce_order_items.order_id
      and public.commerce_orders.user_id = (select auth.uid())::text
  )
);

revoke all on table public.commerce_orders from anon;
revoke all on table public.commerce_order_items from anon;

-- Do not allow browser clients to insert, update, or delete commerce data.
-- Django performs writes server-side after Supabase token verification.
