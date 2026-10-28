# KCK SERVICES — Car Rental Platform

KCK SERVICES COMPANY uses this system to **publish its rental cars, service packages and promotions**, take **online bookings**, and collect **customer feedback** that management approves and replies to.

It follows the same architecture as TRAX WORK PROJECT:

| Layer | Technology |
|---|---|
| Backend API | Python **FastAPI** + Uvicorn, Pydantic schemas, psycopg connection pool |
| API docs | **Swagger UI** (auto-generated at `/docs`) with an **Authorize** button |
| Database | **Supabase** PostgreSQL (`supabase/schema.sql`) with Row Level Security |
| Auth | Supabase Auth (email + password) → JWT Bearer token checked by FastAPI |
| File storage | Supabase Storage bucket `car-images` for car photos |
| Frontend | **React + Vite** |

---

## 1. Project Structure

```
KCK SERVICES/
├── README.md                     # This step-by-step guide
├── setup.ps1                     # One-click Windows installer (venv + pip + npm)
│
├── backend/                      # Python FastAPI Backend
│   ├── .env.example              # Template for Supabase keys + database URL
│   ├── requirements.txt          # FastAPI, uvicorn, pydantic, psycopg, supabase...
│   ├── main.py                   # App entry: Swagger config, CORS, router registration
│   └── kckservices/
│       ├── config.py             # Reads .env with Pydantic Settings
│       ├── database.py           # PostgreSQL connection pool (psycopg_pool)
│       ├── clients.py            # Supabase admin client + anon client factory
│       ├── dependencies.py       # Bearer-token auth: get_current_user / require_admin
│       ├── schemas.py            # Pydantic models (Create / Update / Out) for every table
│       ├── routers/
│       │   ├── health.py         # GET /health
│       │   ├── auth.py           # /auth  register, login, my profile, user roles
│       │   ├── cars.py           # /cars  CRUD + search/filter + availability + photo upload
│       │   ├── services.py       # /services  CRUD for rental service packages
│       │   ├── promotions.py     # /promotions  CRUD + promo code validation
│       │   ├── bookings.py       # /bookings  quote, book, cancel, admin status, delete
│       │   ├── feedback.py       # /feedback  reviews CRUD + admin moderation & reply
│       │   └── dashboard.py      # /dashboard/summary  revenue, bookings, ratings
│       └── services/
│           ├── crud.py           # Reusable safe INSERT / UPDATE / DELETE helpers
│           ├── pricing.py        # Rental days, service cost, discount, total price
│           ├── booking_rules.py  # Double-booking check + active promo lookup
│           └── storage.py        # Car photo validation & upload to Supabase Storage
│
├── frontend/                     # React + Vite Frontend
│   ├── .env.example              # VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_API_BASE_URL
│   ├── package.json
│   ├── vite.config.js            # Dev server on port 5173
│   ├── index.html
│   └── src/
│       ├── main.jsx              # React entry point
│       ├── App.jsx               # Header/tabs, login & register popup, role detection
│       ├── supabaseClient.js     # Supabase JS client + API base URL
│       ├── api.js                # fetch helper (adds Bearer token, readable errors)
│       ├── styles.js             # Shared inline styles / colours
│       └── components/
│           ├── CarCatalog.jsx    # Public car list, filters, booking form with price quote
│           ├── ServicesBoard.jsx # Published services + active promotions
│           ├── FeedbackWall.jsx  # Published reviews, write / edit / delete own review
│           ├── MyBookings.jsx    # Customer's bookings + cancel
│           ├── AdminPanel.jsx    # Dashboard, bookings, feedback moderation, users
│           └── EntityManager.jsx # Generic admin CRUD screen (cars, services, promotions)
│
└── supabase/
    └── schema.sql                # Tables, seed data, triggers, RLS policies, storage bucket
```

### Database tables (`supabase/schema.sql`)

| Table | Purpose | Key columns |
|---|---|---|
| `profiles` | One row per user (auto-created on sign-up) | `full_name`, `phone`, `role` (`customer` / `admin`) |
| `cars` | The rental fleet | `plate_number`, `brand`, `model`, `category`, `daily_rate`, `image_url`, `is_available` |
| `rental_services` | Packages KCK publishes | `title`, `price`, `price_unit` (`per_trip`, `per_day`...), `is_published` |
| `promotions` | Discount campaigns | `discount_percent`, `promo_code`, `valid_from`, `valid_until`, `is_active` |
| `bookings` | Customer rentals | `car_id`, `service_id`, dates, `total_price`, `status` (`pending` → `confirmed` → `completed` / `cancelled`) |
| `feedback` | Customer reviews | `rating` 1–5, `comment`, `is_published` (admin approval), `admin_reply` |

The schema also seeds **7 cars, 5 services and 2 promo codes** (`WELCOME10`, `WEEKEND15`) so the site has content right away.

---

## 2. Prerequisites (install once)

1. **Python 3.11 or newer**: https://www.python.org/downloads/ (tick *"Add python.exe to PATH"*)
2. **Node.js 18 or newer** (LTS): https://nodejs.org
3. A free **Supabase** account: https://supabase.com
4. A code editor such as VS Code (optional)

Check them in PowerShell:

```bash
python --version
```
```bash
node --version
```

---

## 3. Step-by-Step Setup

### Step 1: Create the Supabase project
1. Go to https://supabase.com/dashboard, then **New project**.
2. Name it `kck-services`, set a **database password** (write it down) and choose region **Southeast Asia (Singapore)**.
3. Wait about 2 minutes for it to finish creating.

### Step 2: Create the database tables
1. In Supabase, open **SQL Editor**, then **New query**.
2. Open `supabase/schema.sql`, copy **everything**, paste it in and click **Run**.
3. Open **Table Editor**. You should see `cars`, `rental_services`, `promotions`, `bookings`, `feedback` and `profiles`, with sample cars inside.
   > Running the script again **resets** these tables (drops and recreates them).

### Step 3: Turn off email confirmation (for development)
**Authentication → Sign In / Providers → Email** → switch **off** "Confirm email" → Save.
This lets new accounts log in immediately without clicking an email link.

### Step 4: Collect your keys
| Where in Supabase | Copy | Paste into |
|---|---|---|
| Project Settings → **API** → Project URL | `https://xxxx.supabase.co` | `SUPABASE_URL` and `VITE_SUPABASE_URL` |
| Project Settings → **API** → `anon` `public` key | long `eyJ...` string | `SUPABASE_ANON_KEY` and `VITE_SUPABASE_ANON_KEY` |
| Project Settings → **API** → `service_role` key | long `eyJ...` string | `SUPABASE_SERVICE_ROLE_KEY` (**backend only, keep secret**) |
| **Connect** button (top bar) → **Session pooler** → URI | `postgresql://postgres.xxxx:[YOUR-PASSWORD]@...pooler.supabase.com:5432/postgres` | `DATABASE_URL` (replace `[YOUR-PASSWORD]`) |

> Use the **Session pooler** URI, not "Direct connection". The direct one needs IPv6, which many home networks do not have.
> If your password contains special characters such as `@ # / :`, URL-encode them (for example `@` becomes `%40`).

### Step 5: Run the installer
Open PowerShell **inside the `KCK SERVICES` folder** and run:

```bash
powershell -ExecutionPolicy Bypass -File setup.ps1
```

This creates `backend/.venv`, installs the Python packages, runs `npm install` and creates both `.env` files from the templates.

<details>
<summary>Manual alternative (if you prefer typing each step)</summary>

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
cd ..\frontend
npm install
copy .env.example .env
```
</details>

### Step 6: Fill in the `.env` files
**`backend/.env`**
```
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...anon...
SUPABASE_SERVICE_ROLE_KEY=eyJ...service_role...
DATABASE_URL=postgresql://postgres.xxxx:YourPassword@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres
FRONTEND_ORIGIN=http://localhost:5173
STORAGE_BUCKET=car-images
```
**`frontend/.env`**
```
VITE_SUPABASE_URL=https://xxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...anon...
VITE_API_BASE_URL=http://localhost:8000
```

### Step 7: Start the backend (Terminal 1)
```bash
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn main:app --reload --port 8000
```
When you see `Application startup complete`, open:
- **Swagger UI:** http://localhost:8000/docs
- ReDoc (alternative docs): http://localhost:8000/redoc
- Health check: http://localhost:8000/health returns `{"ok": true, ...}`

### Step 8: Start the frontend (Terminal 2)
```bash
cd frontend
npm run dev
```
Open **http://localhost:5173**. You should see the KCK car catalogue.

### Step 9: Create your admin account
1. On the website click **Login / Register** → *New customer? Register* → create your account.
   (Or in Swagger: `POST /auth/register`.)
2. In Supabase **SQL Editor** run (use your own email):
   ```sql
   update public.profiles set role = 'admin' where email = 'you@example.com';
   ```
3. Log out and log in again. The **Admin** tab now appears.

---

## 4. Using Swagger UI (testing the CRUD API)

1. Open http://localhost:8000/docs (or the port your backend runs on, e.g. 8001).
2. Click the green **Authorize** button (top right).
3. In **username** type your email, in **password** your password. Leave *client_id* / *client_secret* empty.
4. Click **Authorize**, then **Close**. The padlocks are now closed, and Swagger sends
   `Authorization: Bearer <token>` with every request (it fetched the token from `POST /auth/token` for you).
   To switch account: **Authorize → Logout**, then log in as someone else.
5. Try the CRUD flow:

| CRUD | Endpoint | Who |
|---|---|---|
| **C**reate | `POST /cars` with body `{"plate_number":"KCK 9999","brand":"Toyota","model":"Vios","year":2025,"category":"sedan","daily_rate":140}` | admin |
| **R**ead | `GET /cars`, `GET /cars/{car_id}` (try filters `category=suv`, `search=myvi`) | everyone |
| **U**pdate | `PUT /cars/{car_id}` with body `{"daily_rate":150}` | admin |
| **D**elete | `DELETE /cars/{car_id}` (returns **204**) | admin |

The same Create / Read / Update / Delete pattern exists for `/services`, `/promotions`, `/bookings` and `/feedback`.

### Full endpoint list

| Tag | Method & path | Access | What it does |
|---|---|---|---|
| Health | `GET /health` | public | API alive check |
| Auth & Profile | `POST /auth/register` | public | Create a customer account |
| | `POST /auth/login` | public | Get an `access_token` |
| | `GET /auth/me` · `PUT /auth/me` | logged in | View / update my name & phone |
| | `GET /auth/users` · `PUT /auth/users/{id}/role` | admin | List users, promote/demote admin |
| Cars | `GET /cars` · `GET /cars/{id}` | public | List (filters: category, transmission, available_only, min/max rate, min_seats, search) / detail with average rating |
| | `GET /cars/{id}/availability?start_date=&end_date=` | public | Is the car free on those dates? |
| | `POST /cars` · `PUT /cars/{id}` · `DELETE /cars/{id}` | admin | Create / update / delete |
| | `POST /cars/{id}/image` | admin | Upload a JPG/PNG/WebP photo (max 5 MB) |
| Rental Services | `GET /services` · `GET /services/{id}` | public | Published packages (admin: `include_unpublished=true`) |
| | `POST` · `PUT /{id}` · `DELETE /{id}` | admin | Manage packages |
| Promotions | `GET /promotions` | public | Active promotions (admin: `include_inactive=true`) |
| | `GET /promotions/validate/{code}` | public | Check a promo code |
| | `POST` · `PUT /{id}` · `DELETE /{id}` | admin | Manage promotions |
| Bookings | `POST /bookings/quote` | public | Price calculation without booking |
| | `POST /bookings` | customer | Book a car (blocks double booking) |
| | `GET /bookings/me` · `GET /bookings/{id}` | customer | My bookings |
| | `PATCH /bookings/{id}/cancel` | customer | Cancel my pending/confirmed booking |
| | `GET /bookings` · `PUT /bookings/{id}/status` · `DELETE /bookings/{id}` | admin | All bookings, confirm/complete/cancel, delete |
| Customer Feedback | `GET /feedback` · `GET /feedback/{id}` | public | Published reviews (filters: car_id, min_rating) |
| | `POST /feedback` · `GET /feedback/me` | customer | Write a review / my reviews |
| | `PUT /feedback/{id}` · `DELETE /feedback/{id}` | owner (delete: owner or admin) | Edit (goes back to approval) / delete |
| | `PUT /feedback/{id}/moderate` | admin | Publish / unpublish, write public reply |
| Admin Dashboard | `GET /dashboard/summary` | admin | Revenue, booking counts, average rating, top cars |

### HTTP status codes you will see
`200` OK · `201` Created · `204` Deleted · `400` business rule broken (e.g. past date, expired promo) · `401` not logged in / bad token · `403` not admin / not your record · `404` not found · `409` conflict (duplicate plate, car already booked, car still has bookings) · `422` validation error (wrong field type, rating 9, end date before start date).

---

## 5. How the Components Connect

* **`CarCatalog.jsx` → `POST /bookings/quote` → `pricing.py`**: works out rental days × daily rate, plus the service package cost, minus the promo discount.
* **`CarCatalog.jsx` → `POST /bookings` → `booking_rules.py`**: locks the car row and rejects dates that overlap another pending/confirmed booking (**409**).
* **`dependencies.py`**: every protected endpoint reads the `Authorization: Bearer` token, verifies it with Supabase Auth, then loads the user's `role` from `profiles`. `require_admin` blocks non-admins with **403**.
* **`FeedbackWall.jsx` → `POST /feedback`**: reviews are saved with `is_published = false`. **`AdminPanel.jsx` → `PUT /feedback/{id}/moderate`** approves them and adds a public reply. Approved ratings feed the car's average rating.
* **`AdminPanel.jsx` → `POST /cars/{id}/image` → `storage.py`**: uploads the photo to the `car-images` bucket and saves its public URL on the car.
* **`EntityManager.jsx`**: one reusable React screen that does Create / Edit / Delete for cars, services and promotions. **`crud.py`** is its backend twin.

---

## 6. Troubleshooting

| Problem | Fix |
|---|---|
| `running scripts is disabled on this system` | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or use `powershell -ExecutionPolicy Bypass -File setup.ps1`. |
| `ValidationError ... Field required` when starting uvicorn | `backend/.env` is missing a value. Start uvicorn **from inside `backend/`**. |
| `Application Control policy has blocked this file` for `uvicorn.exe` | Windows policy has blocked the backend executable. Do not switch launchers or rename files to work around the policy. Ask your device administrator to review the Code Integrity or AppLocker logs and approve or deploy the trusted project dependency through the organization's normal process. Provide the blocked file path, event ID and time of the attempt. |
| `[Errno 10048] ... address already in use` on 8000 | Another server (e.g. TRAX) is running. Stop it, or use `--port 8001` and set `VITE_API_BASE_URL=http://localhost:8001`. |
| `connection timeout` / `could not translate host name` | Use the **Session pooler** URI in `DATABASE_URL` and check the password. |
| `psycopg ... no pq wrapper available` / `filename or extension is too long` | The folder path is too long for Windows. Move the project to a shorter path such as `Desktop\KCK SERVICES`, then delete and recreate `backend\.venv`. |
| Browser shows **CORS** error | `FRONTEND_ORIGIN` in `backend/.env` must match the URL in the browser bar exactly (comma-separate several). Restart uvicorn. |
| `401 Auth verification error` | The token expired (1 hour). Log in again and re-Authorize in Swagger. |
| No **Admin** tab | Run the `update public.profiles set role = 'admin' ...` SQL, then log out and log in again. |
| Registration says "confirm your email" | Turn off "Confirm email" (Step 3), or click the link in the email. |
| Photo upload fails | Re-run `schema.sql` (it creates the `car-images` bucket), or create a **public** bucket named `car-images` in Storage. |

---

## 7. Presentation Cheat Sheet

* **Problem:** KCK SERVICES needs one place to advertise its cars, services and promotions, accept bookings and show trustworthy customer reviews.
* **Solution:** a React website backed by a FastAPI REST API and a Supabase PostgreSQL database.
* **CRUD:** full Create / Read / Update / Delete on 5 resources (cars, services, promotions, bookings, feedback) plus profiles, documented live in **Swagger UI**.
* **Schemas:** Pydantic models validate every request (e.g. rating 1–5, plate number length, end date ≥ start date) and shape every response.
* **Security:** Supabase JWT login; role-based access (customer vs admin); Row Level Security in the database; the service-role key never leaves the backend.
* **Business rules:** automatic pricing with promo codes, double-booking prevention, review moderation with admin replies, live dashboard of revenue and ratings.
* **Demo flow:** browse cars → quote with `WELCOME10` → register → book → admin confirms → customer reviews → admin approves & replies → rating shows on the car card → dashboard updates.
