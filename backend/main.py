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

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_methods=["*"],
	allow_headers=["*"],
)

app.include_router(generate_routes.router, prefix="/api")
app.include_router(font_routes.router, prefix="/api")


@app.get("/health")
async def health():
	return {"status": "ok", "service": "certgen-backend"}


if __name__ == "__main__":
	import uvicorn

	uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

