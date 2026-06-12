# M5 · Domain Variants

> **Scope**: M2/M3의 유니버설 규칙을 도메인별로 구체화
> **Load**: Selective (프로젝트 도메인에 따라 해당 섹션만 로드)
> **Dependencies**: M2 (Structure & Quality) · M3 (Communication Contract)
> **Primary Principle**: P2 Extensibility · P1 Cohesion
> **Origin**: Rule 3 (domain branches) + Rule 5 (domain branches)

---

## D1 — Backend / API

### Abstraction Pattern: Ports & Adapters

- M2의 인터페이스 추상화를 **Ports & Adapters (Hexagonal)** 패턴으로 구현.
- **Port**: 도메인이 정의하는 인터페이스 (repository, gateway)
- **Adapter**: 외부 시스템에 대한 구현체 (PostgresRepository, StripeGateway)
- 어댑터 교체 시 포트 인터페이스는 변경 없음.

### Response Envelope

- M3의 서버 응답 봉투 `{ status, data, error, meta }`를 그대로 적용.
- REST API는 HTTP status code와 봉투의 `status` 필드를 일치시킴.
- GraphQL은 봉투를 `data`/`errors` 스키마에 맞게 적응.

---

## D2 — Frontend / Mobile

### Abstraction Pattern: Service Modules

- M2의 인터페이스 추상화를 **dedicated service or API-client modules**로 구현.
- 각 외부 API 또는 데이터 소스에 대해 하나의 서비스 모듈을 생성.
- 컴포넌트는 서비스 모듈을 통해서만 외부 데이터에 접근.

### Intra-Frontend Data Flow

- M3의 응답 봉투 구조는 **서버 통신에만** 적용.
- 컴포넌트 간 데이터 전달은 **프레임워크의 관용적 패턴**을 따름:
  - React: Props, Context, State
  - Vue: Props, Provide/Inject, Pinia/Vuex
  - Angular: Input/Output, Services, RxJS
- 프레임워크 패턴을 봉투 구조로 강제하지 않음.

---

## D3 — Data Engineering / ML Pipelines

### Abstraction Pattern: Source/Sink Connectors

- M2의 인터페이스 추상화를 **abstract source/sink connector classes**로 구현.
- **Source Connector**: 데이터 읽기 인터페이스 (S3Source, KafkaSource, DBSource)
- **Sink Connector**: 데이터 쓰기 인터페이스 (S3Sink, BigQuerySink, PubSubSink)
- 파이프라인 로직은 커넥터 인터페이스에만 의존, 구현체에 의존하지 않음.

### Data Contract

- M3의 계약 타이핑을 **스키마 레지스트리** 또는 **데이터 계약 파일**로 구현.
- 스키마 버전 관리는 M3의 C2 규칙(명시적 타입 + 버전)을 따름.

---

## Cross-Module References

| Target Module | Interaction |
|---|---|
| **M2** (Structure) | 각 도메인의 추상화 패턴은 M2 Q2의 구체화 |
| **M3** (Contract) | 응답 봉투와 계약 타이핑의 도메인별 적응 |
