# CertGen — Security Testing Prompt for Production

Paste this entire prompt into GitHub Copilot (or any AI coding assistant).
It covers every exploitable surface in the CertGen stack based on the actual codebase.

---

## Context

CertGen is a FastAPI backend + vanilla JS frontend for bulk certificate generation.
Key files:
- `backend/main.py` — FastAPI app, CORS, lifespan
- `backend/routes/generate.py` — `/api/generate` and `/api/parse-spreadsheet` endpoints
- `backend/routes/fonts.py` — `/api/fonts` and `/api/fonts/{font_name}` endpoints
- `backend/services/certificate.py` — Pillow image processing
- `backend/services/font_manager.py` — font download and path resolution
- `backend/services/spreadsheet.py` — CSV and XLSX parsing
- `backend/services/zip_builder.py` — ZIP file assembly
- `frontend/js/uploader.js`, `placer.js`, `generator.js`, `app.js` — browser-side logic

Write real test code (pytest for backend, plain JS or HTML for frontend) for every item below.
Where a test is a manual penetration step rather than automated code, write the exact curl command or payload.

---

## 1. File Upload Validation — Template (JPEG/PNG)

### 1a. MIME type bypass
Test that a file with a `.jpg` extension but a malicious payload (e.g. a PHP webshell, an HTML file, a ZIP bomb) is rejected. The backend currently checks the filename extension only — it does NOT verify magic bytes.

**Write a pytest test that:**
- Sends a file named `evil.jpg` whose content is `<?php system($_GET['cmd']); ?>` to `POST /api/generate`
- Asserts a 400 response

**Then patch `generate.py`** to open the file with `PIL.Image.open()` early and verify it is actually a valid image before any other processing. If PIL raises an exception, return a 400 with `code: INVALID_IMAGE`.

### 1b. ZIP bomb / decompression bomb via PNG
A crafted PNG that is small on disk but expands to gigabytes in memory can crash the server.

**Write a pytest test that:**
- Sends a valid but pathologically large decompressed image (use Pillow to generate a 10000×10000 white PNG in memory) to `/api/generate`
- Asserts a 400 response with `code: TEMPLATE_TOO_LARGE`

**Then patch `generate.py`** to check image pixel dimensions after `PIL.Image.open()` and reject if `width * height > 25_000_000` (approximately 25 MP).

### 1c. Template size limit enforcement
Verify the `MAX_TEMPLATE_SIZE_MB` env var is actually read on every request, not cached at startup.

**Write a pytest test that:**
- Sets `MAX_TEMPLATE_SIZE_MB=1` via `monkeypatch.setenv`
- Sends a valid 1.5 MB JPEG
- Asserts a 400 response with `code: TEMPLATE_TOO_LARGE`

---

## 2. File Upload Validation — Spreadsheet (CSV / XLSX)

### 2a. XLSX formula injection (CSV injection)
XLSX and CSV files can contain formulas like `=HYPERLINK("http://attacker.com","click")` or `=cmd|' /C calc'!A0`.
If the extracted names are ever rendered in a downstream context (email, another spreadsheet, an HTML page), this executes.

**Write a pytest test that:**
- Creates an XLSX with a name cell containing `=HYPERLINK("http://evil.com","click")`
- Sends it to `/api/parse-spreadsheet`
- Asserts the returned preview row contains the raw string `=HYPERLINK(...)` unchanged (i.e. the backend does not evaluate it) AND that this string does NOT appear verbatim in any generated certificate image (it should be rendered as text by Pillow, not evaluated)

**Note for the developer:** Because `openpyxl` uses `data_only=True`, formulas are returned as the cached formula string. Add a sanitization step in `spreadsheet.py` that strips any cell value starting with `=`, `+`, `-`, or `@` and replaces it with an empty string or raises a warning.

### 2b. CSV injection via crafted delimiters
**Write a pytest test that:**
- Creates a CSV with a row containing `"=1+1","Normal Name"` (formula in first column)
- Sends it to `/api/parse-spreadsheet`
- Asserts the name column value is sanitized (does not start with `=`)

### 2c. Malformed / oversized spreadsheet
**Write a pytest test that:**
- Sends a 50 MB file named `big.xlsx` to `/api/parse-spreadsheet`
- Asserts a 400 or 413 response (currently there is NO size check on the spreadsheet upload — patch `generate.py` and `parse-spreadsheet` to add a `MAX_SPREADSHEET_SIZE_MB` check defaulting to `5`)

### 2d. Non-spreadsheet disguised as XLSX
**Write a pytest test that:**
- Sends a file named `names.xlsx` whose content is a JPEG
- Asserts a 400 response (openpyxl will throw; ensure the exception is caught cleanly rather than returning a 500)

---

## 3. Path Traversal — Font Endpoint

### 3a. Directory traversal via font name
`GET /api/fonts/{font_name}` passes `font_name` to `get_font_file_path()`, which joins it with `FONT_DIR`. A crafted name like `../../etc/passwd` could read arbitrary files.

**Write a pytest test that:**
- Sends `GET /api/fonts/../../etc/passwd`
- Asserts a 404 response (not a 200 with file contents)

**Then patch `fonts.py`** to validate that `font_name` is in the `SUPPORTED_FONTS` allowlist BEFORE constructing any path. The current code does check `get_font_list()` first, but confirm the check happens before `os.path.join`.

### 3b. Null byte injection in font name
**Write a pytest test that:**
- Sends `GET /api/fonts/playfair_display%00.txt`
- Asserts a 404 response

---

## 4. Input Validation — Generate Endpoint Parameters

### 4a. `font_color_hex` — arbitrary CSS/HTML injection
`font_color_hex` is passed to `certificate.py` and parsed with `int(hex_clean[0:2], 16)`. A value like `"><script>alert(1)</script>` will raise an unhandled `ValueError`.

**Write a pytest test that:**
- Sends `font_color_hex="><script>alert(1)</script>` to `/api/generate` with a valid template + spreadsheet
- Asserts a 400 response (not a 500)

**Patch `generate.py`** to validate `font_color_hex` with a regex `^#[0-9A-Fa-f]{6}$` before calling `certificate.generate_certificate`. Return `code: INVALID_COLOR` on failure.

### 4b. `x_pct` and `y_pct` — float bounds
Values outside `[0.0, 1.0]` won't crash but will produce invisible or garbage certificates.

**Write a pytest test that:**
- Sends `x_pct=9999` and `y_pct=-500` to `/api/generate`
- Asserts either a 400 or a certificate where the name is clipped at a boundary (document the current behavior)

**Patch `generate.py`** to clamp `x_pct` and `y_pct` to `[0.0, 1.0]`.

### 4c. `font_size` — extreme values
`font_size=0` or `font_size=10000` could cause PIL to hang or allocate excessive memory.

**Write a pytest test that:**
- Sends `font_size=0` — asserts 400
- Sends `font_size=10000` — asserts 400

**Patch `generate.py`** to validate `6 <= font_size <= 500`. Return `code: INVALID_FONT_SIZE`.

### 4d. `font_name` — arbitrary font path injection
`font_name` is passed to `get_font_file_path()`. If an attacker supplies a value not in `SUPPORTED_FONTS`, the fallback in `get_font()` catches it, but the code currently does NOT return an error for unrecognised font names — it silently falls back to DejaVu or default.

**Write a pytest test that:**
- Sends `font_name=../../../../usr/share/fonts/truetype/evil` to `/api/generate`
- Asserts a 400 response with `code: INVALID_FONT`

**Patch `generate.py`** to reject any `font_name` not present in `font_manager.get_font_list()` before calling `generate_certificate`.

### 4e. `name_column` — column name not present in spreadsheet
If `name_column` is not a key in the uploaded spreadsheet, `get_names()` returns an empty list and `generate_certificate` is called with 0 names. Uploading a template still processes and returns an empty ZIP with no error.

**Write a pytest test that:**
- Sends a valid spreadsheet with column `Name` but `name_column=DoesNotExist`
- Asserts a 400 response with `code: COLUMN_NOT_FOUND`

---

## 5. Batch Limit Bypass

### 5a. Split-request bypass
The batch limit (`MAX_BATCH_SIZE=200`) is checked after parsing. An attacker could call `/api/generate` directly with a crafted XLSX containing 201 names.

**Write a pytest test that:**
- Sends an XLSX with exactly 201 rows
- Asserts a 400 response with `code: BATCH_LIMIT_EXCEEDED`

### 5b. Zip bomb output — many names × large template
**Write a pytest test that measures peak memory** during generation of 200 names on a 10 MB template and asserts it stays below a reasonable threshold (e.g. 2 GB). This is an integration-level stress test — document the result.

---

## 6. CORS Configuration

### 6a. Wildcard CORS in production
`main.py` has `allow_origins=["*"]` hardcoded. This means any website can make credentialed requests to the API from a user's browser.

**Write a pytest test that:**
- Sends an `OPTIONS` preflight with `Origin: https://attacker.com`
- Asserts `Access-Control-Allow-Origin` in the response is NOT `*` in production mode

**Patch `main.py`** to read `ALLOWED_ORIGINS` from the environment variable (already defined in `.env.example`) and split on commas. Default to `["*"]` only when `ENV=development`. Example:

```python
origins = os.environ.get("ALLOWED_ORIGINS", "*")
allow_origins = ["*"] if origins == "*" else [o.strip() for o in origins.split(",")]
```

---

## 7. ZIP File Security

### 7a. ZIP slip — sanitized filename bypass
`_sanitize_name()` in `zip_builder.py` strips path separators but uses `re.sub(r"[^A-Za-z0-9_-]", "", s)`. Confirm a name like `../../etc/passwd` produces a safe archive entry name.

**Write a pytest test that:**
- Calls `zip_builder._sanitize_name("../../etc/passwd")`
- Asserts the result is `etcpasswd` (no slashes)

**Then confirm** that `zipfile.ZipFile` on Python 3.11 does NOT allow writing entries with `..` in them by default and add a guard anyway.

### 7b. Empty ZIP response
If all name values are empty strings after stripping, the API currently returns an empty ZIP with a 200 status.

**Write a pytest test that:**
- Sends a spreadsheet with one row where the name column is `   ` (whitespace only)
- Asserts a 400 response with `code: NO_VALID_NAMES`

---

## 8. Error Information Disclosure

### 8a. Stack traces in 500 responses
FastAPI by default returns Python exception details in development. Verify production mode does not leak stack traces.

**Write a pytest test that:**
- Triggers an intentional server error (e.g. corrupt PIL image bytes)
- Asserts the response body does NOT contain `Traceback` or file paths

**Patch `main.py`** to add a global exception handler:

```python
from fastapi.responses import JSONResponse
from fastapi import Request

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": "Internal server error", "code": "INTERNAL_ERROR"})
```

### 8b. Font download failure disclosure
`font_manager.py` catches exceptions silently with `pass`. Ensure font download failures do not surface internal paths or URLs in any API response.

---

## 9. Rate Limiting

### 9a. No rate limiting on `/api/generate`
The generate endpoint processes CPU- and memory-intensive Pillow operations. There is currently no rate limiting.

**Document the attack:** An attacker can flood `/api/generate` with 200-name batches on a large template to exhaust Railway's free-tier CPU/memory and cause downtime.

**Recommended fix:** Add `slowapi` rate limiting:

```python
# pip install slowapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# On the route:
@router.post("/generate")
@limiter.limit("10/minute")
async def generate(request: Request, ...):
```

**Write a pytest test** using `slowapi`'s test client that:
- Sends 11 requests to `/api/generate` in sequence
- Asserts the 11th returns a 429 response

---

## 10. Frontend Security

### 10a. `API_BASE` hardcoded fallback
In `app.js`, the production URL fallback is `https://your-backend.railway.app`. If a developer forgets to replace this, all requests silently go to the placeholder domain (which might be registered by someone else).

**Write a Jest (or plain browser console) test that:**
- Mocks `window.location.hostname` as a non-localhost value
- Imports `app.js` and checks that `API_BASE` does NOT equal `'https://your-backend.railway.app'`

**Recommended fix:** Replace the hardcoded fallback with an env variable injected at build time (e.g. via a `config.js` generated by the Netlify build script).

### 10b. No `Content-Security-Policy` header
The frontend is served by Netlify's static file server with no CSP header. Any XSS in user-supplied content (preview name rendered in canvas — currently safe, but worth locking down) could exfiltrate data.

**Add a `netlify.toml` `[[headers]]` block:**

```toml
[[headers]]
  for = "/*"
  [headers.values]
    Content-Security-Policy = "default-src 'self'; connect-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com https://*.railway.app; font-src 'self' https://fonts.gstatic.com; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; img-src 'self' blob: data:;"
    X-Frame-Options = "DENY"
    X-Content-Type-Options = "nosniff"
    Referrer-Policy = "strict-origin-when-cross-origin"
```

**Manually verify** using curl that these headers appear in the Netlify response.

### 10c. `alert()` used for error display (XSS vector)
`uploader.js` and `generator.js` call `alert(err.error || ...)` with server-provided strings. If the backend ever echoes user input in an error message (e.g. the column name), a crafted column name could trigger XSS via `alert()`.

**Write a browser test (Playwright or manual) that:**
- Creates a CSV with a column named `<img src=x onerror=alert(1)>`
- Sends it to the app and verifies `alert()` receives the raw string — not an executed script (since `alert()` renders plain text, this is safe today — but document the risk for future `innerHTML` use)

**Recommended fix:** Replace all `alert()` calls with a proper in-page error banner that uses `textContent` (not `innerHTML`).

---

## 11. Dependency Security Scan

Run the following and fix any HIGH or CRITICAL findings before deploying:

```bash
# Backend
pip install pip-audit
pip-audit -r backend/requirements.txt

# Check for known-vulnerable Pillow versions (common source of CVEs)
pip show Pillow | grep Version
```

**Write a CI step** (GitHub Actions) that runs `pip-audit` and fails the build on HIGH+ severity:

```yaml
- name: Audit Python dependencies
  run: |
    pip install pip-audit
    pip-audit -r backend/requirements.txt --severity high --fail-on-vuln
```

---

## 12. Docker / Railway Deployment Hardening

### 12a. Running as root
The `Dockerfile` does not set a non-root user. FastAPI runs as root inside the container, meaning any RCE gives full container access.

**Patch `backend/Dockerfile`:**

```dockerfile
RUN useradd -m certgen
USER certgen
```

Verify with:
```bash
docker run --rm certgen-backend whoami
# should print: certgen
```

### 12b. Font directory is world-writable
`download_all_fonts()` writes to `/app/fonts` inside the container. Confirm no endpoint allows an attacker to trigger arbitrary writes to that directory via a crafted font name that escapes to a different path.

**Write a pytest test that:**
- Mocks `urllib.request.urlretrieve` to capture the destination path
- Calls `download_all_fonts()`
- Asserts every destination path starts with the expected `FONT_DIR` prefix

---

## 13. Authentication — API Key Middleware

### 13a. All `/api/` endpoints are publicly accessible with no authentication
Currently anyone who discovers your Railway backend URL can call `/api/generate`, `/api/parse-spreadsheet`, and `/api/fonts` directly — bypassing your frontend entirely. Since this is a side project with a static frontend and no user login system, a shared API key is the right fit. It blocks direct backend access without adding any visible friction to real users.

**Implement the middleware in `backend/main.py`:**

```python
import os
from fastapi import Request
from fastapi.responses import JSONResponse

API_KEY = os.environ.get("API_KEY", "")

@app.middleware("http")
async def check_api_key(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        if API_KEY:
            key = request.headers.get("X-API-Key", "")
            if key != API_KEY:
                return JSONResponse(
                    status_code=401,
                    content={"error": "Unauthorized", "code": "INVALID_API_KEY"}
                )
    return await call_next(request)
```

Set `API_KEY=your-secret-value` in Railway's environment variable settings. Leave `API_KEY` unset or empty in local development so it doesn't block you during testing.

**Write a pytest test that:**
- Sets `API_KEY=test-secret` via `monkeypatch.setenv`
- Sends a request to `/api/fonts` with no `X-API-Key` header
- Asserts a 401 response with `code: INVALID_API_KEY`

**Write a second pytest test that:**
- Sends the same request with `X-API-Key: test-secret`
- Asserts a 200 response

**Write a third pytest test that:**
- Sends the request with `X-API-Key: wrong-key`
- Asserts a 401 response

### 13b. Exempt the `/health` endpoint
The Railway healthcheck hits `/health` without any headers. Make sure the middleware does not block it.

**Write a pytest test that:**
- Sets `API_KEY=test-secret` via `monkeypatch.setenv`
- Sends `GET /health` with no headers
- Asserts a 200 response with `{"status": "ok"}`

The middleware above already handles this since it only checks paths starting with `/api/` — confirm this is the case.

### 13c. Wire the API key into all three frontend fetch calls

There are exactly 3 places in the frontend that call the backend. All three need the header added:

**`frontend/js/app.js`** — fonts fetch:
```javascript
const res = await fetch(API_BASE + '/api/fonts', {
  headers: { "X-API-Key": "your-secret-value" }
});
```

**`frontend/js/uploader.js`** — spreadsheet parse:
```javascript
fetch(window.API_BASE + '/api/parse-spreadsheet', {
  method: 'POST',
  body: fd,
  headers: { "X-API-Key": "your-secret-value" }
})
```

**`frontend/js/generator.js`** — certificate generation:
```javascript
const res = await fetch(window.API_BASE + '/api/generate', {
  method: 'POST',
  body: fd,
  headers: { "X-API-Key": "your-secret-value" }
});
```

**Important caveat to document:** Since CertGen's frontend is plain static JS with no build step, the API key is stored in plain text in `app.js`, `uploader.js`, and `generator.js`. Anyone who opens browser DevTools can read it. This is an acceptable tradeoff for a side project — it still blocks anyone hitting the Railway URL directly without the frontend. It is NOT a substitute for real authentication if the app ever handles sensitive data. Keep the key out of your public GitHub repository by either keeping the repo private or injecting the key at deploy time via a Netlify build environment variable and a simple `config.js` file.

---

## Summary Checklist

After implementing and running all tests above, verify the following manually before going live:

- [ ] Magic byte validation on template upload (not just extension check)
- [ ] Image dimension cap (25 MP max)
- [ ] Spreadsheet size limit enforced
- [ ] Formula injection sanitized in spreadsheet parser
- [ ] `font_color_hex` validated by regex
- [ ] `font_name` restricted to allowlist
- [ ] `x_pct`, `y_pct` clamped to [0.0, 1.0]
- [ ] `font_size` validated in range [6, 500]
- [ ] `name_column` existence validated before generation
- [ ] Path traversal blocked on `/api/fonts/{font_name}`
- [ ] CORS restricted to production frontend domain
- [ ] Rate limiting on `/api/generate` (10 req/min recommended)
- [ ] Global 500 handler does not leak stack traces
- [ ] Security headers on Netlify frontend
- [ ] `pip-audit` passing with no HIGH/CRITICAL findings
- [ ] Container running as non-root user
- [ ] `API_BASE` production URL correctly set (not placeholder)
- [ ] `API_KEY` set in Railway environment variables
- [ ] All 3 frontend fetch calls send `X-API-Key` header
- [ ] `/health` endpoint responds 200 without an API key (Railway healthcheck)
- [ ] API key not committed to public GitHub repository
