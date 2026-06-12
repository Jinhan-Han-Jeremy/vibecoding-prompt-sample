# Global Developer System Prompt · v4 — Modular Index

## Module Registry

| Module | File | Description | Required |
|---|---|---|---|
| M0 | `m0-core-identity.md` | 역할 · 메타규칙 · 설계 원칙 | ✅ Always |
| M1 | `m1-security-trust.md` | 인증 · 비밀 보호 · 경계 검증 | ✅ Always |
| M2 | `m2-structure-quality.md` | 설정 구조 · 추상화 · 코드 품질 | ✅ Always |
| M3 | `m3-communication-contract.md` | 시간 표준 · API 계약 · 프로토콜 | ✅ Always |
| M4 | `m4-operations.md` | 로깅 · 트레이싱 · 에러 핸들링 | ✅ Always |
| M5 | `m5-domain-variants.md` | 도메인별 변형 (Backend/Frontend/Data) | 🎯 Selective |
| M6 | `m6-output-protocol.md` | 출력 형식 · 테스트 규약 | ✅ Always |

---

## Composition Presets

### Full Stack (All Modules)
```
Load: M0 → M1 → M2 → M3 → M4 → M5(All) → M6
```

### Backend API
```
Load: M0 → M1 → M2 → M3 → M4 → M5.Backend → M6
```

### Frontend UI
```
Load: M0 → M1 → M2 → M3(Partial) → M4 → M5.Frontend → M6
```

### Data Engineering
```
Load: M0 → M1 → M2 → M3 → M4 → M5.Data → M6
```

### Code Review (Lightweight)
```
Load: M0 → M2 → M6
```

### Security Audit
```
Load: M0 → M1 → M4(Masking) → M6
```

---

## Load Order Rationale

1. **M0 first**: 모든 판단의 기준이 되는 원칙을 먼저 로드
2. **M1-M4 parallel**: 관심사별 독립 모듈 — 순서 무관
3. **M5 after M2,M3**: 도메인 변형은 구조/계약 규칙의 구체화이므로 후순위
4. **M6 last**: 출력 형식은 모든 규칙 적용 후 최종 검증 단계
