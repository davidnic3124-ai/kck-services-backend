from datetime import date
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from kckservices.database import get_db
from kckservices.dependencies import get_current_user, require_admin
from kckservices.schemas import (
    BookingCreate, BookingOut, BookingQuote, BookingStatus, BookingStatusUpdate, CurrentUser
)
from kckservices.services.booking_rules import car_is_free, find_active_promotion
from kckservices.services.crud import delete_row, get_row
from kckservices.services.pricing import calculate_quote, count_rental_days

router = APIRouter(prefix="/bookings", tags=["Bookings"])

BOOKING_SELECT = """
    SELECT b.*,
           p.full_name AS customer_name,
           p.email AS customer_email,
           c.brand || ' ' || c.model || ' (' || c.plate_number || ')' AS car_label,
           s.title AS service_title,
           pr.promo_code
    FROM public.bookings b
    JOIN public.profiles p ON p.id = b.customer_id
    JOIN public.cars c ON c.id = b.car_id
    LEFT JOIN public.rental_services s ON s.id = b.service_id
    LEFT JOIN public.promotions pr ON pr.id = b.promotion_id
"""

def fetch_booking(conn, booking_id) -> dict:
    with conn.cursor() as cur:
        cur.execute(f"{BOOKING_SELECT} WHERE b.id = %s;", (str(booking_id),))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Booking not found.")
    return row

def build_quote(conn, payload: BookingCreate) -> tuple[dict, Optional[str]]:
    car = get_row(conn, "cars", payload.car_id, "car")
    if not car["is_available"]:
        raise HTTPException(status_code=400, detail="This car is currently not available for rent.")

    svc_price, svc_unit = 0.0, None
    if payload.service_id:
        svc = get_row(conn, "rental_services", payload.service_id, "rental service")
        if not svc["is_published"]:
            raise HTTPException(status_code=400, detail="This rental service is not offered at the moment.")
        svc_price, svc_unit = float(svc["price"]), svc["price_unit"]

    discount, promotion_id = 0, None
    if payload.promo_code:
        promo = find_active_promotion(conn, payload.promo_code)
        if not promo:
            raise HTTPException(status_code=400, detail="Promo code is invalid or expired.")
        discount, promotion_id = promo["discount_percent"], str(promo["id"])

    days = count_rental_days(payload.start_date, payload.end_date)
    return calculate_quote(float(car["daily_rate"]), days, svc_price, svc_unit, discount), promotion_id

@router.post("/quote", response_model=BookingQuote)
def get_price_quote(payload: BookingCreate):
    with get_db() as conn:
        quote, _ = build_quote(conn, payload)
        return quote

@router.post("", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def create_booking(payload: BookingCreate, user: CurrentUser = Depends(get_current_user)):
    if payload.start_date < date.today():
        raise HTTPException(status_code=400, detail="Start date cannot be in the past.")

    with get_db() as conn:
        with conn.cursor() as cur:
            # Lock the car row so two customers cannot book the same dates at the same time
            cur.execute("SELECT id FROM public.cars WHERE id = %s FOR UPDATE;", (str(payload.car_id),))
        quote, promotion_id = build_quote(conn, payload)
        if not car_is_free(conn, payload.car_id, payload.start_date, payload.end_date):
            raise HTTPException(status_code=409, detail="Sorry, this car is already booked for those dates.")

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.bookings
                (customer_id, car_id, service_id, promotion_id, start_date, end_date, rental_days,
                 pickup_location, notes, subtotal, discount_amount, total_price, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending')
                RETURNING id;
                """,
                (
                    user.id, str(payload.car_id), str(payload.service_id) if payload.service_id else None,
                    promotion_id, payload.start_date, payload.end_date, quote["rental_days"],
                    payload.pickup_location, payload.notes, quote["subtotal"], quote["discount_amount"],
                    quote["total_price"],
                )
            )
            booking_id = cur.fetchone()["id"]
        conn.commit()
        return fetch_booking(conn, booking_id)

@router.get("/me", response_model=list[BookingOut])
def list_my_bookings(user: CurrentUser = Depends(get_current_user)):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(f"{BOOKING_SELECT} WHERE b.customer_id = %s ORDER BY b.start_date DESC;", (user.id,))
            return cur.fetchall()

@router.get("", response_model=list[BookingOut])
def list_all_bookings(booking_status: Optional[BookingStatus] = None, admin: CurrentUser = Depends(require_admin)):
    with get_db() as conn:
        with conn.cursor() as cur:
            if booking_status:
                cur.execute(f"{BOOKING_SELECT} WHERE b.status = %s ORDER BY b.created_at DESC;", (booking_status,))
            else:
                cur.execute(f"{BOOKING_SELECT} ORDER BY b.created_at DESC;")
            return cur.fetchall()

@router.get("/{booking_id}", response_model=BookingOut)
def get_booking(booking_id: UUID, user: CurrentUser = Depends(get_current_user)):
    with get_db() as conn:
        booking = fetch_booking(conn, booking_id)
    if str(booking["customer_id"]) != user.id and user.role != "admin":
        raise HTTPException(status_code=404, detail="Booking not found.")
    return booking

@router.patch("/{booking_id}/cancel", response_model=BookingOut)
def cancel_my_booking(booking_id: UUID, user: CurrentUser = Depends(get_current_user)):
    with get_db() as conn:
        booking = fetch_booking(conn, booking_id)
        if str(booking["customer_id"]) != user.id:
            raise HTTPException(status_code=404, detail="Booking not found.")
        if booking["status"] not in ("pending", "confirmed"):
            raise HTTPException(status_code=400, detail=f"A {booking['status']} booking cannot be cancelled.")
        with conn.cursor() as cur:
            cur.execute("UPDATE public.bookings SET status = 'cancelled' WHERE id = %s;", (str(booking_id),))
        conn.commit()
        return fetch_booking(conn, booking_id)

@router.put("/{booking_id}/status", response_model=BookingOut)
def update_booking_status(booking_id: UUID, payload: BookingStatusUpdate, admin: CurrentUser = Depends(require_admin)):
    with get_db() as conn:
        booking = fetch_booking(conn, booking_id)
        # Re-activating a cancelled booking must not double-book the car
        if payload.status in ("pending", "confirmed") and booking["status"] in ("cancelled", "completed"):
            if not car_is_free(conn, booking["car_id"], booking["start_date"], booking["end_date"], str(booking_id)):
                raise HTTPException(status_code=409, detail="The car is already booked by someone else for those dates.")
        with conn.cursor() as cur:
            cur.execute("UPDATE public.bookings SET status = %s WHERE id = %s;", (payload.status, str(booking_id)))
        conn.commit()
        return fetch_booking(conn, booking_id)

@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(booking_id: UUID, admin: CurrentUser = Depends(require_admin)):
    with get_db() as conn:
        delete_row(conn, "bookings", booking_id, "booking")
