import io
import os
import re
import fastapi

from fastapi import UploadFile, Request

from PIL import Image, UnidentifiedImageError

import services.spreadsheet as spreadsheet
import services.certificate as certificate
import services.zip_builder as zip_builder
from limiter import limiter
import quota


router = fastapi.APIRouter()


@router.post("/parse-spreadsheet")
@limiter.limit("10/minute")
async def parse_spreadsheet(request: Request, spreadsheet_file: UploadFile):
	max_spreadsheet_mb = int(os.environ.get("MAX_SPREADSHEET_SIZE_MB", "5"))
	try:
		content = await spreadsheet_file.read()
		if len(content) > max_spreadsheet_mb * 1024 * 1024:
			return fastapi.responses.JSONResponse(
				status_code=400,
				content={
					"error": f"Spreadsheet must be under {max_spreadsheet_mb}MB",
					"code": "SPREADSHEET_TOO_LARGE",
				},
			)
		rows = spreadsheet.parse_spreadsheet(content, spreadsheet_file.filename)
	except ValueError as e:
		return fastapi.responses.JSONResponse(
			status_code=400,
			content={"error": str(e), "code": "PARSE_ERROR"},
		)

	columns = spreadsheet.get_column_names(rows)
	preview = rows[:5]
	return {"columns": columns, "preview": preview, "total": len(rows)}


@router.post("/generate")
@limiter.limit("10/minute")
async def generate(
	request: fastapi.Request,
	template_file: UploadFile,
	spreadsheet_file: UploadFile,
	name_column: str = fastapi.Form(...),
	x_pct: float = fastapi.Form(...),
	y_pct: float = fastapi.Form(...),
	font_name: str = fastapi.Form(...),
	font_size: int = fastapi.Form(...),
	font_color_hex: str = fastapi.Form(...),
	output_format: str = fastapi.Form(...),
	bold: str = fastapi.Form("false"),
	italic: str = fastapi.Form("false"),
	text_align: str = fastapi.Form("center"),
):
	max_template_mb = int(os.environ.get("MAX_TEMPLATE_SIZE_MB", "10"))
	# Read bytes and enforce size-bytes limit first
	template_bytes = await template_file.read()
	if len(template_bytes) > max_template_mb * 1024 * 1024:
		return fastapi.responses.JSONResponse(
			status_code=400,
			content={
				"error": f"Template must be under {max_template_mb}MB",
				"code": "TEMPLATE_TOO_LARGE",
			},
		)

	# Validate actual image content (magic-bytes) and dimensions
	try:
		with Image.open(io.BytesIO(template_bytes)) as img:
			img.verify()
		# Re-open to read dimensions (verify() may leave file in unusable state)
		with Image.open(io.BytesIO(template_bytes)) as img2:
			width, height = img2.size
	except UnidentifiedImageError:
		return fastapi.responses.JSONResponse(
			status_code=400,
			content={"error": "Uploaded file is not a valid image.", "code": "INVALID_IMAGE"},
		)
	except Exception:
		return fastapi.responses.JSONResponse(
			status_code=400,
			content={"error": "Invalid image file.", "code": "INVALID_IMAGE"},
		)

	# Enforce pixel-count cap (25 megapixels)
	if width * height > 25_000_000:
		return fastapi.responses.JSONResponse(
			status_code=400,
			content={
				"error": "Template exceeds maximum pixel dimensions",
				"code": "TEMPLATE_TOO_LARGE",
			},
		)
	max_spreadsheet_mb = int(os.environ.get("MAX_SPREADSHEET_SIZE_MB", "5"))
	try:
		sp_bytes = await spreadsheet_file.read()
		if len(sp_bytes) > max_spreadsheet_mb * 1024 * 1024:
			return fastapi.responses.JSONResponse(
				status_code=400,
				content={
					"error": f"Spreadsheet must be under {max_spreadsheet_mb}MB",
					"code": "SPREADSHEET_TOO_LARGE",
				},
			)
		rows = spreadsheet.parse_spreadsheet(sp_bytes, spreadsheet_file.filename)
	except ValueError as e:
		return fastapi.responses.JSONResponse(
			status_code=400,
			content={"error": str(e), "code": "PARSE_ERROR"},
		)

	# Validate column name exists in parsed rows
	columns = spreadsheet.get_column_names(rows)
	if name_column not in columns:
		return fastapi.responses.JSONResponse(
			status_code=400,
			content={
				"error": f"Column '{name_column}' not found in spreadsheet",
				"code": "INVALID_COLUMN",
			},
		)

	names = spreadsheet.get_names(rows, name_column)
	max_batch = int(os.environ.get("MAX_BATCH_SIZE", "77"))
	if len(names) > max_batch:
		return fastapi.responses.JSONResponse(
			status_code=400,
			content={
				"error": f"Batch limit is {max_batch}. You uploaded {len(names)} names.",
				"code": "BATCH_LIMIT_EXCEEDED",
			},
		)

	# Validate x_pct and y_pct are within 0.0-1.0 range
	try:
		x_pct = float(x_pct)
		y_pct = float(y_pct)
		if not (0.0 <= x_pct <= 1.0):
			return fastapi.responses.JSONResponse(
				status_code=400,
				content={"error": "x_pct must be between 0.0 and 1.0", "code": "INVALID_X_PCT"},
			)
		if not (0.0 <= y_pct <= 1.0):
			return fastapi.responses.JSONResponse(
				status_code=400,
				content={"error": "y_pct must be between 0.0 and 1.0", "code": "INVALID_Y_PCT"},
			)
	except (ValueError, TypeError):
		return fastapi.responses.JSONResponse(
			status_code=400,
			content={"error": "x_pct and y_pct must be valid numbers", "code": "INVALID_COORDINATES"},
		)

	# Validate font_size is within 6-500 range
	try:
		font_size = int(font_size)
		if not (6 <= font_size <= 500):
			return fastapi.responses.JSONResponse(
				status_code=400,
				content={"error": "font_size must be between 6 and 500", "code": "INVALID_FONT_SIZE"},
			)
	except (ValueError, TypeError):
		return fastapi.responses.JSONResponse(
			status_code=400,
			content={"error": "font_size must be a valid integer", "code": "INVALID_FONT_SIZE"},
		)

	# Validate font_color_hex format (must be #RRGGBB)
	if not re.match(r'^#[0-9A-Fa-f]{6}$', str(font_color_hex)):
		return fastapi.responses.JSONResponse(
			status_code=400,
			content={"error": "font_color_hex must be a valid hex color (e.g., #C9A84C)", "code": "INVALID_HEX_COLOR"},
		)

	# Validate font_name is in the allowlist
	valid_fonts = spreadsheet.get_valid_fonts()
	if font_name not in valid_fonts:
		return fastapi.responses.JSONResponse(
			status_code=400,
			content={"error": f"Unknown font: {font_name}", "code": "INVALID_FONT_NAME"},
		)

	bold_flag = str(bold).strip().lower() in ("1", "true", "yes", "on")
	italic_flag = str(italic).strip().lower() in ("1", "true", "yes", "on")
	text_align_clean = str(text_align or "center").strip().lower()
	if text_align_clean not in ("left", "center", "right"):
		text_align_clean = "center"

	certificates = []
	# Enforce per-key daily quota (if API key present)
	api_key = None
	try:
		api_key = request.headers.get("X-API-Key")
	except Exception:
		api_key = None
	num_names = len(names)
	if api_key:
		if not quota.reserve(api_key, num_names):
			return fastapi.responses.JSONResponse(
				status_code=403,
				content={"error": f"Per-key daily quota exceeded ({quota.get_usage(api_key)}/{quota.PER_KEY_CERTS_PER_DAY})", "code": "PER_KEY_QUOTA_EXCEEDED"},
			)
	try:
		for n in names:
			out = certificate.generate_certificate(
				template_bytes,
				n,
				x_pct,
				y_pct,
				font_name,
				font_size,
				font_color_hex,
				output_format,
				bold_flag,
				italic_flag,
				text_align_clean,
			)
			certificates.append({"name": n, "jpeg": out.get("jpeg"), "pdf": out.get("pdf")})
	except Exception:
		# On failure, release reserved quota
		try:
			if api_key:
				quota.release(api_key, num_names)
		except Exception:
			pass
		raise

	zip_bytes = zip_builder.build_zip(certificates, output_format)
	return fastapi.responses.StreamingResponse(
		io.BytesIO(zip_bytes),
		media_type="application/zip",
		headers={"Content-Disposition": "attachment; filename=certificates.zip"},
	)

