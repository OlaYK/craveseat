from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
import sys
import os

# Add parent directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your routes
from authentication import auth as auth_routes
from user_profile import routes as profile_routes
from vendor_profile import routes as vendor_routes
from cravings import routes as cravings_routes
from responses import routes as responses_routes
from notifications import routes as notifications_routes
from public import routes as public_routes

# Create FastAPI app
app = FastAPI(
    title="CraveSeat API",
    description="A platform for posting food cravings and connecting with vendors",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://your-frontend-domain.vercel.app",
        "*"  # Update this in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
        "message": "Welcome to CraveSeat API on Vercel",
        "docs": "/docs",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "platform": "vercel"}

# Mangum handler for Vercel serverless
handler = Mangum(app)