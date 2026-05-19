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
