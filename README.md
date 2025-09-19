# Adidas Danki Server

## Overview
This repository contains a Flask application that centralizes product data for Adidas footwear lines used by Danki, exposing both a REST API and a lightweight admin interface. The server boots with a MongoDB connection, enforces collection schemas, and dynamically generates CRUD routes for the main collections (`shoes`, `suggestion`, `pinterest`, `images`, and `tag`).【F:app.py†L33-L208】 Beyond basic persistence, the API offers aggregation pipelines that join shoes with associated images, Pinterest assets, color variants, and cross-sell suggestions to support retail touchpoints and digital kiosks.【F:app.py†L211-L395】 The service also manages tag lookups, rich shoe updates, and HTTPS hosting with certificate files under `static/`.【F:app.py†L469-L704】

## Key Features
- **Dynamic CRUD API** – Generates standard create/read/update/delete endpoints for each configured MongoDB collection at startup.【F:app.py†L33-L208】
- **Product aggregation endpoints** – Provides composite views such as `/shoes-with-images`, `/shoe-with-pinterest`, `/shoe-details`, and tag-filtered listings for retail experiences.【F:app.py†L211-L595】
- **Pinterest ingestion pipeline** – Scrapes boards, uploads imagery to S3, and persists links back to MongoDB, both from API endpoints and standalone utilities.【F:app.py†L400-L466】【F:utils/pinterest.py†L1-L181】
- **Admin dashboard** – Blueprint-backed HTML pages for listing sneakers, uploading assets to S3, browsing Pinterest boards, and fetching in-store telemetry via external APIs.【F:admin.py†L12-L137】
- **Schema enforcement** – Applies JSON Schema validators to critical collections during boot to keep data consistent.【F:database.py†L9-L76】
- **Automation scripts** – Includes importers for initial shoe data, suggestion relationships, and utilities to fabricate kiosk analytics samples.【F:imports/import_shoes.py†L1-L35】【F:imports/import_suggestion.py†L1-L33】【F:generate_fakes.py†L1-L36】

## Project Layout
| Path | Description |
| --- | --- |
| `app.py` | Flask application factory, dynamic routes, and public API endpoints.【F:app.py†L41-L704】 |
| `admin.py` | Admin blueprint with HTML routes, S3 uploads, Pinterest board browsing, and telemetry proxying.【F:admin.py†L12-L137】 |
| `database.py` | Helper functions that load JSON schemas and attach validators to MongoDB collections.【F:database.py†L9-L76】 |
| `schemas/` | JSON schema files consumed by `database.py` (ensure they match MongoDB collections). |
| `utils/` | Service integrations for AWS S3 (`boto.py`) and Pinterest scraping/storage (`pinterest.py`).【F:utils/boto.py†L1-L80】【F:utils/pinterest.py†L1-L181】 |
| `imports/` | Scripts and seed files to bulk-load product and suggestion data into MongoDB.【F:imports/import_shoes.py†L1-L35】【F:imports/import_suggestion.py†L1-L33】 |
| `templates/` & `static/` | Admin HTML templates, shared assets, and SSL certificate files referenced when running with HTTPS.【F:app.py†L700-L704】 |
| `documentation/` | Markdown reference describing every API endpoint in greater detail.【F:documentation/endpoints.md†L1-L170】 |
| `tests/` | Pytest/unittest cases covering S3 helpers and Pinterest ingestion flows (require external services).【F:tests/test_boto.py†L1-L58】【F:tests/test_pin.py†L1-L11】 |

## Application Components
### Flask Application (`app.py`)
1. **App factory** – Loads environment variables, registers the admin blueprint, instantiates the Mongo client, applies schema validators, and stores database handles on the Flask app instance.【F:app.py†L41-L77】
2. **Dynamic CRUD routes** – `create_crud_routes` defines POST/GET/PUT/DELETE handlers for each configured collection, including ObjectId conversion for nested payloads.【F:app.py†L84-L208】
3. **Aggregation & helper endpoints** – Dedicated routes join shoes with images, Pinterest content, color variants, tag metadata, and kiosk suggestions, while additional endpoints expose tag CRUD, shoe updates, and image lookups.【F:app.py†L211-L692】
4. **Pinterest sync endpoint** – `/add-pinterest-data` orchestrates scraping a Pinterest board, uploading assets to S3, saving URLs to MongoDB, and cleaning temporary files.【F:app.py†L400-L466】
5. **Runtime configuration** – When executed directly, the server binds to `0.0.0.0:5050` with SSL certificates located at `static/fullchain.pem` and `static/privkey.pem`.【F:app.py†L700-L704】

### Admin Blueprint (`admin.py`)
- Serves menu, list, detail, create, scan, and report pages under `/sneaker/*`, rendering Jinja templates found in `templates/admin`.【F:admin.py†L12-L43】
- Provides a multipart upload endpoint that streams sneaker imagery to an S3 bucket using Flask form fields and a helper from `utils.boto`.【F:admin.py†L45-L77】
- Integrates with the Pinterest API to list boards (token read from environment variables) and fetches remote telemetry data for dashboards.【F:admin.py†L80-L137】

### Database Schema Management (`database.py`)
- Loads JSON schemas from the `schemas/` directory, ensures collections exist, and runs `collMod` to enforce validators on MongoDB, keeping shoe, suggestion, Pinterest, and image documents aligned with expectations.【F:database.py†L9-L76】

### Utility Modules (`utils/`)
- **`boto.py`** – Configures a boto3 S3 client from environment credentials and exposes helpers for uploading, downloading, listing, deleting, and generating presigned URLs for assets.【F:utils/boto.py†L1-L80】
- **`pinterest.py`** – Reads Pinterest tokens and Mongo credentials from environment variables, downloads pins for mapped boards, uploads media to S3, and writes links back to MongoDB collections.【F:utils/pinterest.py†L1-L181】

### Data Import & Generation (`imports/` & scripts)
- `imports/import_shoes.py` loads seed products from `Import.json`, splits out image URLs, and populates both `shoes` and `images` collections.【F:imports/import_shoes.py†L10-L35】
- `imports/import_suggestion.py` converts object IDs from JSON and inserts cross-sell suggestion documents.【F:imports/import_suggestion.py†L17-L33】
- `generate_fakes.py` fabricates kiosk telemetry entries for testing dashboards fed by `/dados-danki`.【F:generate_fakes.py†L1-L36】

### Tests & Documentation
- `tests/test_boto.py` exercises the S3 helper functions end-to-end against a test bucket, verifying upload, list, URL generation, download, and deletion flows (requires valid AWS credentials and `TEST_S3_BUCKET`).【F:tests/test_boto.py†L1-L55】
- `tests/test_pin.py` posts to `/add-pinterest-data` to validate the Pinterest ingestion endpoint while the server is running locally.【F:tests/test_pin.py†L1-L11】
- `documentation/endpoints.md` supplements this README with request/response examples for every public API route.【F:documentation/endpoints.md†L1-L170】

## Configuration
Create a `.env` file (or equivalent environment configuration) with the following keys before running the application:

| Variable | Purpose |
| --- | --- |
| `MONGO_URI` | Connection string for the `danki-adidas` MongoDB database used by the API and Pinterest utilities.【F:app.py†L50-L69】【F:utils/pinterest.py†L33-L44】 |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION` | Credentials for the AWS account hosting sneaker imagery in S3, consumed by `utils.boto`.【F:utils/boto.py†L1-L38】 |
| `TEST_S3_BUCKET` | Bucket name targeted by admin uploads and S3 unit tests.【F:admin.py†L45-L77】【F:tests/test_boto.py†L8-L55】 |
| `PINTEREST_TOKEN` | OAuth token for Pinterest API requests used in both the admin blueprint and Pinterest utilities.【F:admin.py†L80-L105】【F:utils/pinterest.py†L46-L99】 |

When running with HTTPS locally, ensure `static/fullchain.pem` and `static/privkey.pem` contain the appropriate certificates referenced by the development server entry point.【F:app.py†L700-L704】

## Getting Started
1. **Install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Configure environment** – Populate `.env` with the variables listed above and provision the referenced MongoDB cluster, S3 buckets, and Pinterest access token.
3. **Run the server**
   - For local HTTP development:
     ```bash
     flask --app app run --port 5050 --host 0.0.0.0
     ```
   - To mirror the production HTTPS configuration, launch the module directly so Flask reads the certificate pair:
     ```bash
     python app.py
     ```
4. **Explore the API** – Consult `documentation/endpoints.md` for payload formats, or visit the admin UI at `http://localhost:5050/` to use the HTML tools.【F:documentation/endpoints.md†L1-L170】【F:admin.py†L12-L43】

## Running Tests
The bundled tests rely on live AWS and Pinterest services. Ensure the Flask app is running and external credentials are configured before executing:
```bash
pytest
```
- `tests/test_boto.py` requires valid AWS credentials and access to `TEST_S3_BUCKET` to complete S3 operations.【F:tests/test_boto.py†L1-L55】
- `tests/test_pin.py` expects the Flask server to be available on `http://127.0.0.1:5000` with `/add-pinterest-data` enabled and backed by a reachable Mongo/Pinterest stack.【F:tests/test_pin.py†L1-L11】

## Additional Resources
- API walkthrough: `documentation/endpoints.md`
- Static assets and TLS material: `static/`
- Admin templates: `templates/admin/`

These materials complement the README when onboarding new contributors or deploying the service.
