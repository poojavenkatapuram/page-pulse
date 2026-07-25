# Observability and Rollbacks

This document describes the operational practices required to run Page Pulse as a production service with customer-facing reliability expectations.

Important distinction:

- Current implementation: structured application logging, request IDs, `/health`, CI, and production deployments already exist.
- Proposed production additions in this document: centralized metrics collection, dashboards, formal alerting, readiness/liveness separation, and controlled deployment rollback workflows.

## Structured Logging

Page Pulse already benefits from structured request logging and request IDs. In a larger production setup, structured logs should be standardized across API instances and worker processes.

Recommended log fields:

| Field | Purpose |
|---|---|
| timestamp | Event ordering and incident analysis |
| level | Severity filtering |
| request_id | End-to-end request tracing |
| client_ip | Abuse analysis and support investigations |
| normalized_url | Cache key correlation and troubleshooting |
| route | API request grouping |
| http_status | Response classification |
| response_time_ms | Latency analysis |
| cache_status | Hit, miss, bypass |
| queue_job_id | Traceability between API and worker events |
| worker_id | Per-worker diagnosis |
| upstream_status | External website outcome |
| error_code | Stable operational classification |

Logging guidance:

- log one structured entry for each inbound API request
- log worker start and worker completion events
- log retry attempts with reason and retry count
- avoid logging full HTML payloads or sensitive data
- keep error codes stable so alerts and dashboards remain meaningful

## Metrics

The system should expose application and infrastructure metrics suitable for Prometheus scraping or equivalent collection.

Core metrics:

| Metric | Why It Matters |
|---|---|
| latency | Detect regressions in user-facing response time |
| requests/sec | Measure inbound demand and burst behavior |
| cache hit ratio | Confirm whether caching is reducing repeated work |
| error rate | Detect customer-visible reliability problems |
| CPU | Identify compute saturation on API or workers |
| memory | Detect leak patterns and unsafe growth |
| queue depth | Identify backlog before users feel severe delays |

Recommended metric breakdowns:

- API latency by route and status code
- worker job duration by outcome
- outbound fetch latency by target domain
- retry count by failure code
- dead-letter queue volume

## Dashboards

Grafana or an equivalent dashboarding tool should provide separate views for:

### Executive / SLA Dashboard

- request volume
- success rate
- p50, p95, and p99 latency
- current incident status

### API Operations Dashboard

- request rate
- 4xx and 5xx rates
- cache hit ratio
- rate-limit events
- CPU and memory per API instance

### Worker and Queue Dashboard

- queue depth
- oldest queued job age
- completed jobs per minute
- retry volume
- dead-letter queue count
- worker heartbeat / availability

### Upstream Dependency Dashboard

- fetch timeout rate
- DNS failure rate
- SSL failure rate
- non-HTML response rate
- domain concentration for failures

Grafana is useful because it allows these signals to be layered into incident-friendly views rather than requiring operators to correlate raw metrics manually.

## Alerts

Alerts should be actionable and prioritized. Example thresholds:

| Alert | Example Threshold | Response Goal |
|---|---|---|
| latency >2s | p95 API latency above 2 seconds for 10 minutes | Investigate degradation before SLA breach |
| error rate >5% | 5xx or actionable failure rate above 5% | Detect customer-visible instability |
| queue backlog | Queue depth or queue age exceeds expected envelope | Prevent delayed audits from compounding |
| worker crash | Missing worker heartbeat or crash-loop detection | Restore processing capacity quickly |
| cache unavailable | Redis health failures or hit ratio collapse | Avoid cascading latency issues |

Additional useful alerts:

- dead-letter queue receives more than a baseline threshold
- outbound timeout rate spikes on many domains
- API instance memory rises continuously
- deployment error rate rises immediately after release

Alert design principles:

- page only on signals that require human action
- route warnings separately from incidents
- include links to dashboards and logs in alert payloads

## Health Checks

### `/health` Endpoint

The current `/health` endpoint is appropriate as a lightweight liveness signal.

It should continue to answer:

- whether the service process is alive
- whether the application can accept basic traffic

### Readiness Probes

Readiness probes should answer whether an instance is ready to receive production traffic. For a scaled deployment, readiness should typically validate:

- application startup completed
- routing stack initialized
- dependency connectivity where required for serving safely

Readiness should fail if the instance cannot serve correctly, even if the process is technically running.

### Liveness Probes

Liveness probes should answer whether the process is stuck, deadlocked, or unrecoverable. Liveness should not depend on every downstream dependency, otherwise transient failures can trigger restart storms.

Recommended model:

- `/health` for basic service liveness
- separate readiness check for deploy/load balancer admission

## Deployment Strategy

### GitHub Actions

GitHub Actions should remain the CI gate for:

- backend dependency installation
- backend tests
- frontend type checks
- frontend tests

No production deployment should proceed without CI success.

### Automatic Deployments

Automatic deployments are appropriate for non-production or staging environments after CI passes. For production, automatic deployment is acceptable only when rollback risk is low and deployment verification is strong.

### Blue-Green Deployment

Blue-green deployment is appropriate when the team wants the clearest rollback path:

- deploy new version to idle environment
- run smoke checks
- switch traffic only after verification
- revert traffic instantly if issues appear

This is operationally simple to reason about during incidents.

### Canary Deployment

Canary deployment is appropriate when:

- risk of regression is moderate
- real traffic behavior matters more than pre-release testing alone
- the team wants gradual confidence-building

Recommended canary pattern:

1. send a small percentage of traffic to new API version
2. compare latency and error metrics
3. increase traffic gradually if stable
4. abort quickly on regression

## Rollback Plan

### Immediate Rollback

If a deployment causes elevated latency, increased failures, worker instability, or broken API behavior:

1. stop promotion
2. shift traffic back to the previous known-good version
3. preserve logs and metrics from the failed version
4. communicate incident status internally

Rollback should be an execution path, not an improvised decision.

### Deployment Verification

Before declaring a deployment successful, verify:

- `/health` returns success
- audit endpoint accepts valid requests
- frontend can communicate with backend
- error rates remain within baseline
- latency remains within expected range
- worker backlog does not rise abnormally

### Database Compatibility

Schema changes should be backward compatible whenever possible.

Recommended rules:

- expand before contract
- avoid destructive schema changes in the same release as dependent code
- ensure rollback-safe migrations
- test migrations separately from app code paths

This is especially important if PostgreSQL is introduced for persistent audit history.

### Post-Rollback Validation

After rollback:

1. confirm traffic is landing on the previous version
2. verify latency and error rates normalize
3. confirm queue and worker behavior recover
4. validate cache and database connectivity
5. create an incident summary and identify root cause before reattempting release

## Recommended Operational Baseline

For a credible production setup, Page Pulse should have:

- stable structured logs with request IDs
- dashboards for API, worker, queue, cache, and upstream failure signals
- alerting on latency, error rate, queue health, and cache health
- readiness and liveness separation
- CI-gated deployments
- rehearsed rollback procedures

These practices reduce mean time to detect, mean time to recover, and deployment risk as the system evolves beyond the assignment baseline.
