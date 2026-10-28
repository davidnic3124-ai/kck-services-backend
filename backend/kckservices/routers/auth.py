from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from kckservices.clients import new_anon_client
from kckservices.database import get_db
from kckservices.dependencies import get_current_user, require_admin
from kckservices.schemas import (
    AuthResponse, CurrentUser, LoginRequest, ProfileOut, ProfileUpdate, RegisterRequest, RoleUpdate
)

router = APIRouter(prefix="/auth", tags=["Auth & Profile"])

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest):
    client = new_anon_client()
    try:
        res = client.auth.sign_up({
            "email": payload.email,
            "password": payload.password,
            "options": {"data": {"full_name": payload.full_name, "phone": payload.phone}},
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Registration failed: {str(e)}")
    if not res.user:
        raise HTTPException(status_code=400, detail="Registration failed.")

    # The signup trigger creates the profile; make sure name/phone are filled in
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE public.profiles SET full_name = %s, phone = COALESCE(%s, phone) WHERE id = %s;",
                (payload.full_name, payload.phone, str(res.user.id))
            )
        conn.commit()

    if res.session:
        return AuthResponse(
            message="Registered and logged in.",
            user_id=str(res.user.id),
            email=res.user.email,
            access_token=res.session.access_token,
            expires_in=res.session.expires_in,
        )
    return AuthResponse(
        message="Registered. Please confirm your email address, then log in.",
        user_id=str(res.user.id),
        email=res.user.email,
    )

@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest):
    client = new_anon_client()
    try:
        res = client.auth.sign_in_with_password({"email": payload.email, "password": payload.password})
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Login failed: {str(e)}")
    if not res.session:
        raise HTTPException(status_code=401, detail="Login failed.")
    return AuthResponse(
        message="Login successful. In Swagger, use the Authorize button to log in for all requests.",
        user_id=str(res.user.id),
        email=res.user.email,
        access_token=res.session.access_token,
        expires_in=res.session.expires_in,
    )

@router.post("/token", summary="Swagger Authorize login (OAuth2 form)")
def login_for_swagger(form: OAuth2PasswordRequestForm = Depends()):
    """Used by the **Authorize** button. `username` = your email."""
    client = new_anon_client()
    try:
        res = client.auth.sign_in_with_password({"email": form.username.strip(), "password": form.password})
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Login failed: {str(e)}", headers={"WWW-Authenticate": "Bearer"})
    if not res.session:
        raise HTTPException(status_code=401, detail="Login failed.", headers={"WWW-Authenticate": "Bearer"})
    return {"access_token": res.session.access_token, "token_type": "bearer", "expires_in": res.session.expires_in}

@router.get("/me", response_model=ProfileOut)
def get_my_profile(user: CurrentUser = Depends(get_current_user)):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM public.profiles WHERE id = %s;", (user.id,))
            return cur.fetchone()

@router.put("/me", response_model=ProfileOut)
def update_my_profile(payload: ProfileUpdate, user: CurrentUser = Depends(get_current_user)):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE public.profiles
                SET full_name = COALESCE(%s, full_name),
                    phone = COALESCE(%s, phone)
                WHERE id = %s
                RETURNING *;
                """,
                (payload.full_name, payload.phone, user.id)
            )
            row = cur.fetchone()
        conn.commit()
        return row

@router.get("/users", response_model=list[ProfileOut])
def list_users(admin: CurrentUser = Depends(require_admin)):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM public.profiles ORDER BY created_at DESC;")
            return cur.fetchall()

@router.put("/users/{user_id}/role", response_model=ProfileOut)
def change_user_role(user_id: str, payload: RoleUpdate, admin: CurrentUser = Depends(require_admin)):
    if user_id == admin.id and payload.role != "admin":
        raise HTTPException(status_code=400, detail="You cannot remove your own admin role.")
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE public.profiles SET role = %s WHERE id = %s RETURNING *;", (payload.role, user_id))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="User not found.")
        conn.commit()
        return row
