# Failure Analysis

This document identifies the three highest-risk production failures for Page Pulse, with emphasis on operational behavior in a scaled deployment.

Important context:

- The current implementation already handles many request-level failures gracefully, including invalid URLs, timeouts, DNS failures, SSL failures, redirect issues, non-HTML responses, and oversized pages.
- The risks below focus on production-service reliability rather than only request-level correctness.

## Failure 1: External Website Timeout or Unresponsive Upstream

### Failure

A target website is slow, partially unavailable, or stalls during connection, redirect, or content download.

### Impact

- User-facing requests become slow if handled synchronously
- Worker throughput drops when many jobs target slow websites
- Queue backlog can grow during spikes
- Error rates increase if timeouts exceed retry budgets

This is the most fundamental risk in Page Pulse because the product depends on third-party websites that are outside the system's control.

### Detection

Primary signals:

- rising upstream fetch latency
- increased timeout error count
- worker job duration growth
- elevated queue depth
- increased p95 and p99 API latency

Useful log indicators:

- request ID frequency for `FETCH_TIMEOUT`
- concentration of failures by domain
- repeated retries against the same hostname

### Mitigation

- enforce strict outbound timeouts
- cap maximum redirects
- cap maximum response size
- isolate fetch work in workers rather than API request threads
- apply bounded retries only for transient failures
- cache recent successful results to reduce repeated upstream fetches

Fallback behavior:

- return a structured timeout response
- avoid indefinite blocking
- avoid crashing the API process

### Recovery

Recovery is usually automatic:

1. timeout occurs
2. job is marked failed or retried according to policy
3. healthy requests continue for other URLs
4. cached results serve repeated requests if available

If a specific external domain remains unstable, the operational response may include temporary retry reduction or domain-level throttling to protect worker capacity.

## Failure 2: Redis Cache Failure or Degraded Cache Availability

### Failure

Redis becomes unavailable, experiences elevated latency, or serves errors due to memory pressure, network partition, or node failure.

### Impact

- cache hit ratio drops sharply
- duplicate audits increase
- API latency rises because more requests fall through to execution paths
- rate-limiting accuracy may degrade if rate-limit counters depend on Redis
- queue load increases because repeated URLs cannot be short-circuited

Cache failure may not cause immediate total outage, but it can create a cascading performance problem.

### Detection

Primary signals:

- Redis health check failures
- cache connection errors in logs
- sudden drop in cache hit ratio
- rising queue ingress rate without matching user growth
- increased API response latency

Operational indicators:

- elevated connection timeout logs to Redis
- higher CPU across API and worker fleets due to reduced reuse

### Mitigation

- treat Redis as an optimization layer, not the sole source of truth
- keep API nodes stateless and capable of operating without cache hits
- preserve durable records in PostgreSQL
- enforce graceful fallback behavior when cache lookup fails
- alert aggressively on cache unavailability

Fallback behavior:

- continue serving requests through queue + worker execution
- skip cache reads/writes temporarily
- degrade performance rather than correctness

### Recovery

Recovery steps:

1. restore Redis service health
2. confirm connectivity from API and worker nodes
3. observe cache hit ratio recovery
4. verify queue depth stabilizes
5. verify API latency returns toward baseline

No manual data reconstruction should be required for short-lived cache keys, but rate-limit counters and hot-result caches will naturally warm back up over time.

## Failure 3: Queue Backlog Growth or Worker Crash

### Failure

Workers stop consuming jobs efficiently due to crashes, resource starvation, bad deployments, upstream slowness, or message broker disruption.

### Impact

- pending audits accumulate
- perceived product responsiveness degrades
- synchronous fallback paths may become overloaded
- retries can amplify the backlog if not bounded
- customer-facing SLA is threatened even though the API may still respond

This is one of the most important production risks once the system adopts asynchronous execution.

### Detection

Primary signals:

- queue depth rising continuously
- queue age increasing
- worker heartbeat failures
- lower completed-jobs-per-minute
- more dead-letter queue entries

Secondary signals:

- support complaints about slow result delivery
- elevated timeout rates on job completion polling
- increased deploy-to-incident correlation after worker releases

### Mitigation

- maintain worker health checks and heartbeat monitoring
- autoscale worker count based on queue depth and processing latency
- isolate worker resource classes from API resource classes
- use dead-letter queues for repeatedly failing jobs
- use bounded retries with exponential backoff
- support safe worker restarts without losing acknowledged work semantics

Fallback behavior:

- continue accepting requests if queue durability remains healthy
- return clear in-progress or temporarily delayed responses if asynchronous UX is exposed
- prioritize system stability over attempting unlimited catch-up

### Recovery

Recovery steps:

1. identify whether the issue is worker capacity, crash loop, queue broker health, or upstream slowdown
2. restore worker service or rollback the worker deployment
3. scale workers horizontally if the issue is backlog pressure
4. drain dead-letter or stuck jobs selectively after root cause validation
5. verify queue age, throughput, and success rate return to normal

If backlog clearance will take significant time, communication and temporary product messaging become part of the operational response.

## Operational Fallback Summary

| Failure | Preferred Fallback | Goal |
|---|---|---|
| External website timeout | Return structured timeout error, preserve platform health | Prevent tail-latency collapse |
| Redis failure | Bypass cache, continue with slower execution path | Preserve correctness |
| Queue backlog / worker crash | Restore workers, scale capacity, use retries + DLQ | Preserve throughput and recover predictably |

## Why These Three Failures Matter Most

These are the highest-risk failures because they attack the system's three most important reliability boundaries:

1. third-party dependency reliability
2. shared performance infrastructure
3. background execution capacity

Together, they determine whether Page Pulse can maintain predictable user experience during real-world traffic and upstream instability.
