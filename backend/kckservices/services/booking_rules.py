from datetime import date
from typing import Optional

def car_is_free(conn, car_id: str, start_date: date, end_date: date, exclude_booking_id: Optional[str] = None) -> bool:
    # A car is taken if any pending/confirmed booking overlaps the requested dates
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1 FROM public.bookings
            WHERE car_id = %s
              AND status IN ('pending', 'confirmed')
              AND start_date <= %s
              AND end_date >= %s
              AND (%s::uuid IS NULL OR id <> %s::uuid)
            LIMIT 1;
            """,
            (str(car_id), end_date, start_date, exclude_booking_id, exclude_booking_id)
        )
        return cur.fetchone() is None

def find_active_promotion(conn, promo_code: str) -> Optional[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT * FROM public.promotions
            WHERE UPPER(promo_code) = UPPER(%s)
              AND is_active = true
              AND CURRENT_DATE BETWEEN valid_from AND valid_until;
            """,
            (promo_code.strip(),)
        )
        return cur.fetchone()
