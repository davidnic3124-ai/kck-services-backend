# KCK SERVICES — Demo Accounts

Use these for the presentation. They are demo-only accounts (not real people).

| Role | Email | Password | What you can show |
|---|---|---|---|
| **Admin** | `admin@kckservices.demo` | `KckAdmin#2026` | Admin tab: dashboard, add/edit/delete cars, services and promotions, confirm bookings, approve and reply to reviews, manage users |
| **Customer** | `customer@kckservices.demo` | `KckCustomer#2026` | Book a car with promo code `WELCOME10`, view and cancel My Bookings, write a review |

Recreate or reset them at any time (for example, if a password was changed during the demo):

```bash
cd backend
.\.venv\Scripts\python.exe seed_demo_users.py
```

## Starting the backend

Start the backend from the `backend` folder with:

```powershell
uvicorn main:app --reload --port 8001
```

If Windows reports that an Application Control policy blocked `uvicorn.exe`, the server has not started. Do not try another launcher or rename the executable to work around the block. Ask your device administrator to review the Code Integrity or AppLocker logs and approve or deploy the trusted project dependency through the organization's normal process.

For the block observed on October 28, 2026, provide these Code Integrity details:

- Event IDs: `3077` and `3033`
- Time: `8:45:18 AM`
- Blocked file: `C:\Users\User\OneDrive\Desktop\KCK SERVICES\backend\.venv\Scripts\uvicorn.exe`
- Policy ID: `{0283ac0f-fff1-49ae-ada1-8a933130cad6}`
- AppLocker EXE and DLL log: no matching event found

After your administrator approves the trusted dependency through the normal process, retry the command above.

## Suggested demo flow (about 5 minutes)
1. **Visitor**: browse **Our Cars**, filter by category, open **Services & Promos**.
2. **Customer** login → Book Now → enter promo `WELCOME10` → **Get Price Quote** → **Confirm Booking** → **My Bookings** shows it as *pending*.
3. **Customer** → **Customer Feedback** → write a 5★ review (it shows "Awaiting approval").
4. Logout → **Admin** login → **Admin → Bookings**: set the booking to *confirmed*.
5. **Admin → Feedback**: write a reply → **Approve & Publish**.
6. **Admin → Dashboard**: revenue and ratings have updated. **Our Cars**: the car card now shows the star rating.
7. Open **http://localhost:8001/docs** (Swagger UI): **Authorize** → username = admin email, password → **Authorize** → **Close** → try `POST /cars`, `PUT /cars/{id}`, `DELETE /cars/{id}`.