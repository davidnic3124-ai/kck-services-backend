from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from kckservices.database import get_db
from kckservices.dependencies import get_current_user, get_optional_user, require_admin
from kckservices.schemas import CurrentUser, FeedbackCreate, FeedbackModerate, FeedbackOut, FeedbackUpdate
from kckservices.services.crud import delete_row, get_row, update_row

router = APIRouter(prefix="/feedback", tags=["Customer Feedback"])

FEEDBACK_SELECT = """
    SELECT f.*,
           p.full_name AS customer_name,
           CASE WHEN c.id IS NULL THEN NULL ELSE c.brand || ' ' || c.model END AS car_label
    FROM public.feedback f
    JOIN public.profiles p ON p.id = f.customer_id
    LEFT JOIN public.cars c ON c.id = f.car_id
"""

def fetch_feedback(conn, feedback_id) -> dict:
    with conn.cursor() as cur:
        cur.execute(f"{FEEDBACK_SELECT} WHERE f.id = %s;", (str(feedback_id),))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Feedback not found.")
    return row

@router.get("", response_model=list[FeedbackOut])
def list_feedback(
    car_id: Optional[UUID] = None,
    min_rating: Optional[int] = Query(None, ge=1, le=5),
    include_unpublished: bool = False,
    user: Optional[CurrentUser] = Depends(get_optional_user),
):
    conditions, params = [], []
    if not (include_unpublished and user is not None and user.role == "admin"):
        conditions.append("f.is_published = true")
    if car_id:
        conditions.append("f.car_id = %s")
        params.append(str(car_id))
    if min_rating:
        conditions.append("f.rating >= %s")
        params.append(min_rating)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(f"{FEEDBACK_SELECT} {where} ORDER BY f.created_at DESC;", params)
            return cur.fetchall()

@router.get("/me", response_model=list[FeedbackOut])
def list_my_feedback(user: CurrentUser = Depends(get_current_user)):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(f"{FEEDBACK_SELECT} WHERE f.customer_id = %s ORDER BY f.created_at DESC;", (user.id,))
            return cur.fetchall()

@router.get("/{feedback_id}", response_model=FeedbackOut)
def get_feedback(feedback_id: UUID, user: Optional[CurrentUser] = Depends(get_optional_user)):
    with get_db() as conn:
        row = fetch_feedback(conn, feedback_id)
    is_owner_or_admin = user is not None and (str(row["customer_id"]) == user.id or user.role == "admin")
    if not row["is_published"] and not is_owner_or_admin:
        raise HTTPException(status_code=404, detail="Feedback not found.")
    return row

@router.post("", response_model=FeedbackOut, status_code=status.HTTP_201_CREATED)
def create_feedback(payload: FeedbackCreate, user: CurrentUser = Depends(get_current_user)):
    car_id = str(payload.car_id) if payload.car_id else None
    booking_id = str(payload.booking_id) if payload.booking_id else None

    with get_db() as conn:
        if booking_id:
            booking = get_row(conn, "bookings", booking_id, "booking")
            if str(booking["customer_id"]) != user.id:
                raise HTTPException(status_code=403, detail="You can only review your own bookings.")
            car_id = car_id or str(booking["car_id"])
        if car_id:
            get_row(conn, "cars", car_id, "car")

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.feedback (customer_id, car_id, booking_id, rating, title, comment)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id;
                """,
                (user.id, car_id, booking_id, payload.rating, payload.title, payload.comment)
            )
            feedback_id = cur.fetchone()["id"]
        conn.commit()
        return fetch_feedback(conn, feedback_id)

@router.put("/{feedback_id}", response_model=FeedbackOut)
def update_my_feedback(feedback_id: UUID, payload: FeedbackUpdate, user: CurrentUser = Depends(get_current_user)):
    with get_db() as conn:
        row = fetch_feedback(conn, feedback_id)
        if str(row["customer_id"]) != user.id:
            raise HTTPException(status_code=403, detail="You can only edit your own feedback.")
        changes = payload.model_dump(exclude_none=True)
        if changes:
            changes["is_published"] = False  # edited reviews go back to the approval queue
        update_row(conn, "feedback", feedback_id, changes, "feedback")
        return fetch_feedback(conn, feedback_id)

@router.put("/{feedback_id}/moderate", response_model=FeedbackOut)
def moderate_feedback(feedback_id: UUID, payload: FeedbackModerate, admin: CurrentUser = Depends(require_admin)):
    with get_db() as conn:
        update_row(conn, "feedback", feedback_id, payload.model_dump(exclude_none=True), "feedback")
        return fetch_feedback(conn, feedback_id)

@router.delete("/{feedback_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_feedback(feedback_id: UUID, user: CurrentUser = Depends(get_current_user)):
    with get_db() as conn:
        row = fetch_feedback(conn, feedback_id)
        if str(row["customer_id"]) != user.id and user.role != "admin":
            raise HTTPException(status_code=403, detail="You can only delete your own feedback.")
        delete_row(conn, "feedback", feedback_id, "feedback")
