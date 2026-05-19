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

	# Enforce API key requirement in production or when explicitly requested.
	# If REQUIRE_API_KEYS=true or ENV=production and no API_KEYS provided, fail-fast.
	require_keys_env = os.environ.get("REQUIRE_API_KEYS", "").lower()
	env = os.environ.get("ENV", "").lower()
	require_keys = require_keys_env in ("1", "true", "yes") or env == "production"
	if require_keys and not (os.environ.get("API_KEYS") or os.environ.get("API_KEY")):
		logger.error("API_KEYS environment variable is required in production (REQUIRE_API_KEYS or ENV=production) but is not set. Exiting.")
		raise RuntimeError("API_KEYS must be set when REQUIRE_API_KEYS=true or ENV=production")
	
	# Warn when running without API keys in non-production mode
	if not (os.environ.get("API_KEYS") or os.environ.get("API_KEY")):
		logger.warning("API_KEYS not set — running in permissive development mode.\n" \
			"Set REQUIRE_API_KEYS=true or ENV=production and configure API_KEYS in production to enforce API keys.")

	# Initialize runtime counters for monitoring
	app.state.rate_limit_count = 0
	app.state.request_count = 0
	yield


app = FastAPI(title="CertGen API", lifespan=lifespan)


# Proxy headers: only enable if operators explicitly opt in via env var.
# Default is safe (do not trust client-supplied X-Forwarded-For).
use_proxy_headers = os.environ.get("USE_PROXY_HEADERS", "").lower() in ("1", "true", "yes")
if use_proxy_headers:
	try:
		from starlette.middleware.proxy_headers import ProxyHeadersMiddleware

		app.add_middleware(ProxyHeadersMiddleware)
		logger.info("USE_PROXY_HEADERS=true: Proxy headers trusted. Ensure the fronting proxy is configured to overwrite client-supplied headers and is in the trust boundary.")
	except Exception:
		logger.exception("Failed to enable ProxyHeadersMiddleware; continuing without trusting proxy headers.")
else:
	logger.info("USE_PROXY_HEADERS not set: ignoring X-Forwarded-For by default (safe mode).")


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

# Safe CORS: do not allow credentials with wildcard origins.
# Behavior:
# - In production (ENV=production or REQUIRE_API_KEYS=true) we fail-fast if
#   credentials would be allowed with a wildcard origin to avoid insecure configs.
# - In development we disable credentials and warn instead of failing the process.
allow_credentials_env = os.environ.get("ALLOW_CREDENTIALS", "true").lower() in ("1", "true", "yes")
env_raw = os.environ.get("ENV", "").lower()
require_keys_env = os.environ.get("REQUIRE_API_KEYS", "").lower()
require_keys_flag = require_keys_env in ("1", "true", "yes") or env_raw == "production"

allow_credentials_flag = bool(allow_credentials_env)
if allowed_origins == ["*"] and allow_credentials_flag:
	if require_keys_flag:
		logger.error("Invalid CORS configuration: allow_credentials=True with wildcard ALLOWED_ORIGINS in production.")
		raise RuntimeError("ALLOWED_ORIGINS must be set to the exact frontend origin when allow_credentials is enabled in production.")
	else:
		# Non-production: disable credentials to avoid unsafe browser behaviors
		logger.warning("Disabling CORS credentials because ALLOWED_ORIGINS='*' would otherwise be insecure.")
		allow_credentials_flag = False

app.add_middleware(
	CORSMiddleware,
	allow_origins=allowed_origins,
	allow_methods=["*"],
	allow_headers=["*"],
	allow_credentials=allow_credentials_flag,
)

# Add rate limiter state to app
app.state.limiter = limiter

app.include_router(generate_routes.router, prefix="/api")
app.include_router(font_routes.router, prefix="/api")


# Global exception handler to catch rate limit errors and other exceptions
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
	"""Handle rate limit exceeded errors with user-friendly response."""
	# Increment runtime counter for monitoring
	try:
		request.app.state.rate_limit_count += 1
	except Exception:
		pass

	# Optionally include a Retry-After header to help clients back off.
	return JSONResponse(
		status_code=429,
		content={
			"error": "Too many requests. Please wait before trying again.",
			"code": "RATE_LIMIT_EXCEEDED",
		},
		headers={"Retry-After": "60"},
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


@app.get("/metrics")
async def metrics():
	"""Expose minimal runtime metrics to assist rollout monitoring."""
	return {
		"rate_limit_count": getattr(app.state, "rate_limit_count", 0),
		"request_count": getattr(app.state, "request_count", 0),
	}


if __name__ == "__main__":
	import uvicorn

	uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

