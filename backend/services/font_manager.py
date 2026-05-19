import os
import urllib.request
from urllib.parse import urlparse
import shutil
import tempfile
import PIL.ImageFont

# Fonts directory (resolved to an absolute canonical path)
FONT_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "fonts"))

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
		"file": "oswald.regular.ttf",
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

	# Allowed hostnames for font downloads to avoid redirect-to-arbitrary-host attacks
	ALLOWED_HOSTS = {"raw.githubusercontent.com", "github.com", "githubusercontent.com", "fonts.gstatic.com", "fonts.googleapis.com"}

	for key, meta in SUPPORTED_FONTS.items():
		url = meta.get("url")
		filename = meta.get("file", f"{key}.ttf")
		# Ensure destination path is inside FONT_DIR
		dest = os.path.join(fonts_dir, filename)
		dest_real = os.path.realpath(dest)
		if not dest_real.startswith(FONT_DIR + os.sep):
			print(f"Skipped (unsafe filename): {key}")
			continue

		if os.path.exists(dest_real):
			print(f"Ready: {key}")
			continue
		try:
			if url:
				p = urlparse(url)
				if not p.scheme or p.scheme not in ("http", "https"):
					raise ValueError("Unsupported URL scheme")
				# allow only known hostnames
				host = p.netloc.lower()
				if not any(h in host for h in ALLOWED_HOSTS):
					raise ValueError("Host not allowed")
				# Stream download with size cap (10 MB) and write to a temp file first
				max_bytes = 10 * 1024 * 1024
				with urllib.request.urlopen(url, timeout=30) as resp:
					# Simple content-length check
					cl = resp.getheader('Content-Length')
					if cl:
						try:
							if int(cl) > max_bytes:
								raise ValueError("Remote file too large")
						except Exception:
							pass
					# write to temp file
					fd, tmp_path = tempfile.mkstemp(dir=fonts_dir)
					with os.fdopen(fd, 'wb') as out_f:
						total = 0
						chunk_size = 16 * 1024
						while True:
							chunk = resp.read(chunk_size)
							if not chunk:
								break
							out_f.write(chunk)
							total += len(chunk)
							if total > max_bytes:
								out_f.close()
								os.remove(tmp_path)
								raise ValueError("Downloaded file exceeds size limit")
					# Atomic rename
					os.replace(tmp_path, dest_real)
					# Restrictive permissions
					try:
						os.chmod(dest_real, 0o644)
					except Exception:
						pass
			if os.path.exists(dest_real):
				print(f"Ready: {key}")
			else:
				print(f"Failed: {key}")
		except Exception:
			# Do not raise — missing fonts should not crash the app
			print(f"Failed: {key}")
			continue


def get_font_file_path(font_name):
	# Only allow keys from SUPPORTED_FONTS (prevents traversal via font_name)
	meta = SUPPORTED_FONTS.get(font_name)
	if not meta:
		return None
	filename = meta.get("file", f"{font_name}.ttf")
	# Resolve path and ensure it stays inside FONT_DIR
	path = os.path.realpath(os.path.join(FONT_DIR, filename))
	if not path.startswith(FONT_DIR + os.sep):
		return None
	return path


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

