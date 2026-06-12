# M1 · Security & Trust

> **Scope**: 인증/인가 · 비밀 보호 · 입력 경계 검증
> **Load**: Always
> **Dependencies**: M0 (Core Identity)
> **Primary Principle**: P3 Availability
> **Origin**: Rule 1 (secrets portion) + Rule 2

---

## S1 — Secret Protection

- Secrets (auth tokens, DB credentials, API keys, encryption keys) must **never** surface in:
  - Log output
  - Error responses returned to clients
  - Stack traces or debug dumps
  - Version-controlled files
- **Critical secrets** (auth secrets, DB connections, security keys): system must **fail at startup** if absent and unrecoverable.
- All secret access is routed through the centralized config module defined in M2.

---

## S2 — Boundary Authentication & Authorization

- Auth/authz checks execute **at the system boundary** — not distributed through business logic.
- Authentication verifies identity **before** any request reaches the domain layer.
- Authorization determines permission **before** any protected resource is accessed.

---

## S3 — Input Boundary Validation

- Malformed or invalid inputs are rejected with a **structured error** before entering the domain layer.
- Validation produces machine-readable error codes — not raw exception messages.
- Draft or temporary states (partially filled forms, unsaved records) belong to **UI/session state management**, not domain processing.

---

## Cross-Module References

| Target Module | Interaction |
|---|---|
| **M2** (Structure) | Secret access flows through M2's centralized config module |
| **M4** (Operations) | Log output must never contain secrets (M4 enforces masking) |
| **M3** (Contract) | Error payloads follow M3's structured error format |
