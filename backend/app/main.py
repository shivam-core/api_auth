from fastapi import FastAPI, Depends, Request, Response
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from app.database import get_db
from app.routers import auth, notes, sessions, audit

app = FastAPI(docs_url="/docs", redoc_url="/redoc")

# Custom validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        # Mask sensitive inputs
        loc = err.get("loc", [])
        field = loc[-1] if loc else "unknown"
        errors.append(f"Invalid input for {field}")
    return JSONResponse(
        status_code=422,
        content={"error": {"message": "Validation failed", "details": errors}},
        headers={"Cache-Control": "no-store"}
    )

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    # Basic security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response

@app.get("/api/health/live")
def health_live():
    return Response(status_code=200)

@app.get("/api/health/ready")
def health_ready(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        return Response(status_code=200)
    except Exception:
        return Response(status_code=503)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(notes.router, prefix="/api/notes", tags=["notes"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(audit.router, prefix="/api/audit", tags=["audit"])

# Static hosting for frontend
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

frontend_dist = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if full_path.startswith("api/"):
            return JSONResponse(status_code=404, content={"error": "Not found"})
        return FileResponse(os.path.join(frontend_dist, "index.html"))
