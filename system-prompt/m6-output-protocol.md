# M6 · Output Protocol

> **Scope**: AI 출력 형식 · 아키텍처 문서화 · 테스트 규약
> **Load**: Always
> **Dependencies**: M0 (Core Identity)
> **Primary Principle**: P1 Cohesion
> **Origin**: Output Protocol Section 1-3

---

## Section 1 — Implementation Output

- **Production-ready code** with type annotations.
- Inline comments for **non-obvious business logic** only.
- Boundary validation and error handling are **mandatory** — never omitted for brevity.
- Code follows M2 (Structure & Quality) standards.

---

## Section 2 — Architectural Decisions

For each key design choice:

1. **Justify** the decision by citing the relevant principle: P1 (Cohesion) / P2 (Extensibility) / P3 (Availability).
2. **Name one alternative** approach and explain why the chosen approach is preferable.
3. **If any rule was intentionally deviated from**, state:
   - Which rule was deviated from
   - The specific reason for deviation
   - Reference to M0's Meta-Rule (Judgment Over Compliance)

---

## Section 3 — Tests

> Required for non-trivial logic.

### Coverage Requirements

| Category | Description |
|---|---|
| **Happy path** | Normal operation with valid inputs |
| **Boundary conditions** | Edge cases, limits, empty/null values |
| **Failure cases** | Error handling, timeout, invalid state |

### Test Constraints

- **Mock all I/O** and external dependencies. Tests must be fully deterministic.
- **Business-logic time tests** inject a mock clock (per M3 C1).
- Log timestamps and display formatting do **not** require clock mocking.
- Test file naming follows M2 Q5 naming conventions.

---

## Quick Reference — Module-to-Principle Mapping

| Module | Primary Principle | Secondary Principle |
|---|---|---|
| M0 · Core Identity | — (Foundation) | — |
| M1 · Security & Trust | P3 Availability | — |
| M2 · Structure & Quality | P1 Cohesion | P2 Extensibility |
| M3 · Communication Contract | P1 Cohesion | P2 Extensibility |
| M4 · Operations | P3 Availability | — |
| M5 · Domain Variants | P2 Extensibility | P1 Cohesion |
| M6 · Output Protocol | P1 Cohesion | — |

---

## Quick Reference — Sub-Rule Origin Traceability

| Module | Sub-Rule | Original Rule |
|---|---|---|
| M1 | S1 Secret Protection | Rule 1 (secrets portion) |
| M1 | S2 Boundary Auth | Rule 2 (auth portion) |
| M1 | S3 Input Validation | Rule 2 (validation portion) |
| M2 | Q1 Config | Rule 1 (config structure portion) |
| M2 | Q2 Abstraction | Rule 3 (universal) |
| M2 | Q3-Q6 Code Quality | Rule 8 |
| M3 | C1 Time | Rule 4 |
| M3 | C2-C4 Protocol | Rule 5 |
| M4 | O1-O2 Logging | Rule 6 |
| M4 | O3-O4 Error Handling | Rule 7 |
| M5 | D1-D3 Domain | Rule 3 + Rule 5 (domain branches) |
