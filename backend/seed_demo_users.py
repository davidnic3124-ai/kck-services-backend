r"""Create (or reset) the demo accounts for presenting KCK SERVICES.

Run from the backend folder:
    .\.venv\Scripts\python.exe seed_demo_users.py

Safe to run again: existing demo users get their password reset and role re-applied.
Login details are listed in DEMO_ACCOUNTS.md in the project root.
"""
from kckservices.clients import supabase_admin
from kckservices.database import get_db, pool

DEMO_USERS = [
    {"email": "admin@kckservices.demo", "password": "KckAdmin#2026", "full_name": "KCK Admin", "phone": "03-1234 5678", "role": "admin"},
    {"email": "customer@kckservices.demo", "password": "KckCustomer#2026", "full_name": "Aisyah Customer", "phone": "012-345 6789", "role": "customer"},
]

def find_user_id(email: str):
    page = 1
    while True:
        users = supabase_admin.auth.admin.list_users(page=page, per_page=200)
        if not users:
            return None
        for u in users:
            if (u.email or "").lower() == email.lower():
                return u.id
        page += 1

def seed():
    for demo in DEMO_USERS:
        attributes = {
            "password": demo["password"],
            "email_confirm": True,  # can log in immediately, no confirmation email
            "user_metadata": {"full_name": demo["full_name"], "phone": demo["phone"]},
        }
        user_id = find_user_id(demo["email"])
        if user_id:
            supabase_admin.auth.admin.update_user_by_id(user_id, attributes)
            action = "updated"
        else:
            user_id = supabase_admin.auth.admin.create_user({"email": demo["email"], **attributes}).user.id
            action = "created"

        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO public.profiles (id, email, full_name, phone, role)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE
                    SET email = EXCLUDED.email, full_name = EXCLUDED.full_name,
                        phone = EXCLUDED.phone, role = EXCLUDED.role;
                    """,
                    (str(user_id), demo["email"], demo["full_name"], demo["phone"], demo["role"])
                )
            conn.commit()
        print(f"{action}: {demo['email']} ({demo['role']})")

if __name__ == "__main__":
    try:
        seed()
    finally:
        pool.close()
