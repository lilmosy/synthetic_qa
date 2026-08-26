# Agent instructions

이 파일은 `PROJECTS/synthetic_data` 전체에 적용된다. 작업 전 `README.md`를 읽는다. 연구 방법이나 법령 DB 변경과 연결되는 작업이면 `../law/docs/DESIGN.md`, `../law/docs/DEVLOG.md`, `../law/AGENTS.md`도 읽는다.

## 프로젝트 범위

- 공식 의결 PDF를 방송 전 검토 QA로 변환한다.
- source provenance, 중복 통합, rule mapping, validation을 담당한다.
- 법령 parser, LLM compiler, Wiki, baseline retrieval은 `../law`의 책임이다.
- 현재는 LLM variant를 생성하지 않는다.

## Source of truth

- 원본: `data/raw/decisions/official/*.pdf`
- 수집 목록: `configs/decision_sources.yaml`
- 수동 annotation: `configs/qa_overrides.yaml`
- 공통 질문/label: `configs/schema.yaml`
- rule 검증 입력: `data/reference/legal_corpus.jsonl`
- link 구조 입력: `data/reference/explicit_edges.jsonl`
- 생성물: `data/processed/*`

PDF와 reference snapshot을 자동으로 수정하지 않는다. 생성된 QA를 직접 대량 편집하기보다 parser 또는 override를 수정하고 재생성한다.

## 데이터 품질 불변 원칙

1. artifact는 장면·대사·자막의 사실관계만 담는다.
2. artifact/question에 법적 쟁점, 조문 번호, 위반 결론을 노출하지 않는다.
3. rationale과 Gold rule은 모델 초기 입력에 포함하지 않는다.
4. 공식 의결 결과를 `official_result`에 보존한다.
5. `no_flag`도 검토 rule을 가져야 하며, 요건 불충족이면 `considered_not_triggered`로 기록한다.
6. 사람이 Gold를 보완한 경우 `manual_seed`로 표시한다.
7. 방송 후 수정·추가자료에 의존하는 사례는 현재 benchmark에서 제외한다.
8. 동일 콘텐츠·rule set·결과의 다채널 의결은 하나로 통합하고 모든 `decision_ids`와 source를 보존한다.
9. 공식 의결 PDF를 retrieval corpus로 사용하지 않는다.
10. `auto_draft`는 사람 검수 전 최종 Gold가 아니다.

## 현재 기준과 한계

- PDF 37개
- 원시 의결행 324개
- 독립 QA 205개
- `review_required` 204개
- `no_flag` 1개
- single page 184개
- multi-page unlinked 21개

204:1 불균형을 숨기지 않는다. 이 상태에서 label accuracy를 주요 성능으로 보고하지 않는다. 충분한 no_flag를 확보하기 전에는 rule retrieval 평가를 우선한다.

`evidence_structure`는 page 수와 explicit edge로 계산할 뿐, 순차적 재검색 필요성을 자동 판정하지 않는다. “A를 읽어야 B의 검색어가 생기는가”는 사람 검수가 필요하다.

## Reference snapshot 갱신

`../law/data/processed/legal_corpus.jsonl` 또는 `explicit_edges.jsonl`이 바뀌었다고 자동 복사하지 않는다. 다음을 함께 확인한 뒤 명시적으로 갱신한다.

- 기존 Gold rule ID가 모두 존재하는가
- 새 corpus version에서 QA 의미가 바뀌지 않았는가
- report의 validation이 통과하는가
- corpus freeze 전 변경인가

갱신 사실과 이유를 `../law/docs/DEVLOG.md`에 남긴다.

## 실행과 검증

```bash
python src/run_qa_pipeline.py
```

현재 기대 결과:

```text
synthetic_qa: 205 independent cases
sources: 37 official PDFs
validation: PASS
```

생성 후 반드시 확인한다.

- invalid rule/source ID 0
- 빈 artifact/rationale 0
- duplicate QA ID 없음
- invalid label 없음
- PDF source 37개가 report의 `sources`에 존재
- 별도 `manifest.jsonl`이 생성되지 않음

별도 `tests/` 폴더 대신 현재는 builder의 `--validate`를 사용한다. 검증이 복잡해지면 그때 tests 도입을 다시 결정한다.

## 문서 유지

- schema·수집 범위·분포가 바뀌면 `README.md`를 갱신한다.
- 중요한 데이터 결정은 `../law/docs/DEVLOG.md`에 날짜와 이유를 기록한다.
- 전체 연구 설계는 `../law/docs/DESIGN.md`에만 기록하고 이 프로젝트에 중복 복사하지 않는다.

## 금지

- test 성능을 본 뒤 실패 사례의 rule만 reference corpus에 추가하지 않는다.
- 빈 rule 배열의 no_flag를 평가 가능 사례로 포함하지 않는다.
- 임의의 LLM rationale을 공식 Gold처럼 저장하지 않는다.
- 의결번호 단위로 무작위 분할해 같은 콘텐츠를 train/test에 동시에 넣지 않는다.
- PDF 추출 오류를 QA JSONL에서만 임시 수정하지 않는다. word repair 또는 override로 재현 가능하게 처리한다.
