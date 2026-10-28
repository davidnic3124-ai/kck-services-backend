-- KCK SERVICES - Car Rental Platform
-- Run this whole file in Supabase Dashboard -> SQL Editor -> New query -> Run.
-- WARNING: it drops and recreates the KCK tables (your data in them will be reset).

create extension if not exists pgcrypto;

drop table if exists public.feedback cascade;
drop table if exists public.bookings cascade;
drop table if exists public.promotions cascade;
drop table if exists public.rental_services cascade;
drop table if exists public.cars cascade;
drop table if exists public.profiles cascade;

-- ---------------------------------------------------------------------------
-- Shared trigger: keep updated_at fresh on every UPDATE
-- ---------------------------------------------------------------------------
create or replace function public.set_updated_at() returns trigger
language plpgsql as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

-- ---------------------------------------------------------------------------
-- 1. PROFILES (one row per Supabase Auth user; role decides admin access)
-- ---------------------------------------------------------------------------
create table public.profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    email text,
    full_name varchar(120),
    phone varchar(30),
    role varchar(20) not null default 'customer' check (role in ('customer', 'admin')),
    created_at timestamp with time zone default now() not null,
    updated_at timestamp with time zone default now() not null
);

create or replace function public.handle_new_user() returns trigger
language plpgsql security definer set search_path = public as $$
begin
    insert into public.profiles (id, email, full_name, phone)
    values (
        new.id,
        new.email,
        coalesce(new.raw_user_meta_data->>'full_name', split_part(new.email, '@', 1)),
        new.raw_user_meta_data->>'phone'
    )
    on conflict (id) do nothing;
    return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
    after insert on auth.users
    for each row execute function public.handle_new_user();

-- Backfill profiles for users that already existed before this script ran
insert into public.profiles (id, email, full_name)
select id, email, split_part(email, '@', 1) from auth.users
on conflict (id) do nothing;

-- ---------------------------------------------------------------------------
-- 2. CARS (the rental fleet)
-- ---------------------------------------------------------------------------
create table public.cars (
    id uuid primary key default gen_random_uuid(),
    plate_number varchar(15) unique not null,
    brand varchar(60) not null,
    model varchar(60) not null,
    year integer not null check (year between 1990 and 2100),
    category varchar(20) not null check (category in ('sedan', 'hatchback', 'suv', 'mpv', 'pickup', 'van', 'luxury')),
    transmission varchar(10) not null default 'auto' check (transmission in ('auto', 'manual')),
    seats integer not null default 5 check (seats between 2 and 15),
    fuel_type varchar(10) not null default 'petrol' check (fuel_type in ('petrol', 'diesel', 'hybrid', 'electric')),
    daily_rate numeric(10, 2) not null check (daily_rate > 0),
    image_url text,
    description text,
    is_available boolean not null default true,
    created_at timestamp with time zone default now() not null,
    updated_at timestamp with time zone default now() not null
);

insert into public.cars (plate_number, brand, model, year, category, transmission, seats, fuel_type, daily_rate, description)
values
  ('KCK 1001', 'Perodua', 'Axia',   2024, 'hatchback', 'auto', 5, 'petrol', 90.00,  'Fuel-saving city car. Perfect for short trips around town.'),
  ('KCK 1002', 'Perodua', 'Myvi',   2024, 'hatchback', 'auto', 5, 'petrol', 110.00, 'Malaysia''s favourite compact. Roomy, reliable and easy to park.'),
  ('KCK 2001', 'Proton',  'Saga',   2023, 'sedan',     'auto', 5, 'petrol', 100.00, 'Comfortable budget sedan with a big boot.'),
  ('KCK 2002', 'Honda',   'City',   2024, 'sedan',     'auto', 5, 'hybrid', 160.00, 'Smooth hybrid sedan for business and long-distance travel.'),
  ('KCK 3001', 'Proton',  'X50',    2024, 'suv',       'auto', 5, 'petrol', 200.00, 'Compact SUV with high seating position and modern safety features.'),
  ('KCK 4001', 'Toyota',  'Alphard',2023, 'luxury',    'auto', 7, 'petrol', 650.00, 'Premium MPV for VIP transfers, weddings and corporate events.'),
  ('KCK 5001', 'Toyota',  'Hilux',  2023, 'pickup',    'manual', 5, 'diesel', 250.00, '4x4 pickup for cargo, outstation and rough-road trips.');

-- ---------------------------------------------------------------------------
-- 3. RENTAL SERVICES (packages / add-ons the company publishes)
-- ---------------------------------------------------------------------------
create table public.rental_services (
    id uuid primary key default gen_random_uuid(),
    title varchar(120) not null,
    description text,
    price numeric(10, 2) not null default 0 check (price >= 0),
    price_unit varchar(20) not null default 'per_trip' check (price_unit in ('per_hour', 'per_day', 'per_trip', 'per_month')),
    is_published boolean not null default true,
    created_at timestamp with time zone default now() not null,
    updated_at timestamp with time zone default now() not null
);

insert into public.rental_services (title, description, price, price_unit)
values
  ('Self-Drive Rental',        'Pick up the car and drive yourself. Car rate only, no extra charge.', 0.00,   'per_trip'),
  ('Chauffeur Service',        'Professional KCK driver included for the whole rental period.',      150.00, 'per_day'),
  ('Airport Pickup & Drop-off','Car delivered to / collected from KLIA or KLIA2.',                     80.00,  'per_trip'),
  ('Wedding Car Package',      'Decorated car with chauffeur for your special day.',                  350.00, 'per_trip'),
  ('Monthly Long-Term Rental', 'Discounted fixed monthly plan with free maintenance.',                1800.00,'per_month');

-- ---------------------------------------------------------------------------
-- 4. PROMOTIONS (discount codes the company publishes)
-- ---------------------------------------------------------------------------
create table public.promotions (
    id uuid primary key default gen_random_uuid(),
    title varchar(120) not null,
    description text,
    discount_percent integer not null check (discount_percent between 0 and 100),
    promo_code varchar(30) unique,
    valid_from date not null default current_date,
    valid_until date not null,
    is_active boolean not null default true,
    created_at timestamp with time zone default now() not null,
    updated_at timestamp with time zone default now() not null,
    check (valid_until >= valid_from)
);

insert into public.promotions (title, description, discount_percent, promo_code, valid_from, valid_until)
values
  ('Welcome Discount', '10% off your first KCK rental.',              10, 'WELCOME10', '2026-01-01', '2027-12-31'),
  ('Weekend Getaway',  '15% off your weekend road trip.',             15, 'WEEKEND15', '2026-01-01', '2027-12-31');

-- ---------------------------------------------------------------------------
-- 5. BOOKINGS (customer rental requests)
-- ---------------------------------------------------------------------------
create table public.bookings (
    id uuid primary key default gen_random_uuid(),
    customer_id uuid not null references public.profiles(id) on delete cascade,
    car_id uuid not null references public.cars(id) on delete restrict,
    service_id uuid references public.rental_services(id) on delete set null,
    promotion_id uuid references public.promotions(id) on delete set null,
    start_date date not null,
    end_date date not null,
    rental_days integer not null check (rental_days > 0),
    pickup_location varchar(200) not null,
    notes text,
    subtotal numeric(10, 2) not null default 0,
    discount_amount numeric(10, 2) not null default 0,
    total_price numeric(10, 2) not null default 0,
    status varchar(20) not null default 'pending' check (status in ('pending', 'confirmed', 'completed', 'cancelled')),
    created_at timestamp with time zone default now() not null,
    updated_at timestamp with time zone default now() not null,
    check (end_date >= start_date)
);

create index bookings_car_dates_idx on public.bookings (car_id, start_date, end_date);

-- ---------------------------------------------------------------------------
-- 6. FEEDBACK (customer reviews; admin approves before they are public)
-- ---------------------------------------------------------------------------
create table public.feedback (
    id uuid primary key default gen_random_uuid(),
    customer_id uuid not null references public.profiles(id) on delete cascade,
    car_id uuid references public.cars(id) on delete set null,
    booking_id uuid references public.bookings(id) on delete set null,
    rating smallint not null check (rating between 1 and 5),
    title varchar(120),
    comment text not null,
    is_published boolean not null default false,
    admin_reply text,
    created_at timestamp with time zone default now() not null,
    updated_at timestamp with time zone default now() not null
);

-- updated_at triggers
create trigger profiles_updated_at before update on public.profiles for each row execute function public.set_updated_at();
create trigger cars_updated_at before update on public.cars for each row execute function public.set_updated_at();
create trigger services_updated_at before update on public.rental_services for each row execute function public.set_updated_at();
create trigger promotions_updated_at before update on public.promotions for each row execute function public.set_updated_at();
create trigger bookings_updated_at before update on public.bookings for each row execute function public.set_updated_at();
create trigger feedback_updated_at before update on public.feedback for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------------
-- ROW LEVEL SECURITY
-- The FastAPI backend connects with DATABASE_URL (postgres role) and enforces
-- its own rules; these policies protect direct access with the anon key.
-- ---------------------------------------------------------------------------
alter table public.profiles enable row level security;
alter table public.cars enable row level security;
alter table public.rental_services enable row level security;
alter table public.promotions enable row level security;
alter table public.bookings enable row level security;
alter table public.feedback enable row level security;

create policy "Users view own profile" on public.profiles
    for select using (auth.uid() = id);
create policy "Users update own profile" on public.profiles
    for update using (auth.uid() = id) with check (auth.uid() = id);

create policy "Public can view cars" on public.cars
    for select using (true);

create policy "Public can view published services" on public.rental_services
    for select using (is_published = true);

create policy "Public can view active promotions" on public.promotions
    for select using (is_active = true);

create policy "Customers view own bookings" on public.bookings
    for select using (auth.uid() = customer_id);
create policy "Customers create own bookings" on public.bookings
    for insert with check (auth.uid() = customer_id);

create policy "Public view published feedback, owners view own" on public.feedback
    for select using (is_published = true or auth.uid() = customer_id);
create policy "Customers manage own feedback" on public.feedback
    for all using (auth.uid() = customer_id) with check (auth.uid() = customer_id);

-- ---------------------------------------------------------------------------
-- STORAGE: public bucket for car photos
-- ---------------------------------------------------------------------------
insert into storage.buckets (id, name, public)
values ('car-images', 'car-images', true)
on conflict (id) do nothing;

drop policy if exists "Public can view car images" on storage.objects;
create policy "Public can view car images" on storage.objects
    for select using (bucket_id = 'car-images');

-- ---------------------------------------------------------------------------
-- MAKE YOURSELF ADMIN (run after you register your account):
--   update public.profiles set role = 'admin' where email = 'you@example.com';
-- ---------------------------------------------------------------------------