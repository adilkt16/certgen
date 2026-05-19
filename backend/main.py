from contextlib import asynccontextmanager
import os
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from limiter import limiter
from auth import verify_api_key
import services.font_manager as font_manager
from routes import generate as generate_routes
from routes import fonts as font_routes

# Configure logging for error tracking
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
	print("CertGen backend starting...")
	try:
		font_manager.download_all_fonts()
	except Exception:
		pass
	yield


app = FastAPI(title="CertGen API", lifespan=lifespan)


# Simple API key middleware (checks X-API-Key for /api/* requests)
@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
	try:
		await verify_api_key(request)
	except Exception as e:
		# verify_api_key raises HTTPException for 401; convert to JSONResponse
		from fastapi.responses import JSONResponse
		status_code = getattr(e, 'status_code', 401)
		detail = getattr(e, 'detail', {'error': 'Unauthorized', 'code': 'INVALID_API_KEY'})
		return JSONResponse(status_code=status_code, content=detail)
	return await call_next(request)

# Configure CORS from environment variable `ALLOWED_ORIGINS` (comma-separated).
# If set to '*' the old permissive behavior is preserved; otherwise provide
# a comma-separated list like 'https://example.com,http://localhost:3000'.
raw_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").strip()
if raw_origins == "*" or raw_origins == "":
	allowed_origins = ["*"]
else:
	allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

print(f"CORS allowed origins: {allowed_origins}")

app.add_middleware(
	CORSMiddleware,
	allow_origins=allowed_origins,
	allow_methods=["*"],
	allow_headers=["*"],
	allow_credentials=True,
)

# Add rate limiter state to app
app.state.limiter = limiter

app.include_router(generate_routes.router, prefix="/api")
app.include_router(font_routes.router, prefix="/api")


# Global exception handler to catch rate limit errors and other exceptions
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
	"""Handle rate limit exceeded errors with user-friendly response."""
	return JSONResponse(
		status_code=429,
		content={
			"error": "Too many requests. Please wait before trying again.",
			"code": "RATE_LIMIT_EXCEEDED",
		},
	)


# Global exception handler to prevent stack trace leakage
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
	"""Catch unhandled exceptions and return generic 500 error without leaking stack trace."""
	logger.error(f"Unhandled exception: {exc}", exc_info=True)
	return JSONResponse(
		status_code=500,
		content={
			"error": "Internal server error",
			"code": "SERVER_ERROR",
		},
	)


@app.get("/health")
async def health():
	return {"status": "ok", "service": "certgen-backend"}


if __name__ == "__main__":
	import uvicorn

	uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

