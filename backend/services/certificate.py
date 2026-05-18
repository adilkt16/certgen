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
	bold=False,
	italic=False,
	text_align="center",
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
	try:
		text_width = draw.textlength(name, font=font)
	except Exception:
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
	align = (text_align or "center").lower()
	if align not in ("left", "center", "right"):
		align = "center"

	try:
		bbox = draw.textbbox((0, 0), name, font=font, anchor="lt")
	except Exception:
		bbox = (0, 0, 1, 1)
	text_w = max(1, int(bbox[2] - bbox[0]))
	text_h = max(1, int(bbox[3] - bbox[1]))

	italic_shear = 0.2 if italic else 0.0
	extra_w = int(abs(italic_shear) * text_h) if italic else 0
	text_img = Image.new("RGBA", (text_w + extra_w, text_h), (0, 0, 0, 0))
	text_draw = ImageDraw.Draw(text_img)
	stroke_width = max(1, int(round(current_size / 24))) if bold else 0
	text_draw.text(
		(-bbox[0], -bbox[1]),
		name,
		font=font,
		fill=rgb,
		anchor="lt",
		stroke_width=stroke_width,
		stroke_fill=rgb,
	)

	if italic:
		text_img = text_img.transform(
			(text_img.width, text_img.height),
			Image.AFFINE,
			(1, italic_shear, 0, 0, 1, 0),
			resample=Image.BICUBIC,
		)

	if align == "left":
		draw_x = x_px
	elif align == "right":
		draw_x = x_px - text_width
	else:
		draw_x = x_px - (text_width / 2)

	draw_y = y_px - (text_img.height / 2)
	img.paste(text_img, (int(draw_x), int(draw_y)), text_img)

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

