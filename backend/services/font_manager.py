import os
import urllib.request
import PIL.ImageFont

FONT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fonts"))

SUPPORTED_FONTS = {
	"playfair_display": {
		"url": "https://github.com/google/fonts/raw/main/ofl/playfairdisplay/static/PlayfairDisplay-Regular.ttf",
		"label": "Playfair Display",
		"weight": 400,
		"style": "normal",
		"file": "playfair-display.regular.ttf",
	},
	"lato_bold": {
		"url": "https://github.com/google/fonts/raw/main/ofl/lato/Lato-Bold.ttf",
		"label": "Lato Bold",
		"weight": 700,
		"style": "normal",
	},
	"lato_regular": {
		"url": "https://github.com/google/fonts/raw/main/ofl/lato/Lato-Regular.ttf",
		"label": "Lato Regular",
		"weight": 400,
		"style": "normal",
	},
	"archivo_black": {
		"url": "https://github.com/google/fonts/raw/main/ofl/archivoblack/ArchivoBlack-Regular.ttf",
		"label": "Archivo Black",
		"weight": 400,
		"style": "normal",
	},
	"oswald": {
		"url": "https://github.com/google/fonts/raw/main/ofl/oswald/Oswald-Regular.ttf",
		"label": "Oswald",
		"weight": 400,
		"style": "normal",
	},
	"bungee": {
		"url": "https://github.com/google/fonts/raw/main/ofl/bungee/Bungee-Regular.ttf",
		"label": "Bungee",
		"weight": 400,
		"style": "normal",
	},
	"playwrite_england_joined_guides": {
		"url": None,
		"label": "Playwrite England Joined Guides",
		"weight": 400,
		"style": "normal",
		"file": "PlaywriteGBJGuides-Regular.ttf",
	},
	"playwrite_england_joined_guides_italic": {
		"url": None,
		"label": "Playwrite England Joined Guides Italic",
		"weight": 400,
		"style": "italic",
		"file": "PlaywriteGBJGuides-Italic.ttf",
	},
}


def download_all_fonts():
	fonts_dir = FONT_DIR
	os.makedirs(fonts_dir, exist_ok=True)
	for key, meta in SUPPORTED_FONTS.items():
		url = meta.get("url")
		filename = meta.get("file", f"{key}.ttf")
		dest = os.path.join(fonts_dir, filename)
		if os.path.exists(dest):
			print(f"Ready: {key}")
			continue
		try:
			if url:
				urllib.request.urlretrieve(url, dest)
			if os.path.exists(dest):
				print(f"Ready: {key}")
			else:
				print(f"Failed: {key}")
		except Exception:
			print(f"Failed: {key}")
			continue


def get_font_file_path(font_name):
	meta = SUPPORTED_FONTS.get(font_name)
	if not meta:
		return None
	filename = meta.get("file", f"{font_name}.ttf")
	return os.path.join(FONT_DIR, filename)


def get_font(font_name, size):
	path = get_font_file_path(font_name)
	if os.path.exists(path):
		try:
			return PIL.ImageFont.truetype(path, size)
		except Exception:
			pass

	# Keep size behavior predictable even when downloaded font files are missing.
	try:
		return PIL.ImageFont.truetype("DejaVuSans.ttf", size)
	except Exception:
		return PIL.ImageFont.load_default()


def get_font_list():
	return list(SUPPORTED_FONTS.keys())


def get_font_manifest():
	fonts = []
	for key, meta in SUPPORTED_FONTS.items():
		path = get_font_file_path(key)
		if not os.path.exists(path) and not meta.get("url"):
			continue
		fonts.append(
			{
				"id": key,
				"label": meta.get("label", key),
				"weight": meta.get("weight", 400),
				"style": meta.get("style", "normal"),
			}
		)
	return fonts


def get_fonts_dir():
	return FONT_DIR

