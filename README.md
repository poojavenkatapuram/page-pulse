# Page Pulse

Page Pulse is a focused URL auditor for checking the essential on-page signals of any public webpage. Enter a domain or complete URL to receive a concise report covering response health, content structure, metadata, and a basic accessibility signal.

---

## Overview

Page Pulse is a full-stack web application built for the **Digital Heroes Software Development Internship Qualification Task**.

The application allows users to audit any public webpage by entering its URL. The frontend sends the request to a FastAPI backend, which safely fetches the webpage, analyzes its HTML, and returns a structured SEO and accessibility report.

The project emphasizes:

- Robust backend engineering
- Clean API design
- Error handling
- Responsive frontend UI
- Production deployment
- Automated testing

---

## Features

- Audit any valid public HTTP or HTTPS URL.
- Automatically prepend `https://` when only a domain is entered.
- Extract:
  - HTTP Status Code
  - Response Time
  - Page Title
  - Meta Description
  - H1 Count
  - Images Missing Alt Text
  - Approximate Visible Word Count
- Gracefully handle:
  - Invalid URLs
  - Timeouts
  - DNS failures
  - SSL failures
  - Redirect loops
  - Non-HTML responses
  - Oversized pages
- SSRF protection by blocking private/local network destinations.
- Clean responsive UI with loading, validation, success, and error states.
- Automated backend and frontend testing.

---

# Tech Stack

| Layer | Technologies |
|--------|--------------|
| Frontend | Next.js 15, TypeScript, Tailwind CSS, Axios, Lucide React |
| Backend | Python 3.12, FastAPI, Pydantic v2, httpx |
| HTML Parsing | BeautifulSoup4, lxml |
| Backend Testing | pytest |
| Frontend Testing | Vitest, React Testing Library |
| Deployment | Vercel (Frontend), Render (Backend) |

---

# Architecture

```text
Browser
    │
    │ POST /api/v1/audits
    ▼
Next.js Frontend (Vercel)
    │
    ▼
FastAPI Backend (Render)
    │
    ├── URL Validation
    ├── SSRF Protection
    ├── HTTP Fetch
    ├── HTML Parsing
    └── Response Formatting
    │
    ▼
Structured JSON Report
```

The frontend is responsible for collecting user input and presenting the audit results.

The backend performs URL validation, secure HTTP fetching, HTML parsing, structured response generation, and error handling.

---

# Repository

GitHub Repository

**https://github.com/poojavenkatapuram/page-pulse**

---

# API Endpoint

## Create Audit

```
POST /api/v1/audits
```

### Request

```json
{
  "url": "https://example.com"
}
```

### Success Response

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

### Error Response

```json
{
  "error": {
    "code": "NON_HTML_RESPONSE",
    "message": "The URL returned content that is not an HTML page."
  }
}
```

---

# API Contract

| Method | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/v1/audits` | Audit a webpage |
| GET | `/health` | Backend health check |

Possible HTTP responses:

| Status | Meaning |
|---------|---------|
| 200 | Success |
| 400 | Invalid URL |
| 422 | Non-HTML Response |
| 502 | Upstream Fetch Error |
| 504 | Timeout |

---

# Example cURL Request

```bash
curl -X POST https://page-pulse-2-6vmo.onrender.com/api/v1/audits \
-H "Content-Type: application/json" \
-d '{"url":"https://example.com"}'
```

---

# Local Setup

## Prerequisites

- Python 3.12
- Node.js 20+
- pnpm

---

## Backend

Create a virtual environment

```bash
python -m venv .venv
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run the backend

```bash
uvicorn app.main:app --reload
```

Backend runs at

```
http://localhost:8000
```

Health endpoint

```
http://localhost:8000/health
```

---

## Frontend

Move into frontend

```bash
cd frontend
```

Install packages

```bash
pnpm install
```

Start development server

```bash
pnpm dev
```

Runs at

```
http://localhost:3000
```

---

# Environment Variables

## Backend

Copy

```
.env.example
```

to

```
.env
```

Variables

| Variable | Description |
|----------|-------------|
| ALLOWED_ORIGINS | Allowed frontend origins |
| FETCH_TIMEOUT_SECONDS | Request timeout |
| MAX_REDIRECTS | Redirect limit |
| MAX_RESPONSE_BYTES | Maximum HTML size |
| PORT | Hosting platform port |

---

## Frontend

Copy

```
frontend/.env.example
```

to

```
frontend/.env.local
```

Variable

```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

---

# Live Deployment

## Frontend

https://page-pulse-hazel.vercel.app

## Backend

https://page-pulse-2-6vmo.onrender.com

## Health Endpoint

https://page-pulse-2-6vmo.onrender.com/health

---

# Project Structure

```text
.
├── app/
│   ├── api/
│   ├── parsers/
│   ├── schemas/
│   ├── services/
│   ├── config.py
│   └── main.py
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── types/
│   └── vitest.config.ts
│
├── tests/
├── render.yaml
├── requirements.txt
└── README.md
```

---

# Testing

## Backend

```bash
pytest -q
```

Tests include:

- Successful audits
- Invalid URLs
- DNS failures
- SSL failures
- Redirect handling
- Timeouts
- Oversized responses
- Parser extraction
- SSRF protection

---

## Frontend

```bash
cd frontend

pnpm test

pnpm typecheck
```

Tests include:

- Empty input validation
- Loading state
- Disabled submit button
- Successful report rendering
- Error rendering
- Footer verification
- Metric cards
- Accessibility labels

---

# Design Decisions

## 1. Backend Owns All Fetching

The browser never contacts audited websites directly.

Keeping all network requests inside FastAPI:

- avoids browser CORS issues
- enables timeout control
- prevents SSRF attacks
- limits response size
- centralizes error handling

---

## 2. Service Layer Architecture

Business logic is separated from API routes.

This makes the code:

- easier to test
- easier to maintain
- easier to extend

The API routes remain thin while services handle audit orchestration.

---

## 3. Strongly Typed API Contract

The backend returns typed Pydantic models.

The frontend consumes matching TypeScript interfaces.

Benefits:

- predictable API
- compile-time safety
- fewer runtime bugs
- easier maintenance

---

# Future Improvements

- JavaScript rendering using Playwright
- Authentication and user accounts
- Audit history
- Export reports as PDF
- Additional SEO metrics
- Open Graph analysis
- Canonical URL detection
- Robots.txt analysis
- Sitemap validation
- Rate limiting

---

# Author

**Pooja Venkatapuram**

---

# Assignment Information

This project was developed as part of the **Digital Heroes Software Development Internship Qualification Task**.

The live application includes the required footer:

> **Built for Digital Heroes Training Task**

linked to

https://digitalheroesco.com

---

# Live Links

### GitHub Repository

https://github.com/poojavenkatapuram/page-pulse

### Live Frontend

https://page-pulse-hazel.vercel.app

### Backend API

https://page-pulse-2-6vmo.onrender.com

### Health Endpoint

https://page-pulse-2-6vmo.onrender.com/health