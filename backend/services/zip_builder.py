import io
import zipfile
import re


def _sanitize_name(name: str) -> str:
	s = name.replace(" ", "_")
	s = re.sub(r"[^A-Za-z0-9_-]", "", s)
	return s[:80]


def build_zip(certificates, output_format):
	buf = io.BytesIO()
	with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
		for cert in certificates:
			raw_name = cert.get("name", "cert")
			name = _sanitize_name(raw_name)

			# JPEG handling
			if output_format in ("jpeg", "both"):
				jpeg_bytes = cert.get("jpeg")
				if jpeg_bytes:
					if output_format == "jpeg":
						arcname = f"{name}.jpg"
					else:
						arcname = f"jpeg/{name}.jpg"
					z.writestr(arcname, jpeg_bytes)

			# PDF handling
			if output_format in ("pdf", "both"):
				pdf_bytes = cert.get("pdf")
				if pdf_bytes:
					if output_format == "pdf":
						arcname = f"{name}.pdf"
					else:
						arcname = f"pdf/{name}.pdf"
					z.writestr(arcname, pdf_bytes)

	return buf.getvalue()

