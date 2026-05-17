# CertGen
CertGen is a lightweight certificate generator that lets you upload a certificate template and a spreadsheet of names, place and style the text, and generate a ZIP of finished certificates in JPEG, PDF, or both formats.

## Local setup (exact commands)
```bash
cd /home/user/Desktop/certgen-small/certgen/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

In a second terminal:
```bash
cd /home/user/Desktop/certgen-small/certgen/frontend
python3 -m http.server 5500
```

## Deploy to Railway and Netlify (exact steps)
1. Push this repository to GitHub.
2. In Railway, create a new project from the GitHub repo and set the service root to `backend`.
3. Confirm Railway uses the Dockerfile in `backend/Dockerfile` and deploy the service.
4. Copy the Railway service URL and replace `API_BASE` in `frontend/js/app.js` with that URL.
5. In Netlify, create a new site from the same GitHub repo and set the publish directory to `frontend`.
6. Deploy the Netlify site.
7. After the backend and frontend are both live, open the Netlify URL and verify `/health` on Railway returns `{"status":"ok","service":"certgen-backend"}`.

## Environment variables (table)
| Variable | Used by | Purpose | Default |
| --- | --- | --- | --- |
| `MAX_BATCH_SIZE` | backend | Maximum names per batch | `200` |
| `FONTS_DIR` | backend | Folder used for downloaded fonts | `./fonts` |
| `MAX_TEMPLATE_SIZE_MB` | backend | Template upload size limit | `10` |
| `ALLOWED_ORIGINS` | backend | CORS origin allow list | `*` |
| `API_BASE` | frontend | Backend base URL for fetch requests | `https://your-backend.railway.app` |

## Cost: $0/month
This project can run at no monthly cost on the free tiers of Railway and Netlify as long as usage stays within those providers' free-tier limits.
