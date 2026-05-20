# CertGen — Critical Issues Report (v2, current codebase)
# Give this entire file to Copilot. Fix issues in the order listed.

---

## ISSUE 1 — PRODUCTION COMPLETELY BROKEN (Blocker)
### `API_BASE` placeholder URL still in `frontend/js/app.js`

File: `frontend/js/app.js`, line 10
Current code:
```javascript
return 'https://your-backend.railway.app';
```

Every fetch call from the Netlify frontend (fonts, spreadsheet parsing, certificate generation)
goes to a placeholder domain that does not exist. The app is entirely non-functional in production.

Fix — replace the placeholder with the real Railway URL before deploying:
```javascript
return 'https://YOUR-ACTUAL-SERVICE.up.railway.app';
```

To avoid forgetting this in future deploys, move it to a separate config file that is
gitignored so it is never accidentally reset:

Create `frontend/js/config.js`:
```javascript
window.CERTGEN_API_BASE = 'https://YOUR-ACTUAL-SERVICE.up.railway.app';
window.CERTGEN_API_KEY  = 'your-api-key-here';
```

Add to `.gitignore`:
```
frontend/js/config.js
```

Add to `frontend/index.html` before the app.js script tag:
```html
<script src="js/config.js"></script>
```

Update `frontend/js/app.js`:
```javascript
const API_BASE = (() => {
  const hostname = window.location.hostname;
  if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '') {
    return 'http://localhost:8000';
  }
  return window.CERTGEN_API_BASE || '';
})();
```

And replace the localStorage line:
```javascript
window.API_KEY = window.CERTGEN_API_KEY || localStorage.getItem('certgen_api_key') || '';
```

---

## ISSUE 2 — CSP BLOCKS ALL BACKEND CALLS (Blocker)
### `netlify.toml` Content-Security-Policy sets `connect-src 'self'` which blocks Railway

File: `frontend/netlify.toml`

Current CSP:
```
connect-src 'self';
```

The Netlify frontend origin (e.g. `https://certgen.netlify.app`) and the Railway backend
origin (e.g. `https://yourservice.up.railway.app`) are different domains. `connect-src 'self'`
tells the browser to block ALL fetch() calls to any domain other than the Netlify one.
This means fonts, spreadsheet parsing, and certificate generation all fail silently
with a CSP violation the moment the site goes live.

Fix — add the Railway URL to connect-src. Replace the CSP line in netlify.toml:
```toml
Content-Security-Policy = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' blob: data:; connect-src 'self' https://YOUR-ACTUAL-SERVICE.up.railway.app; frame-ancestors 'none'; upgrade-insecure-requests;"
```

Replace `https://YOUR-ACTUAL-SERVICE.up.railway.app` with the real Railway URL.

---

## ISSUE 3 — SPREADSHEET UPLOAD BREAKS WITH API KEYS ENABLED (Critical)
### `uploader.js` parse-spreadsheet fetch sends no `X-API-Key` header

File: `frontend/js/uploader.js`

Current code:
```javascript
fetch(window.API_BASE + '/api/parse-spreadsheet', { method:'POST', body: fd })
```

When API_KEYS is set on Railway (i.e. in production), the backend returns 401.
The user uploads their spreadsheet in Step 3, nothing happens, the column selector
never populates, and they cannot proceed to Step 4. The error shows as a generic
"Could not read spreadsheet" message with no indication it is an auth issue.

Fix:
```javascript
const spHeaders = {};
if(window.API_KEY) spHeaders['X-API-Key'] = window.API_KEY;
fetch(window.API_BASE + '/api/parse-spreadsheet', { method:'POST', headers: spHeaders, body: fd })
```

---

## ISSUE 4 — METRICS ENDPOINT PUBLICLY ACCESSIBLE (Security)
### `/metrics` in `backend/main.py` sits outside `/api/` and bypasses API key middleware

File: `backend/main.py`

Current code:
```python
@app.get("/metrics")
async def metrics():
    return {
        "rate_limit_count": getattr(app.state, "rate_limit_count", 0),
        "request_count": getattr(app.state, "request_count", 0),
    }
```

The API key middleware only protects paths starting with `/api/`. The `/metrics`
endpoint is at the root level, so anyone who knows your Railway URL can poll it
without a key. Currently it only exposes two counters, but it confirms your service
is live, reveals traffic patterns, and will leak more if you ever add fields.

Fix — add a key check directly on the endpoint:
```python
@app.get("/metrics")
async def metrics(request: Request):
    from auth import _load_keys
    valid_keys = _load_keys()
    if valid_keys:
        key = request.headers.get("X-API-Key", "")
        if key not in valid_keys:
            return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    return {
        "rate_limit_count": getattr(app.state, "rate_limit_count", 0),
        "request_count": getattr(app.state, "request_count", 0),
    }
```

---

## ISSUE 5 — TypeError CRASH IN FONT LOADING (Reliability)
### `get_font()` calls `os.path.exists(None)` when path is None

File: `backend/services/font_manager.py`

Current code:
```python
def get_font(font_name, size):
    path = get_font_file_path(font_name)
    if os.path.exists(path):   # TypeError if path is None
```

`get_font_file_path()` returns `None` for unknown font names or unsafe paths.
`os.path.exists(None)` raises TypeError in Python. The generate.py validator
prevents this in the normal flow, but it is a crash waiting to happen if ever
called from anywhere else, and it causes quota to be reserved but not released
because the exception propagates through the generation loop before the release
block runs.

Fix — one line change:
```python
def get_font(font_name, size):
    path = get_font_file_path(font_name)
    if path and os.path.exists(path):
```

---

## What is being skipped and why it does not matter for your setup

**CSV injection / formula sanitization** — already implemented in `_sanitize_cell()`.
The frontend also uses `textContent` everywhere in the preview table, not `innerHTML`,
so even if a formula got through it cannot execute in the browser. Skipped.

**ZIP slip / filename traversal** — `_sanitize_name()` strips everything except
alphanumeric, underscore, hyphen. Python's `zipfile` on 3.11 also has internal
protections. Skipped.

**Path traversal on font endpoint** — `get_font_file_path()` now uses `os.realpath()`
and checks the resolved path starts with `FONT_DIR + os.sep`. The route also checks
the allowlist before constructing any path. Solid. Skipped.

**Dependency vulnerabilities** — `audit-report.json` in your repo shows zero
vulnerabilities across all pinned packages including Pillow 12.2.0. No action needed
until the next audit.

**CORS wildcard + credentials bug** — already fixed in `main.py`. The code now
detects the wildcard + credentials combination and either disables credentials or
fails fast in production mode. Skipped.

**Rate limiting on parse-spreadsheet** — already added (`@limiter.limit("10/minute")`).
Skipped.

**Decompression bomb / oversized image** — already handled. PIL verify + 25MP cap
in `generate.py`. Skipped.

**Magic byte validation** — already handled. `img.verify()` before processing. Skipped.

**Non-root Docker user** — already in Dockerfile (`useradd appuser`). Skipped.

**Font download host allowlist** — already in `font_manager.py` (`ALLOWED_HOSTS`).
Skipped.

**Stack trace leakage** — global exception handler in `main.py` returns only
`{"error": "Internal server error", "code": "SERVER_ERROR"}`. Skipped.

**Per-key quota in-memory reset** — known limitation, documented in `quota.py`.
For your usage (small orgs, occasional batches) this is acceptable. Railway's free
tier sleeps containers between uses anyway; the quota is a courtesy limit not a
hard billing control. Skipped.

**Proxy IP spoofing on rate limiter** — `limiter.py` defaults to socket-level IP,
not `X-Forwarded-For`. Safe by default. `USE_PROXY_HEADERS` is off. Skipped.

**API key in localStorage / plain text JS** — acceptable tradeoff for a static
frontend with no build step. It blocks direct Railway access; it does not protect
against someone reading DevTools. For a small side project with known institution
users this is the right call. Skipped.

---

## Fix order

| # | Issue | Severity | File |
|---|---|---|---|
| 1 | Placeholder `API_BASE` URL | **Blocker** | `frontend/js/app.js` |
| 2 | CSP blocks Railway backend | **Blocker** | `frontend/netlify.toml` |
| 3 | Missing API key on parse-spreadsheet | **Critical** | `frontend/js/uploader.js` |
| 4 | `/metrics` unprotected | **Security** | `backend/main.py` |
| 5 | `os.path.exists(None)` in get_font | **Reliability** | `backend/services/font_manager.py` |

Fix 1 and 2 before anything else — without both the app does not work at all in production.
Fix 3 immediately after — without it Step 3 of the workflow silently breaks when API keys are active.
Fix 4 and 5 before making the Railway URL public.
