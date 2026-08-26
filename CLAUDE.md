# Claude project entry point

작업 전 다음 문서를 읽는다.

1. `AGENTS.md` — 데이터 불변 원칙과 검증 절차
2. `README.md` — 현재 수집 범위, schema, 실행법
3. `../law/docs/DESIGN.md` — 전체 연구 질문과 평가 설계
4. `../law/docs/DEVLOG.md` — 변경 이력과 결정 이유

핵심 주의사항:

- 현재 데이터는 공식 의결 기반 deterministic 초안이며 LLM variant가 아니다.
- artifact에 법적 쟁점이나 정답을 노출하지 않는다.
- rationale과 Gold rule을 모델 입력으로 주지 않는다.
- 공식 PDF를 retrieval corpus로 사용하지 않는다.
- `auto_draft`를 사람 검수 없이 최종 Gold로 간주하지 않는다.
- no_flag는 검토했으나 충족되지 않은 rule이 있어야 한다.

코드·문서·report 수치가 다르면 pipeline을 재실행해 실제 결과를 확인하고 관련 문서를 함께 갱신한다.
