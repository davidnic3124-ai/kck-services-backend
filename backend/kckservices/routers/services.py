from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from kckservices.database import get_db
from kckservices.dependencies import get_optional_user, require_admin
from kckservices.schemas import CurrentUser, ServiceCreate, ServiceOut, ServiceUpdate
from kckservices.services.crud import delete_row, get_row, insert_row, update_row

router = APIRouter(prefix="/services", tags=["Rental Services"])

@router.get("", response_model=list[ServiceOut])
def list_services(include_unpublished: bool = False, user: Optional[CurrentUser] = Depends(get_optional_user)):
    # Drafts are only shown to admins
    show_all = include_unpublished and user is not None and user.role == "admin"
    with get_db() as conn:
        with conn.cursor() as cur:
            if show_all:
                cur.execute("SELECT * FROM public.rental_services ORDER BY price ASC;")
            else:
                cur.execute("SELECT * FROM public.rental_services WHERE is_published = true ORDER BY price ASC;")
            return cur.fetchall()

@router.get("/{service_id}", response_model=ServiceOut)
def get_service(service_id: UUID, user: Optional[CurrentUser] = Depends(get_optional_user)):
    with get_db() as conn:
        row = get_row(conn, "rental_services", service_id, "rental service")
    if not row["is_published"] and not (user and user.role == "admin"):
        raise HTTPException(status_code=404, detail="Rental service not found.")
    return row

@router.post("", response_model=ServiceOut, status_code=status.HTTP_201_CREATED)
def create_service(payload: ServiceCreate, admin: CurrentUser = Depends(require_admin)):
    with get_db() as conn:
        return insert_row(conn, "rental_services", payload.model_dump(), "rental service")

@router.put("/{service_id}", response_model=ServiceOut)
def update_service(service_id: UUID, payload: ServiceUpdate, admin: CurrentUser = Depends(require_admin)):
    with get_db() as conn:
        return update_row(conn, "rental_services", service_id, payload.model_dump(exclude_none=True), "rental service")

@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(service_id: UUID, admin: CurrentUser = Depends(require_admin)):
    with get_db() as conn:
        delete_row(conn, "rental_services", service_id, "rental service")
