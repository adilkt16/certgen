import os
import urllib.request
import PIL.ImageFont

SUPPORTED_FONTS = {
	"cinzel_bold": "https://github.com/google/fonts/raw/main/ofl/cinzel/static/Cinzel-Bold.ttf",
	"cinzel_regular": "https://github.com/google/fonts/raw/main/ofl/cinzel/static/Cinzel-Regular.ttf",
	"playfair_bold": "https://github.com/google/fonts/raw/main/ofl/playfairdisplay/static/PlayfairDisplay-Bold.ttf",
	"playfair_regular": "https://github.com/google/fonts/raw/main/ofl/playfairdisplay/static/PlayfairDisplay-Regular.ttf",
	"montserrat_bold": "https://github.com/google/fonts/raw/main/ofl/montserrat/static/Montserrat-Bold.ttf",
	"montserrat_regular": "https://github.com/google/fonts/raw/main/ofl/montserrat/static/Montserrat-Regular.ttf",
	"lato_bold": "https://github.com/google/fonts/raw/main/ofl/lato/Lato-Bold.ttf",
	"lato_regular": "https://github.com/google/fonts/raw/main/ofl/lato/Lato-Regular.ttf",
	"raleway_bold": "https://github.com/google/fonts/raw/main/ofl/raleway/static/Raleway-Bold.ttf",
	"opensans_bold": "https://github.com/google/fonts/raw/main/ofl/opensans/static/OpenSans-Bold.ttf",
}


def download_all_fonts():
	fonts_dir = "./fonts"
	os.makedirs(fonts_dir, exist_ok=True)
	for key, url in SUPPORTED_FONTS.items():
		dest = os.path.join(fonts_dir, f"{key}.ttf")
		if os.path.exists(dest):
			print(f"Ready: {key}")
			continue
		try:
			urllib.request.urlretrieve(url, dest)
			if os.path.exists(dest):
				print(f"Ready: {key}")
			else:
				print(f"Failed: {key}")
		except Exception:
			print(f"Failed: {key}")
			continue


def get_font(font_name, size):
	path = f"./fonts/{font_name}.ttf"
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

