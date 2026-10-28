from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from kckservices.config import settings
from kckservices.database import pool
from kckservices.routers import health, auth, cars, services, promotions, bookings, feedback, dashboard

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    pool.close()  # release database connections cleanly on shutdown

tags_metadata = [
    {"name": "Health", "description": "Is the API alive?"},
    {"name": "Auth & Profile", "description": "Register, log in and manage your profile. `POST /auth/token` is what the **Authorize** button uses."},
    {"name": "Cars", "description": "The KCK rental fleet. Anyone can browse; admins create, update, delete and upload photos."},
    {"name": "Rental Services", "description": "Service packages KCK publishes (chauffeur, airport transfer, wedding car...)."},
    {"name": "Promotions", "description": "Discount campaigns and promo codes."},
    {"name": "Bookings", "description": "Customers book cars; admins confirm, complete or cancel them."},
    {"name": "Customer Feedback", "description": "Customer reviews. New reviews wait for admin approval before they are published."},
    {"name": "Admin Dashboard", "description": "Business summary for KCK management."},
]

app = FastAPI(
    title="KCK SERVICES - Car Rental API",
    description=(
        "Backend for **KCK SERVICES COMPANY**: publish rental cars, service packages and promotions, "
        "take customer bookings and collect customer feedback.\n\n"
        "**How to test protected endpoints (🔒):** click **Authorize** (top right), type your email in "
        "*username* and your password, click **Authorize**, then **Close**. Every request now carries your "
        "login token. Click **Authorize → Logout** to switch accounts.\n\n"
        "Public endpoints (no padlock) work without logging in."
    ),
    version="1.0.0",
    openapi_tags=tags_metadata,
    swagger_ui_parameters={"persistAuthorization": True},
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(cars.router)
app.include_router(services.router)
app.include_router(promotions.router)
app.include_router(bookings.router)
app.include_router(feedback.router)
app.include_router(dashboard.router)
