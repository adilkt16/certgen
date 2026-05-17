import io
import os
import fastapi

from fastapi import UploadFile

import services.spreadsheet as spreadsheet
import services.certificate as certificate
import services.zip_builder as zip_builder


router = fastapi.APIRouter()


@router.post("/parse-spreadsheet")
async def parse_spreadsheet(spreadsheet_file: UploadFile):
	try:
		content = await spreadsheet_file.read()
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
):
	max_template_mb = int(os.environ.get("MAX_TEMPLATE_SIZE_MB", "10"))
	# Validate template format
	tpl_name = (template_file.filename or "").lower()
	if not tpl_name.endswith((".jpg", ".jpeg", ".png")):
		return fastapi.responses.JSONResponse(
			status_code=400,
			content={
				"error": "Template must be JPEG or PNG",
				"code": "UNSUPPORTED_TEMPLATE_FORMAT",
			},
		)

	template_bytes = await template_file.read()
	if len(template_bytes) > max_template_mb * 1024 * 1024:
		return fastapi.responses.JSONResponse(
			status_code=400,
			content={
				"error": f"Template must be under {max_template_mb}MB",
				"code": "TEMPLATE_TOO_LARGE",
			},
		)
	try:
		sp_bytes = await spreadsheet_file.read()
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
		)
		certificates.append({"name": n, "jpeg": out.get("jpeg"), "pdf": out.get("pdf")})

	zip_bytes = zip_builder.build_zip(certificates, output_format)
	return fastapi.responses.StreamingResponse(
		io.BytesIO(zip_bytes),
		media_type="application/zip",
		headers={"Content-Disposition": "attachment; filename=certificates.zip"},
	)

