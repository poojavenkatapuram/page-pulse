# Page Pulse

Page Pulse is a focused URL auditor for checking the essential on-page signals of any public webpage. Enter a domain or complete URL to receive a concise report covering response health, content structure, metadata, and a basic accessibility signal.

## Overview

The application pairs a Next.js frontend with a FastAPI backend. The browser submits a URL to the API; the API validates it, safely fetches the target page, parses its server-rendered HTML, and returns a structured audit report.

## Features

- Audits any valid public `http` or `https` URL.
- Automatically adds `https://` when a domain is entered without a scheme.
- Reports HTTP status, response time, page title, meta description, H1 count, missing image alt text, and approximate visible word count.
- Handles invalid URLs, redirects, timeouts, DNS/SSL/connection errors, non-HTML responses, oversized pages, and parsing failures with structured errors.
- Blocks local and private-network destinations to reduce SSRF risk.
- Provides clear empty, loading, success, validation, and error states in a responsive interface.
- Includes automated backend and frontend test suites with mocked network behavior.

## Tech Stack

| Layer | Technologies |
| --- | --- |
| Frontend | Next.js 15, TypeScript, Tailwind CSS, Axios, Lucide React |
| Backend | Python 3.12, FastAPI, Pydantic v2, httpx |
| HTML parsing | BeautifulSoup4 with lxml |
| Frontend testing | Vitest, React Testing Library |
| Backend testing | pytest |
| Hosting | Vercel (frontend), Render (backend) |

## Architecture

```text
Browser
  |
  | POST /api/v1/audits
  v
Next.js frontend (Vercel)
  |
  v
FastAPI API (Render)
  |
  +-- URL validation and SSRF checks
  +-- Bounded HTTP fetch with redirect handling
  +-- BeautifulSoup HTML parser
  |
  v
Structured JSON audit report
```

The frontend is responsible for user interaction and report presentation. The backend owns URL validation, safe outbound HTTP requests, response-size limits, HTML parsing, and error mapping.

## API Endpoint

### Create an audit

`POST /api/v1/audits`

Request body:

```json
{
  "url": "https://example.com"
}
```

Successful responses return `200 OK`. Invalid input returns `400`; non-HTML content returns `422`; unreachable upstream services return `502`; and fetch timeouts return `504`.

## API Request and Response Example

```bash
curl -X POST https://page-pulse-2-6vmo.onrender.com/api/v1/audits \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}'
```

```json
{
  "url": "https://example.com/",
  "http_status": 200,
  "response_time_ms": 245.18,
  "title": "Example Domain",
  "meta_description": null,
  "h1_count": 1,
  "images_missing_alt_text": 0,
  "approximate_word_count": 22
}
```

Error responses use a consistent envelope:

```json
{
  "error": {
    "code": "NON_HTML_RESPONSE",
    "message": "The URL returned content that is not an HTML page."
  }
}
```

## Local Setup

### Prerequisites

- Python 3.12
- Node.js 20.9 or later
- pnpm

### Backend

From the repository root:

```bash
python -m venv .venv
```

Activate the virtual environment, then install and run the API:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`, and its health endpoint is available at `http://localhost:8000/health`.

### Frontend

From the `frontend` directory:

```bash
pnpm install
pnpm dev
```

The frontend is available at `http://localhost:3000`.

## Environment Variables

### Backend

Copy `.env.example` to `.env` when local overrides are needed.

| Variable | Purpose | Default |
| --- | --- | --- |
| `ALLOWED_ORIGINS` | Comma-separated browser origins permitted by CORS | `http://localhost:3000` |
| `FETCH_TIMEOUT_SECONDS` | Maximum page-fetch duration | `10` |
| `MAX_REDIRECTS` | Maximum redirects followed | `5` |
| `MAX_RESPONSE_BYTES` | Maximum HTML response size processed | `2000000` |
| `PORT` | Port provided by the hosting platform | Platform-managed |

### Frontend

Copy `frontend/.env.example` to `frontend/.env.local`.

| Variable | Purpose |
| --- | --- |
| `NEXT_PUBLIC_API_BASE_URL` | Public base URL for the FastAPI backend |

For local development:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Live Demo

- Frontend: [https://page-pulse-hazel.vercel.app](https://page-pulse-hazel.vercel.app)
- Backend: [https://page-pulse-2-6vmo.onrender.com](https://page-pulse-2-6vmo.onrender.com)
- Health check: [https://page-pulse-2-6vmo.onrender.com/health](https://page-pulse-2-6vmo.onrender.com/health)

## Project Structure

```text
.
├── app/
│   ├── api/                 # FastAPI routes
│   ├── parsers/             # HTML parsing logic
│   ├── schemas/             # Pydantic request and response models
│   ├── services/            # Fetching and audit orchestration
│   ├── config.py            # Application configuration
│   └── main.py              # FastAPI application entry point
├── frontend/
│   ├── app/                 # Next.js App Router pages and styles
│   ├── components/          # Reusable UI components
│   ├── lib/                 # Axios API client
│   ├── types/               # Shared frontend types
│   └── vitest.config.ts     # Frontend test configuration
├── tests/                   # pytest backend tests
├── render.yaml              # Render service configuration
└── requirements.txt         # Python dependencies
```

## Testing

### Backend

```bash
pytest -q
```

The backend suite covers successful audits, URL validation, redirects, timeouts, DNS and SSL failures, non-HTML responses, oversized responses, parser extraction, and SSRF blocking. All outbound HTTP behavior is mocked; tests never depend on the internet.

### Frontend

```bash
cd frontend
pnpm test
pnpm typecheck
```

The frontend suite covers empty-input validation, loading behavior, disabled submission, successful report rendering, API errors, metric cards, footer content, and accessible labels.

## Design Decisions

### 1. Keep outbound fetching on the backend

The browser never fetches audited URLs directly. Centralizing fetching in FastAPI avoids browser CORS limitations and lets the application enforce timeouts, response-size limits, redirect controls, and private-network blocking consistently.

### 2. Use a small service layer around the API route

FastAPI route handlers remain intentionally small. The audit service owns HTTP orchestration and error mapping, while the parser handles only HTML extraction. This keeps the code testable and makes each responsibility easier to change independently.

### 3. Treat the report as structured data, not scraped UI text

The backend returns a typed Pydantic response model, and the frontend consumes a corresponding TypeScript interface. This makes API contracts explicit and prevents presentation code from depending on unstructured responses.

## Future Improvements

- Support JavaScript-rendered pages with an optional browser-rendering mode.
- Add rate limiting and per-user audit quotas for a larger public deployment.
- Store audit history and enable before/after comparisons.
- Add additional SEO signals such as canonical URLs, Open Graph tags, and heading hierarchy.
- Provide downloadable audit reports.

## Author

Pooja Venkatapuram

Built for the Digital Heroes Software Development Internship assignment.
