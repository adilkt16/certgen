import os
import fastapi
from fastapi.responses import FileResponse

import services.font_manager as font_manager


router = fastapi.APIRouter()


@router.get("/fonts")
async def list_fonts():
	return {"fonts": font_manager.get_font_manifest()}


@router.get("/fonts/{font_name}")
async def get_font_file(font_name: str):
	if font_name not in font_manager.get_font_list():
		raise fastapi.HTTPException(status_code=404, detail="Font not found")

	font_path = font_manager.get_font_file_path(font_name)
	if not font_path:
		raise fastapi.HTTPException(status_code=404, detail="Font not found")
	if not os.path.exists(font_path):
		try:
			font_manager.download_all_fonts()
		except Exception:
			pass

	if not os.path.exists(font_path):
		raise fastapi.HTTPException(status_code=404, detail="Font file missing")

	return FileResponse(font_path, media_type="application/x-font-ttf")


@router.get("/fonts/proxy/{font_name}")
async def get_font_proxy(request: fastapi.Request, font_name: str):
	"""Proxy endpoint that streams font files and is intended for authenticated access.

	The global API key middleware will enforce `X-API-Key` for /api/* routes. This
	route simply validates the allowlist and returns the file response.
	"""
	# Ensure font is allowlisted
	if font_name not in font_manager.get_font_list():
		raise fastapi.HTTPException(status_code=404, detail="Font not found")

	font_path = font_manager.get_font_file_path(font_name)
	if not font_path or not os.path.exists(font_path):
		try:
			font_manager.download_all_fonts()
		except Exception:
			pass

	if not font_path or not os.path.exists(font_path):
		raise fastapi.HTTPException(status_code=404, detail="Font file missing")

	# Use FileResponse to let FastAPI handle range requests and streaming
	return FileResponse(font_path, media_type="application/x-font-ttf")
