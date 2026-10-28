from fastapi import APIRouter

router = APIRouter(tags=["Health"])

@router.get("/health")
def health_check():
    return {"ok": True, "service": "KCK SERVICES - Car Rental API"}
