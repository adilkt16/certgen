## CertGen Production Deployment Guide

This document lists recommended codebase changes, infrastructure setup steps, and operational tasks to publish CertGen to production safely and reliably. Follow the sections in order and check off items as you complete them.

Prerequisites
- Ensure you have a working CI environment (GitHub Actions, GitLab CI, etc.).
- A container registry (Docker Hub, GitHub Packages, Azure Container Registry, etc.).
- A hosting target for the backend (e.g., AWS ECS/EKS, Azure App Service, Render, Railway, DigitalOcean App Platform).
- A static hosting/CDN for the frontend (Vercel, Netlify, CloudFront + S3, or serve from the same host).
- Domain name and DNS control.

1) Codebase: prepare for production
- Pin dependencies: lock `requirements.txt` with exact versions. Run `pip freeze > requirements.txt` from a clean virtualenv after installing tested versions.
- Remove development-only packages from production requirements.
- Ensure `backend/main.py` and other services read configuration (secrets, DB URLs) from environment variables only.
- Add runtime configuration via `.env.example` (do NOT commit secrets).
- Add logging configuration (structured logs, level adjustable by env var). Prefer JSON logs for ingestion by log collectors.
- Add error handling and consistent HTTP error responses; create custom 5xx/4xx error pages if serving HTML.
- Ensure static assets are cache-busted (fingerprint filenames or use a build step for hashing).

2) Security hardening
- Enforce HTTPS and HSTS at the proxy/load balancer.
- Add security headers: `Content-Security-Policy`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `Permissions-Policy`.
- Use strict CORS rules for the API; only allow known origins.
- Disable directory listing and debug endpoints; ensure `DEBUG` is false in production.
- Scan dependencies for vulnerabilities (e.g., `pip-audit`, `safety`, or Snyk). Address critical/high issues.
- Store secrets in a secrets manager (GitHub Secrets, AWS Secrets Manager, Azure Key Vault). Never hardcode credentials.
- Enforce rate limiting to prevent abuse and denial-of-service.

3) Containerization & build
- Create a multi-stage `Dockerfile` for the backend (build, then minimal runtime image). Use an official Python base and pin base image versions.
- For frontend static assets, optionally create a small nginx-based container or deploy to a static host (Vercel/Netlify). Build step should minify and fingerprint assets.
- Add a healthcheck endpoint (`/health` or `/healthz`) used by orchestrators.
- Scan the built image with Trivy or similar and fix findings.

4) CI/CD pipeline
- Configure CI to run on pull requests and main branch merges:
  - Run linters (`flake8`, `black` check or `isort`), type checks (mypy) if used.
  - Run unit tests and integration tests.
  - Build frontend assets (if applicable) and run a smoke test against the built static output.
  - Build Docker image, run containerized tests, push image to registry.
  - Publish release artifacts and trigger deployment job.
- Use immutable tags (e.g., `registry/myapp:${{ github.sha }}`) and promote tags to environments (staging -> production).
- Store deployment credentials as encrypted pipeline secrets.

5) Infrastructure & hosting
- Choose an environment for initial production (Render/Railway/Heroku for fast setup; AWS/Azure/GCP for full control).
- Provision environment with at least two app instances behind a load balancer for availability.
- Use a managed database or ensure your database has replication and backups. Configure connection pooling.
- Configure object storage for generated artifacts (S3, DigitalOcean Spaces). Serve generated ZIPs from object storage with signed URLs.
- Configure a CDN (CloudFront, Cloudflare) in front of static assets and, optionally, API for caching CDNs.

6) Domain, DNS, and TLS
- Point your domain to the host using A/CAA/CNAME records as required. Add `www` and apex records.
- Use TLS certificates from Let's Encrypt or the cloud provider's managed certificates. Automate renewal.
- Configure mail sender and SPF/DKIM/DMARC records if sending emails.

7) Observability & monitoring
- Add structured logs to a log sink (LogDNA, Datadog, AWS CloudWatch). Ensure logs include request ids and user ids where applicable.
- Integrate error tracking (Sentry) for runtime exceptions and unhandled errors.
- Configure uptime monitoring and alerting (Pingdom, UptimeRobot, or provider built-ins).
- Add basic metrics (request rate, error rate, latency) via Prometheus or provider metrics; set alerts for SLO breaches.

8) Backups, migrations & data retention
- Implement automated backups of databases and object storage, and test restore procedures.
- If using migrations (Alembic, Django migrations), integrate `migrate` steps in deploy with safe roll-forward procedures.
- Define retention policies for artifacts, logs, and generated files; consider lifecycle policies for S3 buckets.

9) Performance & testing
- Run load testing (k6, locust) to understand capacity and set autoscaling thresholds.
- Optimize image processing tasks (use worker queues for heavy CPU work; e.g., Celery/RQ with a task queue).
- Consider background job processing for long-running exports and provide user-facing progress and retries.

10) Legal, privacy & compliance
- Publish Privacy Policy and Terms of Service (links exist in the footer, ensure copy is accurate).
- If you collect personal data (names/emails), ensure compliance with GDPR and other relevant regulations.
- If you later accept payments, ensure PCI compliance and use a PCI-compliant provider (Stripe recommended).

11) Launch checklist
- Deploy to staging and perform full E2E smoke tests.
- Validate domain, TLS, and DNS propagation.
- Verify logging, error reporting, and metrics flow into your dashboards.
- Run a simulated production workflow (upload template, place name, generate ZIP) and verify artifact storage and delivery.
- Prepare rollback plan and test restoring previous version from image tags and database backups.

12) Post-launch operations
- Monitor error rates and user feedback closely for the first 72 hours.
- Schedule regular dependency vulnerability scans and security reviews.
- Add rate limits, abuse detection, and monitoring rules as usage patterns emerge.

Quick commands and examples
- Build a production Docker image (example):
```
docker build -t registry/yourorg/certgen:$(git rev-parse --short HEAD) .
docker push registry/yourorg/certgen:$(git rev-parse --short HEAD)
```
- Run container locally with env file:
```
docker run --env-file .env -p 8000:8000 registry/yourorg/certgen:abcd123
```

Further reading and references
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- Twelve-Factor App: https://12factor.net/
- Docker security and scanning: Trivy, Clair

If you want, I can:
- Scaffold a `Dockerfile` and a sample `github/workflows/ci.yml`.
- Add a `.env.example` and a `deploy/` helper script.
