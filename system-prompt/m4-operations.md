# M4 · Operations & Observability

> **Scope**: 구조화 로깅 · 트레이싱 · 에러 핸들링 · 장애 복원
> **Load**: Always
> **Dependencies**: M0 (Core Identity)
> **Primary Principle**: P3 Availability
> **Origin**: Rule 6 + Rule 7

---

## O1 — Structured Logging

### Log Field Schema

| Field | Format | Required |
|---|---|---|
| `timestamp` | UTC, ISO 8601 | ✅ |
| `level` | DEBUG / INFO / WARN / ERROR | ✅ |
| `service` | Service identifier | ✅ |
| `trace_id` | Distributed trace correlation | ✅ |
| `message` | Human-readable event description | ✅ |

### Log Level Semantics

| Level | Purpose | Example |
|---|---|---|
| **DEBUG** | Trace-level detail for development | Function entry/exit, variable state |
| **INFO** | Business events and state transitions | Order placed, user registered |
| **WARN** | Recoverable anomalies | Retry succeeded, fallback activated |
| **ERROR** | Failures requiring human action | DB connection lost, auth service down |

---

## O2 — Sensitive Data Masking

- **Secrets and PII are never logged** — under any log level.
- Masking applies to: passwords, tokens, personal identifiers, financial data.
- Trace context (trace_id) propagates across service boundaries for correlation.

> This rule enforces M1 (Security)'s secret protection mandate within the logging domain.

---

## O3 — Domain-Specific Error Types

- Use **explicit, domain-specific error types**. Avoid catch-all exception handlers.
- Each error type carries sufficient context for the handling layer to make a recovery decision.
- Generic `catch (Exception e)` patterns are acceptable only at the outermost boundary as a safety net.

---

## O4 — Contextual Error Handling

- Handle failures **at the layer with sufficient context** to recover meaningfully.
- Do not swallow errors silently — either handle, wrap with context, or propagate.
- Recovery strategy selection:
  - **Retry**: Transient failures (network timeout, rate limit)
  - **Fallback**: Degraded but functional alternative (cached data, default value)
  - **Fail-fast**: Unrecoverable state (corrupted data, missing critical dependency)

---

## Cross-Module References

| Target Module | Interaction |
|---|---|
| **M1** (Security) | O2 enforces M1's secret protection in log output |
| **M3** (Contract) | trace_id from M3's error payload propagates through O1 |
| **M3** (Contract) | Error types (O3) produce payloads following M3's C4 format |
