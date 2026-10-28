# Presenting the KCK SERVICES Swagger UI

Open **http://localhost:8001/docs** before you start (backend must be running).
Logins are in `DEMO_ACCOUNTS.md`. Total time: about 6–8 minutes.

---

## Part 1: What Swagger UI is (30 seconds)
> "This is Swagger UI. FastAPI generates it automatically from my Python code: every route, every Pydantic schema and every validation rule. So the documentation can never be out of date, and I can test the API live without the frontend."

Point at:
- The **title and description** at the top.
- The **coloured groups (tags)**: Health, Auth & Profile, Cars, Rental Services, Promotions, Bookings, Customer Feedback, Admin Dashboard. "Each tag is one router file in `kckservices/routers/`."
- **Method colours**: GET (blue) = read, POST (green) = create, PUT (orange) = update, PATCH = partial change, DELETE (red) = delete. "That is CRUD."
- **Padlock icons**: 🔒 = must be logged in. No padlock = public (anyone visiting the website).

## Part 2: A public endpoint (1 minute)
1. `GET /health` → **Try it out** → **Execute** → `{"ok": true}`. "The API is alive."
2. `GET /cars` → Try it out → set `category = suv` or `search = myvi` → Execute.
   - Show the **Request URL** (the query string your filters made).
   - Show the **Response body** (JSON list of cars, including `average_rating` from reviews).
   - Show the **status code 200**.
   > "This is exactly the call the React car catalogue makes."

## Part 3: Security (1 minute)
1. Without logging in, try `POST /cars` → Execute → **401 Not logged in**.
   > "Protected endpoints reject anonymous users."
2. Click **Authorize** (top right) → username = **customer** email, password → **Authorize** → **Close**.
   > "Swagger sends my email and password to `POST /auth/token`. My backend checks them with Supabase Auth and returns a JWT token. From now on, Swagger attaches `Authorization: Bearer <token>` to every request, exactly like the website does."
3. `GET /auth/me` → Execute → shows `"role": "customer"`.
4. Try `POST /cars` again → **403 KCK admin access required**.
   > "Logged in is not enough: the role must be admin. That check is `require_admin` in `dependencies.py`."
5. **Authorize → Logout**, then **Authorize** again with the **admin** account. `GET /auth/me` → `"role": "admin"`.

## Part 4: Full CRUD on Cars (2–3 minutes), the main part
| Step | Endpoint | What to show |
|---|---|---|
| **Create** | `POST /cars` → Try it out, edit the example body (e.g. `"plate_number": "DEMO 1"`, `"brand": "Toyota"`, `"model": "Vios"`, `"category": "sedan"`, `"daily_rate": 140`) → Execute | **201 Created**, new car with its generated `id`. **Copy the id.** |
| **Read** | `GET /cars/{car_id}` → paste the id → Execute | **200**, the same car |
| **Update** | `PUT /cars/{car_id}` → body `{"daily_rate": 155}` → Execute | **200**, price changed, `updated_at` changed |
| **Delete** | `DELETE /cars/{car_id}` → Execute | **204 No Content** |
| **Proof** | `GET /cars/{car_id}` again | **404 Car not found** |

Optionally open the website (http://localhost:5173) between steps to show the new car appearing and disappearing in the catalogue. That proves the frontend and Swagger use the same API.

## Part 5: Validation by the schemas (1 minute)
Show that Pydantic schemas protect the database:
- `POST /cars` with `"year": 1800` → **422**. The response says exactly which field is wrong and why.
- `POST /cars` with a plate number that already exists → **409 Conflict**.
- Scroll to the bottom → **Schemas** section → open `CarCreate`, `BookingCreate`, `FeedbackCreate`.
  > "These are the Pydantic models in `schemas.py`. They show the required fields, types, allowed values (like category) and limits (rating 1–5)."

## Part 6: Business logic (1–2 minutes, if time allows)
1. `POST /bookings/quote` with a car id, dates, `"promo_code": "WELCOME10"` → shows rental days, subtotal, discount and total.
   > "Pricing is calculated on the server in `pricing.py`, so customers cannot change the price."
2. `POST /bookings` twice with the same car and dates → second one gives **409 already booked**. "Double-booking prevention."
3. `PUT /feedback/{id}/moderate` with `{"is_published": true, "admin_reply": "Thank you!"}` → the review becomes public.
4. `GET /dashboard/summary` → revenue, bookings by status, average rating, top cars.

## Closing line
> "So Swagger UI documents and tests the same REST API that my React frontend uses: 40+ endpoints, full CRUD on five resources, JWT security with customer and admin roles, and Pydantic validation on every request."

---

### Status codes cheat sheet (your tutor may ask)
| Code | Meaning in KCK |
|---|---|
| 200 | OK, data returned |
| 201 | Created (new car, booking, review...) |
| 204 | Deleted, nothing to return |
| 400 | Business rule broken (past date, expired promo, cancelling a completed booking) |
| 401 | Not logged in, or wrong password |
| 403 | Logged in but not allowed (customer doing admin work, editing someone else's review) |
| 404 | Not found (or hidden from you) |
| 409 | Conflict (duplicate plate, car already booked, car still has bookings) |
| 422 | Validation error from the Pydantic schema |

### If something goes wrong during the demo
- **Authorize says "Auth error"**: check the email and password, and that the backend is running.
- **401 after a while**: the token expired (1 hour). Use Authorize → Logout → log in again.
- **Swagger page won't load**: the backend isn't running on 8001. Start it from the `backend` folder:
  `.\.venv\Scripts\Activate.ps1; uvicorn main:app --reload --port 8001`
