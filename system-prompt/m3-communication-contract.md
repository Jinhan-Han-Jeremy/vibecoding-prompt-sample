# M3 · Communication Contract

> **Scope**: 시간 표준 · API 계약 · 직렬화 · 에러 페이로드
> **Load**: Always
> **Dependencies**: M0 (Core Identity)
> **Primary Principle**: P1 Cohesion · P2 Extensibility
> **Origin**: Rule 4 + Rule 5 (universal portions)

---

## C1 — Deterministic Time

**Scope**: stored timestamps · cross-service event ordering · scheduling · audit trails

- Use **UTC + ISO 8601 / RFC 3339** for any timestamp that crosses a process boundary or is persisted.
- Inject a clock dependency **only when time affects business logic or stored state**.
- Logging timestamps, display formatting, and transient utility calculations may use platform time directly.

---

## C2 — Cross-Service Contract Typing

- Cross-service and external API contracts are **explicitly typed and versioned**.
- DTOs (Data Transfer Objects) are **separate from domain models**.
- Internal domain objects must not be leaked into external responses.

---

## C3 — Server Response Envelope

**Scope**: network-boundary API responses only

```
{ status, data, error, meta }
```

- This envelope applies to **server-sent API responses only**.
- Intra-frontend data flow (Props, Context, local state, component bindings) follows **idiomatic framework conventions** and must not be forced into this structure.

> Frontend-specific data flow conventions are defined in M5 (Domain Variants).

---

## C4 — Structured Error Payload

Error payloads must carry:

| Field | Purpose |
|---|---|
| `code` | Machine-readable error identifier |
| `message` | Human-readable description |
| `trace_id` | Distributed tracing correlation ID |

- Error format is consistent across all service boundaries.
- M1's boundary validation errors follow this same format.

---

## Cross-Module References

| Target Module | Interaction |
|---|---|
| **M1** (Security) | Boundary validation errors use C4 error format |
| **M4** (Operations) | trace_id propagates through M4's observability system |
| **M5** (Domain) | Response envelope (C3) has domain-specific adaptations in M5 |
