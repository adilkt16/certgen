import io
import os
import fastapi

from fastapi import UploadFile

from PIL import Image, UnidentifiedImageError

import services.spreadsheet as spreadsheet
import services.certificate as certificate
import services.zip_builder as zip_builder


router = fastapi.APIRouter()


@router.post("/parse-spreadsheet")
async def parse_spreadsheet(spreadsheet_file: UploadFile):
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
async def generate(
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

	names = spreadsheet.get_names(rows, name_column)
	max_batch = int(os.environ.get("MAX_BATCH_SIZE", "200"))
	if len(names) > max_batch:
		return fastapi.responses.JSONResponse(
			status_code=400,
			content={
				"error": f"Batch limit is {max_batch}. You uploaded {len(names)} names.",
				"code": "BATCH_LIMIT_EXCEEDED",
			},
		)

	bold_flag = str(bold).strip().lower() in ("1", "true", "yes", "on")
	italic_flag = str(italic).strip().lower() in ("1", "true", "yes", "on")
	text_align_clean = str(text_align or "center").strip().lower()
	if text_align_clean not in ("left", "center", "right"):
		text_align_clean = "center"

	certificates = []
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

	zip_bytes = zip_builder.build_zip(certificates, output_format)
	return fastapi.responses.StreamingResponse(
		io.BytesIO(zip_bytes),
		media_type="application/zip",
		headers={"Content-Disposition": "attachment; filename=certificates.zip"},
	)

