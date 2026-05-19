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
    return b"Name\nAlice\n"


def _post_generate(client, template_bytes, spreadsheet_bytes, **data):
    files = {
        "template_file": ("template.jpg", template_bytes, "image/jpeg"),
        "spreadsheet_file": ("names.csv", spreadsheet_bytes, "text/csv"),
    }
    default = {
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
    }
    default.update(data)
    # attach a unique X-API-Key per request to avoid hitting rate limits
    headers = {}
    count = getattr(_post_generate, "_counter", 0) + 1
    _post_generate._counter = count
    headers["X-API-Key"] = f"test-key-{count}"
    return client.post("/api/generate", files=files, data=default, headers=headers)


def test_font_color_hex_variants(monkeypatch):
    monkeypatch.setattr(main.font_manager, "download_all_fonts", lambda: None)
    client = TestClient(main.app)
    template = _make_jpeg_bytes()
    sheet = _make_csv_bytes()

    # valid uppercase
    r = _post_generate(client, template, sheet, font_color_hex="#C9A84C")
    assert r.status_code == 200

    # valid lowercase
    r = _post_generate(client, template, sheet, font_color_hex="#c9a84c")
    assert r.status_code == 200

    # invalid script injection
    r = _post_generate(client, template, sheet, font_color_hex='"> <script>alert(1)</script>')
    assert r.status_code == 400
    assert r.json().get("code") == "INVALID_HEX_COLOR"

    # invalid hex letters
    r = _post_generate(client, template, sheet, font_color_hex="#GGGGGG")
    assert r.status_code == 400
    assert r.json().get("code") == "INVALID_HEX_COLOR"

    # wrong length (5 chars)
    r = _post_generate(client, template, sheet, font_color_hex="#12345")
    assert r.status_code == 400
    # too long (7 chars)
    r = _post_generate(client, template, sheet, font_color_hex="#1234567")
    assert r.status_code == 400

    # empty string (server may return 400 or 422 depending on parsing)
    r = _post_generate(client, template, sheet, font_color_hex="")
    assert r.status_code in (400, 422)


def test_font_size_bounds_and_types(monkeypatch):
    monkeypatch.setattr(main.font_manager, "download_all_fonts", lambda: None)
    client = TestClient(main.app)
    template = _make_jpeg_bytes()
    sheet = _make_csv_bytes()

    # too small 0
    r = _post_generate(client, template, sheet, font_size="0")
    assert r.status_code == 400
    assert r.json().get("code") == "INVALID_FONT_SIZE"

    # 5 invalid
    r = _post_generate(client, template, sheet, font_size="5")
    assert r.status_code == 400

    # boundary valid 6
    r = _post_generate(client, template, sheet, font_size="6")
    assert r.status_code == 200

    # boundary valid 500
    r = _post_generate(client, template, sheet, font_size="500")
    assert r.status_code == 200

    # too large 501
    r = _post_generate(client, template, sheet, font_size="501")
    assert r.status_code == 400

    # non-integer
    r = _post_generate(client, template, sheet, font_size="abc")
    assert r.status_code in (400, 422)


def test_x_y_pct_bounds_and_types(monkeypatch):
    monkeypatch.setattr(main.font_manager, "download_all_fonts", lambda: None)
    client = TestClient(main.app)
    template = _make_jpeg_bytes()
    sheet = _make_csv_bytes()

    # valid 0.0,0.0
    r = _post_generate(client, template, sheet, x_pct="0.0", y_pct="0.0")
    assert r.status_code == 200

    # valid 1.0,1.0
    r = _post_generate(client, template, sheet, x_pct="1.0", y_pct="1.0")
    assert r.status_code == 200

    # too large
    r = _post_generate(client, template, sheet, x_pct="1.001", y_pct="0.5")
    assert r.status_code == 400
    assert r.json().get("code") == "INVALID_X_PCT"

    # negative
    r = _post_generate(client, template, sheet, x_pct="-0.001", y_pct="0.5")
    assert r.status_code == 400

    # non-numeric
    r = _post_generate(client, template, sheet, x_pct="abc", y_pct="0.5")
    assert r.status_code in (400, 422)
    if r.status_code == 400:
        assert r.json().get("code") == "INVALID_COORDINATES"
