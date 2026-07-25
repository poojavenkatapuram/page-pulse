# Technology Decisions

This document records the major technology choices for Page Pulse and distinguishes between:

- current implementation choices already present in the codebase
- proposed production choices recommended for a scaled deployment

## Decision Summary

| Technology | Status | Primary Role |
|---|---|---|
| FastAPI | Current | Backend API framework |
| Next.js | Current | Frontend application framework |
| Redis | Proposed | Shared cache and ephemeral coordination |
| RabbitMQ | Proposed | Queue for asynchronous audit execution |
| PostgreSQL | Proposed | Durable persistence for audit data |
| Render | Current | Backend hosting platform |
| Vercel | Current | Frontend hosting platform |
| GitHub Actions | Current | Continuous integration |

## FastAPI

### Decision

Use FastAPI for the backend API layer.

### Why Chosen

Page Pulse is an HTTP-first service with a small, well-defined contract, typed request and response schemas, and a need for clean error handling. FastAPI aligns well with those constraints.

### Advantages

- Strong Pydantic integration for request and response validation
- Good developer ergonomics for typed APIs
- First-class async support for outbound HTTP workloads
- Automatic OpenAPI and interactive documentation
- Straightforward dependency injection and middleware support

### Disadvantages

- Some middleware and lifecycle composition details require care at scale
- Async does not eliminate the need for explicit outbound concurrency controls
- Complex long-running workflows often need extra infrastructure beyond the core framework

### Alternatives Considered

- Flask
- Django REST Framework
- Express.js / Node.js backend

### Why Alternatives Were Rejected

Flask is flexible but less opinionated for typed API contracts. Django REST Framework is powerful but heavier than necessary for a focused audit service. Express.js would work well operationally but would require a different parsing and typing stack than the current Python-based backend.

### Trade-offs

FastAPI maximizes speed of implementation and type safety, but production maturity still depends on surrounding operational choices such as logging, rate limiting, caching, and worker isolation.

## Next.js

### Decision

Use Next.js for the frontend.

### Why Chosen

Page Pulse needs a polished, responsive, production-ready user interface with clean deployment ergonomics. Next.js provides a strong default foundation without unnecessary client-side complexity.

### Advantages

- Strong TypeScript support
- Good routing and app structure for a single-page product experience
- Excellent deployment workflow on Vercel
- Easy composition of reusable UI components
- Strong ecosystem for performance and accessibility work

### Disadvantages

- Framework overhead is higher than a minimal SPA build
- App Router conventions can increase complexity for very small apps
- Version upgrades can occasionally require framework-specific maintenance

### Alternatives Considered

- Vite + React
- Plain React with CRA-style scaffolding
- Vue / Nuxt

### Why Alternatives Were Rejected

Vite + React would also be a good fit, but Next.js offers stronger production hosting alignment and better portfolio-level presentation for a product-style interface. CRA-style approaches are less current. Vue/Nuxt would add a second ecosystem without clear project benefit.

### Trade-offs

Next.js is slightly more framework than the assignment strictly requires, but it improves delivery quality, deployment simplicity, and long-term maintainability.

## Redis

### Decision

Use Redis as the shared ephemeral state layer in the proposed scaled architecture.

### Why Chosen

The current implementation uses an in-memory cache inside the FastAPI process. That works for a single instance but does not scale across multiple API replicas. Redis solves that cleanly.

### Advantages

- Very low latency for cache reads and writes
- Natural fit for TTL-based audit result caching
- Useful for distributed rate limiting
- Useful for short-lived job state and deduplication
- Operationally mature and widely understood

### Disadvantages

- Adds another operational dependency
- Cache invalidation and key design still require care
- Introduces network hops compared with local memory

### Alternatives Considered

- Keep only in-process cache
- Memcached
- PostgreSQL-only caching pattern

### Why Alternatives Were Rejected

In-process caching fails once requests are distributed across multiple API instances. Memcached is viable but less versatile for multi-purpose ephemeral state. PostgreSQL can store results durably but is not ideal for low-latency, TTL-oriented hot-path caching.

### Trade-offs

Redis adds infrastructure complexity, but it materially improves consistency and performance in a horizontally scaled deployment.

## RabbitMQ

### Decision

Use RabbitMQ, or an equivalent durable queue, for asynchronous audit execution in the proposed production architecture.

### Why Chosen

Outbound website fetching is the least predictable part of the workload. Decoupling it from synchronous API request handling creates better resilience during bursts and under slow-upstream conditions.

### Advantages

- Durable queueing and acknowledgements
- Clear retry and dead-letter semantics
- Good visibility into backlog depth
- Mature operational behavior for task processing workloads

### Disadvantages

- Additional infrastructure to operate
- More moving pieces than direct synchronous processing
- Requires worker orchestration and observability

### Alternatives Considered

- Keep audits fully synchronous in API workers
- Redis-backed queue systems
- Cloud-managed task services

### Why Alternatives Were Rejected

Fully synchronous execution is simpler but less resilient under burst traffic and slow third-party targets. Redis-backed queueing can work, but RabbitMQ provides stronger queue semantics out of the box. Cloud-managed task services may be attractive later but increase platform coupling.

### Trade-offs

RabbitMQ increases operational footprint but gives the system explicit backpressure handling and better control over failure recovery.

## PostgreSQL

### Decision

Use PostgreSQL for durable audit and operational data in the proposed production architecture.

### Why Chosen

Even if the product remains simple, durable storage adds supportability, audit history, analytics potential, and a source of truth independent of cache state.

### Advantages

- Strong consistency and mature tooling
- Familiar operational characteristics
- Excellent fit for structured audit records
- Good support for indexing by normalized URL and audit timestamp

### Disadvantages

- Adds persistence management, backups, and schema evolution concerns
- Higher operational cost than a cache-only approach
- Requires careful compatibility planning during deployments

### Alternatives Considered

- No persistent storage
- SQLite
- Document databases such as MongoDB

### Why Alternatives Were Rejected

No persistent storage limits debugging and historical analysis. SQLite is not appropriate for a horizontally scaled service. A document store could work, but the audit record shape is structured enough that PostgreSQL remains the simpler and more predictable option.

### Trade-offs

PostgreSQL adds operational weight, but it provides a durable foundation for history, reporting, and rollback-safe operational workflows.

## Render

### Decision

Use Render for backend deployment in the current implementation.

### Why Chosen

Render offers a low-friction hosting path for FastAPI, fast deployment iteration, and a straightforward developer experience suitable for an internship assignment and early production staging.

### Advantages

- Simple deployment for Python web services
- Managed HTTPS and service exposure
- Good fit for small teams and portfolio projects
- Minimal setup burden

### Disadvantages

- Less control than self-managed infrastructure
- Platform-specific limits may shape scaling behavior
- Cold starts and free-tier constraints can affect perceived performance

### Alternatives Considered

- Fly.io
- Railway
- AWS ECS / EKS
- Google Cloud Run

### Why Alternatives Were Rejected

Cloud-native container platforms offer more flexibility but would add setup and operational complexity beyond the assignment's intended scope. Render is a more pragmatic fit for the current stage.

### Trade-offs

Render optimizes for delivery speed over maximum infrastructure control. That is a reasonable trade for the current implementation.

## Vercel

### Decision

Use Vercel for frontend deployment.

### Why Chosen

Vercel is tightly aligned with Next.js and makes frontend delivery, HTTPS, and preview workflows simple.

### Advantages

- Excellent Next.js deployment integration
- Fast static asset delivery
- Clean environment-variable workflow
- Easy preview deployments for UI changes

### Disadvantages

- Platform coupling to Vercel-specific conventions
- Less control than a custom CDN and hosting stack
- Cost and scaling characteristics depend on product growth

### Alternatives Considered

- Netlify
- Cloudflare Pages
- S3 + CDN hosting

### Why Alternatives Were Rejected

All could work, but Vercel offers the most direct path for a Next.js project and reduces operational friction.

### Trade-offs

Vercel improves frontend deployment speed and reliability, while trading away some low-level infrastructure control.

## GitHub Actions

### Decision

Use GitHub Actions for CI.

### Why Chosen

The repository already lives in GitHub, and the project benefits from lightweight automated checks on backend and frontend changes.

### Advantages

- Native GitHub integration
- Good support for Python and Node workflows
- Easy visibility on pull requests
- Appropriate for small-to-medium project CI needs

### Disadvantages

- Workflow debugging can be slower than local runs
- Hosted runners introduce environment differences
- Secrets and environment handling need discipline

### Alternatives Considered

- CircleCI
- GitLab CI
- Buildkite

### Why Alternatives Were Rejected

They are capable platforms, but GitHub Actions has the lowest integration cost for this repository and team size.

### Trade-offs

GitHub Actions is not the most specialized CI platform, but it is the most practical and maintainable choice for this project.

## Final Recommendation

The current stack is appropriate for the delivered Page Pulse implementation:

- Next.js on Vercel for product UX
- FastAPI on Render for backend delivery
- GitHub Actions for CI

For the next stage of production maturity, the strongest additions are:

- Redis for shared cache and ephemeral distributed state
- RabbitMQ for queue-backed external fetch execution
- PostgreSQL for durable storage and operational traceability

Those additions preserve the current architecture's strengths while making the system more credible under sustained production load.
