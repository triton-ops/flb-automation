# Best-effort container image — UNVERIFIED. No Docker daemon is available in the environment this
# was written in (docker --version fails here), so this has not been build-tested. It follows the
# standard Microsoft Playwright Python image pattern (matches requirements.txt's playwright==1.60.0
# pin exactly, so the bundled browser build lines up with what the rest of this repo expects) —
# review and build-test before relying on it.
FROM mcr.microsoft.com/playwright/python:v1.60.0-noble

WORKDIR /app

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY . .

# Credentials are never baked into the image — mount/pass .env at run time (see .env.example and
# docs/ci-secrets.md), same convention as every other entry point in this repo.
ENTRYPOINT ["pytest"]
CMD ["tests/e2e", "-v"]
