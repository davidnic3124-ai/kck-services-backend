from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from kckservices.database import get_db
from kckservices.dependencies import get_optional_user, require_admin
from kckservices.schemas import CurrentUser, PromotionCreate, PromotionOut, PromotionUpdate
from kckservices.services.booking_rules import find_active_promotion
from kckservices.services.crud import delete_row, get_row, insert_row, update_row

router = APIRouter(prefix="/promotions", tags=["Promotions"])

def _normalise(data: dict) -> dict:
    if data.get("promo_code"):
        data["promo_code"] = data["promo_code"].strip().upper()
    return data

@router.get("", response_model=list[PromotionOut])
def list_promotions(include_inactive: bool = False, user: Optional[CurrentUser] = Depends(get_optional_user)):
    # Public visitors only see promotions that are active today
    show_all = include_inactive and user is not None and user.role == "admin"
    with get_db() as conn:
        with conn.cursor() as cur:
            if show_all:
                cur.execute("SELECT * FROM public.promotions ORDER BY valid_until DESC;")
            else:
                cur.execute(
                    """
                    SELECT * FROM public.promotions
                    WHERE is_active = true AND CURRENT_DATE BETWEEN valid_from AND valid_until
                    ORDER BY discount_percent DESC;
                    """
                )
            return cur.fetchall()

@router.get("/validate/{promo_code}", response_model=PromotionOut)
def validate_promo_code(promo_code: str):
    with get_db() as conn:
        promo = find_active_promotion(conn, promo_code)
    if not promo:
        raise HTTPException(status_code=404, detail="Promo code is invalid or expired.")
    return promo

@router.get("/{promotion_id}", response_model=PromotionOut)
def get_promotion(promotion_id: UUID):
    with get_db() as conn:
        return get_row(conn, "promotions", promotion_id, "promotion")

@router.post("", response_model=PromotionOut, status_code=status.HTTP_201_CREATED)
def create_promotion(payload: PromotionCreate, admin: CurrentUser = Depends(require_admin)):
    with get_db() as conn:
        return insert_row(conn, "promotions", _normalise(payload.model_dump()), "promotion")

@router.put("/{promotion_id}", response_model=PromotionOut)
def update_promotion(promotion_id: UUID, payload: PromotionUpdate, admin: CurrentUser = Depends(require_admin)):
    with get_db() as conn:
        return update_row(conn, "promotions", promotion_id, _normalise(payload.model_dump(exclude_none=True)), "promotion")

@router.delete("/{promotion_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_promotion(promotion_id: UUID, admin: CurrentUser = Depends(require_admin)):
    with get_db() as conn:
        delete_row(conn, "promotions", promotion_id, "promotion")
