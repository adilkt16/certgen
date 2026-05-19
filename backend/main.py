from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import services.font_manager as font_manager
from routes import generate as generate_routes
from routes import fonts as font_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
	print("CertGen backend starting...")
	try:
		font_manager.download_all_fonts()
	except Exception:
		pass
	yield


app = FastAPI(title="CertGen API", lifespan=lifespan)

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

app.include_router(generate_routes.router, prefix="/api")
app.include_router(font_routes.router, prefix="/api")


@app.get("/health")
async def health():
	return {"status": "ok", "service": "certgen-backend"}


if __name__ == "__main__":
	import uvicorn

	uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

