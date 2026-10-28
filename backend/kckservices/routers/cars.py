from datetime import date
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from kckservices.database import get_db
from kckservices.dependencies import require_admin
from kckservices.schemas import Category, CarCreate, CarOut, CarUpdate, CurrentUser, Transmission
from kckservices.services.booking_rules import car_is_free
from kckservices.services.crud import delete_row, get_row, insert_row, update_row
from kckservices.services.storage import upload_car_image

router = APIRouter(prefix="/cars", tags=["Cars"])

# Every car comes back with its average rating from published customer feedback
CAR_SELECT = """
    SELECT c.*,
           ROUND(AVG(f.rating)::numeric, 1) AS average_rating,
           COUNT(f.id) AS review_count
    FROM public.cars c
    LEFT JOIN public.feedback f ON f.car_id = c.id AND f.is_published = true
"""

def fetch_car(conn, car_id) -> dict:
    get_row(conn, "cars", car_id, "car")  # 404 if missing
    with conn.cursor() as cur:
        cur.execute(f"{CAR_SELECT} WHERE c.id = %s GROUP BY c.id;", (str(car_id),))
        return cur.fetchone()

@router.get("", response_model=list[CarOut])
def list_cars(
    category: Optional[Category] = None,
    transmission: Optional[Transmission] = None,
    available_only: bool = False,
    min_rate: Optional[float] = Query(None, ge=0),
    max_rate: Optional[float] = Query(None, ge=0),
    min_seats: Optional[int] = Query(None, ge=2, le=15),
    search: Optional[str] = Query(None, max_length=60, description="Brand, model or plate number"),
):
    conditions, params = [], []
    if category:
        conditions.append("c.category = %s")
        params.append(category)
    if transmission:
        conditions.append("c.transmission = %s")
        params.append(transmission)
    if available_only:
        conditions.append("c.is_available = true")
    if min_rate is not None:
        conditions.append("c.daily_rate >= %s")
        params.append(min_rate)
    if max_rate is not None:
        conditions.append("c.daily_rate <= %s")
        params.append(max_rate)
    if min_seats is not None:
        conditions.append("c.seats >= %s")
        params.append(min_seats)
    if search:
        conditions.append("(c.brand ILIKE %s OR c.model ILIKE %s OR c.plate_number ILIKE %s)")
        params += [f"%{search}%"] * 3

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(f"{CAR_SELECT} {where} GROUP BY c.id ORDER BY c.daily_rate ASC;", params)
            return cur.fetchall()

@router.get("/{car_id}", response_model=CarOut)
def get_car(car_id: UUID):
    with get_db() as conn:
        return fetch_car(conn, car_id)

@router.get("/{car_id}/availability")
def check_availability(car_id: UUID, start_date: date, end_date: date):
    with get_db() as conn:
        car = get_row(conn, "cars", car_id, "car")
        free = car["is_available"] and end_date >= start_date and car_is_free(conn, car_id, start_date, end_date)
    return {"car_id": str(car_id), "start_date": start_date, "end_date": end_date, "available": free}

@router.post("", response_model=CarOut, status_code=status.HTTP_201_CREATED)
def create_car(payload: CarCreate, admin: CurrentUser = Depends(require_admin)):
    with get_db() as conn:
        row = insert_row(conn, "cars", payload.model_dump(), "car")
        return fetch_car(conn, row["id"])

@router.put("/{car_id}", response_model=CarOut)
def update_car(car_id: UUID, payload: CarUpdate, admin: CurrentUser = Depends(require_admin)):
    with get_db() as conn:
        update_row(conn, "cars", car_id, payload.model_dump(exclude_none=True), "car")
        return fetch_car(conn, car_id)

@router.delete("/{car_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_car(car_id: UUID, admin: CurrentUser = Depends(require_admin)):
    with get_db() as conn:
        delete_row(conn, "cars", car_id, "car")

@router.post("/{car_id}/image", response_model=CarOut)
async def upload_image(car_id: UUID, image: UploadFile = File(...), admin: CurrentUser = Depends(require_admin)):
    with get_db() as conn:
        get_row(conn, "cars", car_id, "car")
    image_url = await upload_car_image(image, str(car_id))
    with get_db() as conn:
        update_row(conn, "cars", car_id, {"image_url": image_url}, "car")
        return fetch_car(conn, car_id)
