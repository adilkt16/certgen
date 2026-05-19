import io
import os
import sys

from fastapi.testclient import TestClient
from PIL import Image

HERE = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(HERE, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import main


def _make_jpeg_bytes():
    image = Image.new("RGB", (32, 32), color="white")
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


def _make_csv_bytes():
    # All-name values sanitize to empty
    return b"Name\n@@@\n!!!\n"


def test_no_valid_names_returns_400(monkeypatch):
    monkeypatch.setattr(main.font_manager, "download_all_fonts", lambda: None)

    client = TestClient(main.app)
    template_bytes = _make_jpeg_bytes()
    spreadsheet_bytes = _make_csv_bytes()

    response = client.post(
        "/api/generate",
        files={
            "template_file": ("template.jpg", template_bytes, "image/jpeg"),
            "spreadsheet_file": ("names.csv", spreadsheet_bytes, "text/csv"),
        },
        data={
            "name_column": "Name",
            "x_pct": "0.5",
            "y_pct": "0.5",
            "font_name": "playfair_display",
            "font_size": "64",
            "font_color_hex": "#C9A84C",
            "output_format": "jpeg",
            "bold": "false",
            "italic": "false",
            "text_align": "center",
        },
    )

    assert response.status_code == 400
    assert response.json()["code"] == "NO_VALID_NAMES"
    assert "No valid names" in response.json()["error"]
