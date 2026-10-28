from fastapi import APIRouter, Depends
from kckservices.database import get_db
from kckservices.dependencies import require_admin
from kckservices.schemas import CurrentUser, DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["Admin Dashboard"])

@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(admin: CurrentUser = Depends(require_admin)):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    (SELECT COUNT(*) FROM public.cars) AS total_cars,
                    (SELECT COUNT(*) FROM public.cars WHERE is_available = true) AS available_cars,
                    (SELECT COUNT(*) FROM public.profiles WHERE role = 'customer') AS total_customers,
                    (SELECT COUNT(*) FROM public.bookings) AS total_bookings,
                    (SELECT COALESCE(SUM(total_price), 0) FROM public.bookings
                        WHERE status IN ('confirmed', 'completed')) AS total_revenue,
                    (SELECT ROUND(AVG(rating)::numeric, 2) FROM public.feedback) AS average_rating,
                    (SELECT COUNT(*) FROM public.feedback WHERE is_published = true) AS published_feedback,
                    (SELECT COUNT(*) FROM public.feedback WHERE is_published = false) AS pending_feedback;
            """)
            totals = cur.fetchone()

            cur.execute("SELECT status, COUNT(*) AS n FROM public.bookings GROUP BY status;")
            by_status = {s: 0 for s in ("pending", "confirmed", "completed", "cancelled")}
            by_status.update({r["status"]: r["n"] for r in cur.fetchall()})

            cur.execute("""
                SELECT c.id AS car_id,
                       c.brand || ' ' || c.model || ' (' || c.plate_number || ')' AS car_label,
                       (SELECT COUNT(*) FROM public.bookings b
                            WHERE b.car_id = c.id AND b.status <> 'cancelled') AS bookings,
                       (SELECT ROUND(AVG(f.rating)::numeric, 1) FROM public.feedback f
                            WHERE f.car_id = c.id AND f.is_published = true) AS average_rating
                FROM public.cars c
                ORDER BY bookings DESC, average_rating DESC NULLS LAST
                LIMIT 5;
            """)
            top_cars = cur.fetchall()

    return {**totals, "bookings_by_status": by_status, "top_cars": top_cars}
