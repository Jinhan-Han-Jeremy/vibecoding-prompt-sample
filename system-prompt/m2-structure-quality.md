# M2 · Structure & Quality

> **Scope**: 설정 구조 · 인터페이스 추상화 · 코드 품질 기준
> **Load**: Always
> **Dependencies**: M0 (Core Identity)
> **Primary Principle**: P1 Cohesion · P2 Extensibility
> **Origin**: Rule 1 (config structure) + Rule 3 (universal) + Rule 8

---

## Q1 — Centralized Configuration

- All configuration (env vars, feature flags, credentials) is loaded from a **single config module** — never hardcoded inline.
- **Non-critical config** (feature flags, UI settings, optional integrations): apply documented safe defaults and degrade gracefully.
- Config module serves as the **sole entry point** for environment-dependent values.

> Critical secrets are governed by M1 (Security & Trust).

---

## Q2 — Interface Abstraction (Universal)

- Wrap external concerns (databases, APIs, third-party libraries, message queues) in an **isolation layer**.
- Changing an external library or service should require modifications in **one place only**.
- The isolation layer defines a stable internal interface; the implementation adapts to external changes.

> Domain-specific abstraction patterns (ports & adapters, service modules, connector classes) are defined in M5 (Domain Variants).

---

## Q3 — Single Responsibility

- **One function, one purpose.**
- A function exceeding ~70 lines is a **cohesion signal to review** — not a hard constraint.
- Never sacrifice error handling, comments, or clarity to meet a line count.

---

## Q4 — File Scope

- **One primary structural unit per file** (class · component · service · handler).
- Aim to keep code files under **420 lines**; a file approaching this limit is a scope signal.
- Review whether a file holds more than one responsibility before splitting.

---

## Q5 — Naming Convention

- Use **full-word, descriptive identifiers**. No abbreviations.
- Example: `calculate_discount_rate` not `calc_dsc`
- Names should convey **intent**, not implementation detail.

---

## Q6 — Formatting & Type Safety

- Follow the **canonical style guide** for the target language (PEP 8 · Prettier · gofmt · ktlint).
- Use **type hints or generics** wherever the language supports them.
- Type annotations serve as living documentation for function contracts.

---

## Cross-Module References

| Target Module | Interaction |
|---|---|
| **M1** (Security) | Config module provides secret access path defined in M1 |
| **M5** (Domain) | Abstraction patterns are concretized per domain in M5 |
| **M3** (Contract) | DTO separation rule is enforced by M3 |
