-- Create trains table to store train information (if we decide to cache or store train data)
create table if not exists public.trains (
  id uuid default uuid_generate_v4() primary key,
  train_num text not null, -- 车次 (e.g. G101)
  from_station text not null,
  to_station text not null,
  start_time time not null,
  end_time time not null,
  duration text, -- 耗时
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Create train_stations table to store mapping between city names and codes
create table if not exists public.train_stations (
  id uuid default uuid_generate_v4() primary key,
  name text not null unique, -- 城市/车站名称 (e.g. 北京)
  code text not null unique, -- 车站代码 (e.g. BJP)
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Create train_orders table to store user ticket orders
create table if not exists public.train_orders (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references auth.users(id) not null,
  train_num text not null,
  from_station text not null,
  to_station text not null,
  departure_date date not null,
  departure_time time,
  arrival_time time,
  seat_type text not null, -- 商务座, 一等座, 二等座, etc.
  passenger_name text not null,
  passenger_id_card text not null, -- ID card number (should be encrypted in real app)
  status text check (status in ('pending', 'paid', 'cancelled', 'completed')) default 'pending',
  price numeric(10, 2),
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS
alter table public.trains enable row level security;
alter table public.train_stations enable row level security;
alter table public.train_orders enable row level security;

-- Policies
-- Trains and Stations are viewable by everyone
create policy "Trains viewable by everyone" on public.trains for select using (true);
create policy "Stations viewable by everyone" on public.train_stations for select using (true);

-- Orders are only viewable and insertable by the owner
create policy "Users can view own orders" on public.train_orders for select using (auth.uid() = user_id);
create policy "Users can insert own orders" on public.train_orders for insert with check (auth.uid() = user_id);
create policy "Users can update own orders" on public.train_orders for update using (auth.uid() = user_id);

-- Insert initial city data (example based on crawler code)
insert into public.train_stations (name, code) values 
('北京', 'BJP'),
('上海', 'SHH'),
('广州', 'GZQ'),
('深圳', 'SZQ'),
('杭州', 'HZQ'),
('天津', 'TZQ'),
('南京', 'HZH'),
('武汉', 'WHN'),
('西安', 'XAY'),
('成都', 'XAY'),
('重庆', 'CQW'),
('长沙', 'CSQ'),
('昆明', 'KMY'),
('厦门', 'KMM'),
('郑州', 'ZZF')
on conflict (code) do nothing;
