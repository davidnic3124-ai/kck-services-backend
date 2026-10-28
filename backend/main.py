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

# Clean and prepare origins from settings
origins = [origin.strip().rstrip("/") for origin in settings.allowed_origins if origin.strip()]

# Ensure frontend origins are explicitly allowed
default_origins = [
    "https://kck-services-frontend.davidnic3124.workers.dev",
    "http://localhost:5173",
    "http://localhost:3000",
]
for origin in default_origins:
    if origin not in origins:
        origins.append(origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows OPTIONS, GET, POST, PUT, DELETE, PATCH, etc.
    allow_headers=["*"],  # Allows all incoming headers during preflight
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
