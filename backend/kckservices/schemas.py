from datetime import date, datetime
from typing import Literal, Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, model_validator

Category = Literal["sedan", "hatchback", "suv", "mpv", "pickup", "van", "luxury"]
Transmission = Literal["auto", "manual"]
FuelType = Literal["petrol", "diesel", "hybrid", "electric"]
PriceUnit = Literal["per_hour", "per_day", "per_trip", "per_month"]
BookingStatus = Literal["pending", "confirmed", "completed", "cancelled"]
Role = Literal["customer", "admin"]

# ---------------------------------------------------------------- Auth / Profile
class CurrentUser(BaseModel):
    id: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Role = "customer"

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=72)
    full_name: str = Field(..., min_length=2, max_length=120, examples=["Ahmad bin Ali"])
    phone: Optional[str] = Field(None, max_length=30, examples=["012-3456789"])

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    message: str
    user_id: Optional[str] = None
    email: Optional[str] = None
    access_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: Optional[int] = None

class ProfileOut(BaseModel):
    id: UUID
    email: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: Role
    created_at: datetime

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=120)
    phone: Optional[str] = Field(None, max_length=30)

class RoleUpdate(BaseModel):
    role: Role

# ---------------------------------------------------------------- Cars
class CarBase(BaseModel):
    plate_number: str = Field(..., min_length=2, max_length=15, examples=["KCK 1234"])
    brand: str = Field(..., min_length=1, max_length=60, examples=["Perodua"])
    model: str = Field(..., min_length=1, max_length=60, examples=["Myvi"])
    year: int = Field(..., ge=1990, le=2100, examples=[2024])
    category: Category
    transmission: Transmission = "auto"
    seats: int = Field(5, ge=2, le=15)
    fuel_type: FuelType = "petrol"
    daily_rate: float = Field(..., gt=0, examples=[120.0])
    description: Optional[str] = Field(None, max_length=2000)
    is_available: bool = True

class CarCreate(CarBase):
    pass

class CarUpdate(BaseModel):
    plate_number: Optional[str] = Field(None, min_length=2, max_length=15)
    brand: Optional[str] = Field(None, min_length=1, max_length=60)
    model: Optional[str] = Field(None, min_length=1, max_length=60)
    year: Optional[int] = Field(None, ge=1990, le=2100)
    category: Optional[Category] = None
    transmission: Optional[Transmission] = None
    seats: Optional[int] = Field(None, ge=2, le=15)
    fuel_type: Optional[FuelType] = None
    daily_rate: Optional[float] = Field(None, gt=0)
    description: Optional[str] = Field(None, max_length=2000)
    is_available: Optional[bool] = None

class CarOut(CarBase):
    id: UUID
    image_url: Optional[str] = None
    average_rating: Optional[float] = None
    review_count: int = 0
    created_at: datetime
    updated_at: datetime

# ---------------------------------------------------------------- Rental services
class ServiceBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=120, examples=["Chauffeur Service"])
    description: Optional[str] = Field(None, max_length=2000)
    price: float = Field(0, ge=0, examples=[150.0])
    price_unit: PriceUnit = "per_trip"
    is_published: bool = True

class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=120)
    description: Optional[str] = Field(None, max_length=2000)
    price: Optional[float] = Field(None, ge=0)
    price_unit: Optional[PriceUnit] = None
    is_published: Optional[bool] = None

class ServiceOut(ServiceBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

# ---------------------------------------------------------------- Promotions
class PromotionBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=120, examples=["Merdeka Sale"])
    description: Optional[str] = Field(None, max_length=2000)
    discount_percent: int = Field(..., ge=0, le=100, examples=[20])
    promo_code: Optional[str] = Field(None, max_length=30, examples=["MERDEKA20"])
    valid_from: date
    valid_until: date
    is_active: bool = True

    @model_validator(mode="after")
    def check_dates(self):
        if self.valid_until < self.valid_from:
            raise ValueError("valid_until must be on or after valid_from")
        return self

class PromotionCreate(PromotionBase):
    pass

class PromotionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=120)
    description: Optional[str] = Field(None, max_length=2000)
    discount_percent: Optional[int] = Field(None, ge=0, le=100)
    promo_code: Optional[str] = Field(None, max_length=30)
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    is_active: Optional[bool] = None

class PromotionOut(PromotionBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

# ---------------------------------------------------------------- Bookings
class BookingCreate(BaseModel):
    car_id: UUID
    service_id: Optional[UUID] = None
    start_date: date
    end_date: date
    pickup_location: str = Field(..., min_length=2, max_length=200, examples=["KCK HQ, Kuala Lumpur"])
    notes: Optional[str] = Field(None, max_length=1000)
    promo_code: Optional[str] = Field(None, max_length=30, examples=["WELCOME10"])

    @model_validator(mode="after")
    def check_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self

class BookingQuote(BaseModel):
    rental_days: int
    car_cost: float
    service_cost: float
    subtotal: float
    discount_percent: int
    discount_amount: float
    total_price: float

class BookingStatusUpdate(BaseModel):
    status: BookingStatus

class BookingOut(BaseModel):
    id: UUID
    customer_id: UUID
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    car_id: UUID
    car_label: Optional[str] = None
    service_id: Optional[UUID] = None
    service_title: Optional[str] = None
    promo_code: Optional[str] = None
    start_date: date
    end_date: date
    rental_days: int
    pickup_location: str
    notes: Optional[str] = None
    subtotal: float
    discount_amount: float
    total_price: float
    status: BookingStatus
    created_at: datetime
    updated_at: datetime

# ---------------------------------------------------------------- Feedback
class FeedbackCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5, examples=[5])
    title: Optional[str] = Field(None, max_length=120, examples=["Great service!"])
    comment: str = Field(..., min_length=3, max_length=2000, examples=["Car was clean and pickup was on time."])
    car_id: Optional[UUID] = None
    booking_id: Optional[UUID] = None

class FeedbackUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    title: Optional[str] = Field(None, max_length=120)
    comment: Optional[str] = Field(None, min_length=3, max_length=2000)

class FeedbackModerate(BaseModel):
    is_published: Optional[bool] = None
    admin_reply: Optional[str] = Field(None, max_length=2000)

class FeedbackOut(BaseModel):
    id: UUID
    customer_id: UUID
    customer_name: Optional[str] = None
    car_id: Optional[UUID] = None
    car_label: Optional[str] = None
    booking_id: Optional[UUID] = None
    rating: int
    title: Optional[str] = None
    comment: str
    is_published: bool
    admin_reply: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# ---------------------------------------------------------------- Dashboard
class TopCar(BaseModel):
    car_id: UUID
    car_label: str
    bookings: int
    average_rating: Optional[float] = None

class DashboardSummary(BaseModel):
    total_cars: int
    available_cars: int
    total_customers: int
    total_bookings: int
    bookings_by_status: dict[str, int]
    total_revenue: float
    average_rating: Optional[float] = None
    published_feedback: int
    pending_feedback: int
    top_cars: list[TopCar]
