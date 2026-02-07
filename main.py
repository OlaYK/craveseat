from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
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

# --- Exception Handlers ---

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "data": None
        },
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Format the validation error message
    errors = exc.errors()
    if errors:
        # Try to create a readable error message from the first error
        error = errors[0]
        msg = f"Validation error: {error.get('msg')} at {'.'.join(str(loc) for loc in error.get('loc'))}"
    else:
        msg = "Validation error"
        
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": msg,
            "data": errors # Include full errors in data for debugging/frontend help
        },
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "An unexpected error occurred. Please try again later.",
            "data": str(exc) if app.debug else None
        },
    )

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://your-frontend-domain.com",
        "*"  # Remove this in production, specify your frontend domain
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
        "success": True,
        "message": "Welcome to CraveSeat API",
        "data": {
            "docs": "/docs",
            "version": "1.0.0",
            "status": "running"
        }
    }

@app.get("/health")
def health_check():
    return {
        "success": True,
        "message": "System is healthy",
        "data": {
            "status": "healthy",
            "platform": "render"
        }
    }