from fastapi import FastAPI
from authentication import auth as auth_routes
from user_profile import routes as profile_routes
from vendor_profile import routes as vendor_routes
from cravings import routes as cravings_routes
from responses import routes as responses_routes
from notifications import routes as notifications_routes
from public import routes as public_routes
from database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CraveSeat App",
    description="A platform for posting food cravings and connecting with vendors",
    version="1.0.0"
)

# Include all routers
app.include_router(auth_routes.router, prefix="/auth", tags=["Authentication"])
app.include_router(profile_routes.router, prefix="/profile", tags=["User Profile"])
app.include_router(vendor_routes.router, prefix="/vendor", tags=["Vendor Profile"])
app.include_router(cravings_routes.router, prefix="/cravings", tags=["Cravings"])
app.include_router(responses_routes.router, prefix="/responses", tags=["Responses"])
app.include_router(notifications_routes.router, prefix="/notifications", tags=["Notifications"])
app.include_router(public_routes.router, prefix="/public", tags=["Public Access"])


@app.get("/")
def root():
    return {
        "message": "Welcome to CraveSeat API",
        "docs": "/docs",
        "version": "1.0.0"
    }