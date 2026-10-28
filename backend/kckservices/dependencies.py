from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from kckservices.clients import supabase_admin
from kckservices.database import get_db
from kckservices.schemas import CurrentUser

# OAuth2 password flow: Swagger's "Authorize" popup asks for email + password,
# calls POST /auth/token itself and then sends "Authorization: Bearer <token>" on every request.
# The React frontend sends the same header using the token from Supabase JS.
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/token",
    auto_error=False,
    description="Type your KCK **email** in the *username* box and your password, then click Authorize. "
                "Leave client_id / client_secret empty.",
)

def _resolve_user(token: str) -> CurrentUser:
    try:
        user_response = supabase_admin.auth.get_user(token)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Auth verification error: {str(e)}")
    if not user_response or not user_response.user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")

    user = user_response.user
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT role, full_name FROM public.profiles WHERE id = %s;", (user.id,))
            profile = cur.fetchone()
            if not profile:
                # Safety net in case the signup trigger was not installed
                cur.execute(
                    """
                    INSERT INTO public.profiles (id, email, full_name)
                    VALUES (%s, %s, %s)
                    RETURNING role, full_name;
                    """,
                    (user.id, user.email, (user.email or "customer").split("@")[0])
                )
                profile = cur.fetchone()
                conn.commit()

    return CurrentUser(id=str(user.id), email=user.email, full_name=profile["full_name"], role=profile["role"])

def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> CurrentUser:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not logged in. Click Authorize (top right of Swagger) and log in with your email and password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _resolve_user(token)

def get_optional_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[CurrentUser]:
    # Public endpoints: anonymous visitors allowed, admins get extra data
    if not token:
        return None
    return _resolve_user(token)

def require_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="KCK admin access required.")
    return user
