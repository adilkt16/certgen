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
import uuid


def _make_jpeg_bytes():
    image = Image.new("RGB", (32, 32), color="white")
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


def _make_csv_bytes():
    return b"Name\nAlice\n"


def test_invalid_output_format_returns_400(monkeypatch):
    monkeypatch.setattr(main.font_manager, "download_all_fonts", lambda: None)

    client = TestClient(main.app)
    template_bytes = _make_jpeg_bytes()
    spreadsheet_bytes = _make_csv_bytes()

    headers = {"X-API-Key": str(uuid.uuid4())}
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
            "output_format": "hack",
            "bold": "false",
            "italic": "false",
            "text_align": "center",
            },
            headers=headers,
    )

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_OUTPUT_FORMAT"
    assert "output_format must be jpeg, pdf, or both" in response.json()["error"]
