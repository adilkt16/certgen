import io
from PIL import Image, ImageDraw
import img2pdf

from .font_manager import get_font


def generate_certificate(
	template_bytes,
	name,
	x_pct,
	y_pct,
	font_name,
	font_size,
	font_color_hex,
	output_format,
):
	result = {"jpeg": None, "pdf": None}

	# Step A — Open the image
	img = Image.open(io.BytesIO(template_bytes))
	img = img.convert("RGBA")

	# Step B — Convert hex color to RGB tuple
	hex_clean = font_color_hex.lstrip("#")
	r = int(hex_clean[0:2], 16)
	g = int(hex_clean[2:4], 16)
	b = int(hex_clean[4:6], 16)
	rgb = (r, g, b)

	# Step C — Load the font
	font = get_font(font_name, font_size)

	# Step D — Auto-shrink text to fit
	draw = ImageDraw.Draw(img)
	text_width = draw.textlength(name, font=font)
	current_size = font_size
	while text_width > img.width * 0.80:
		current_size -= 2
		if current_size < 12:
			break
		font = get_font(font_name, current_size)
		try:
			text_width = draw.textlength(name, font=font)
		except Exception:
			# fallback to approximate measurement
			text_width = draw.textlength(name, font=font)

	# Step E — Calculate pixel position
	x_px = x_pct * img.width
	y_px = y_pct * img.height

	# Step F — Draw the name
	draw.text((x_px, y_px), name, font=font, fill=rgb, anchor="mm")

	# Step G — Produce JPEG output if needed
	if output_format in ("jpeg", "both"):
		rgb_img = img.convert("RGB")
		buf = io.BytesIO()
		rgb_img.save(buf, format="JPEG", quality=95)
		result["jpeg"] = buf.getvalue()

	# Step H — Produce PDF output if needed
	if output_format in ("pdf", "both"):
		rgb_img = img.convert("RGB")
		png_buf = io.BytesIO()
		rgb_img.save(png_buf, format="PNG")
		png_bytes = png_buf.getvalue()
		try:
			pdf_bytes = img2pdf.convert(png_bytes)
			result["pdf"] = pdf_bytes
		except Exception:
			result["pdf"] = None

	# Step I — Return the result dict
	return result

