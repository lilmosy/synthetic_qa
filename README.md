# 방송심의 Synthetic QA

방송통신심의위원회 공식 월별 의결 PDF를 방송 전 규정 검토 QA로 재구성하는 프로젝트다. 법령 DB·LLMWiki 구현은 sibling [`../law`](../law/README.md)가 담당한다.

현재 데이터는 LLM이 만든 variant가 아니라 공식 의결문을 deterministic하게 파싱·중복 통합해 만든 1차 초안이다.

## 현재 상태

2026-08-27 기준:

| 항목 | 수량 |
|---|---:|
| 공식 PDF | 37개 |
| 파싱한 의결행 | 324개 |
| 적재 규정과 연결된 의결행 | 302개 |
| 동일 콘텐츠 중복 통합 | 97개 |
| 독립 QA 초안 | 205개 |
| 제외 의결행 | 22개 |

QA 분포:

| 구분 | 수량 |
|---|---:|
| `broadcast_program` | 117 |
| `broadcast_ad` | 37 |
| `product_sales` | 51 |
| `single_page` | 184 |
| `multi_page_unlinked` | 21 |
| `review_required` | 204 |
| `no_flag` | 1 |

중요: 205개는 최종 Gold가 아니라 `draft_requires_human_review` 상태다. 특히 204:1 label 불균형 때문에 현재 데이터만으로 compliance screening accuracy를 평가하면 안 된다.

## 수집 범위

- 2025년 1~4월: 지상파, 종합편성·보도전문, 전문편성, 방송광고, 상품판매방송
- 2026년 4~6월: 동일 5개 계열
- 2026년 7월: 지상파·상품판매방송 공개분

PDF별 공식 게시글 URL, 파일명, SHA-256, 페이지 수는 `synthetic_qa_report.json`의 `sources`에 저장한다. 별도 manifest 파일은 사용하지 않는다.

## 디렉터리

```text
synthetic_data/
├── configs/
│   ├── schema.yaml
│   ├── decision_sources.yaml
│   └── qa_overrides.yaml
├── data/
│   ├── raw/decisions/official/        # 공식 PDF 37개
│   ├── reference/
│   │   ├── legal_corpus.jsonl         # rule ID 검증용 snapshot
│   │   └── explicit_edges.jsonl       # evidence 구조 판별용 snapshot
│   └── processed/
│       ├── synthetic_qa.jsonl
│       ├── synthetic_qa_report.json
│       └── synthetic_qa_summary.md
├── src/
│   ├── build_qa.py
│   ├── common.py
│   └── run_qa_pipeline.py
├── AGENTS.md
└── CLAUDE.md
```

### 사람이 관리하는 입력

- `configs/decision_sources.yaml`: 수집 대상 PDF와 공식 게시글 정보
- `configs/qa_overrides.yaml`: 사람이 검토·보완한 사례
- `configs/schema.yaml`: 공통 질문과 outcome label
- `data/raw/decisions/official/*.pdf`: 원본 공식 의결자료
- `data/reference/*.jsonl`: `law`에서 복사한 versioned input snapshot

### 자동 생성 산출물

- `synthetic_qa.jsonl`: 모델 평가용 QA 초안
- `synthetic_qa_report.json`: source metadata, 분포, 제외 사유, validation
- `synthetic_qa_summary.md`: 교수·검수자가 읽는 표 형태 요약

## 재생성

```bash
cd /Users/SoyoungCho/Downloads/yozm_ai_agent/PROJECTS/synthetic_data
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/run_qa_pipeline.py
```

현재 기대 결과:

```text
synthetic_qa: 205 independent cases
sources: 37 official PDFs
validation: PASS
```

## 생성 과정

```text
decision_sources.yaml + 공식 PDF
  ↓ source metadata와 SHA-256 계산
PDF별 의결행 파싱
  ↓
방송 내용 / 공식 결과 / 관련조항 추출
  ↓ reference corpus로 rule ID 검증
방송 전 artifact와 Gold 구성
  ↓
동일 콘텐츠·rule set·결과 중복 통합
  ↓
synthetic_qa.jsonl + report + summary
```

현재 LLM 호출은 없다.

## QA 스키마

```json
{
  "qa_id": "QA_<stable_hash>",
  "decision_ids": ["2026-광고-04-0044"],
  "source": [
    {"source_id": "KOCSC_2026_05_BROADCAST_AD", "pages": [1]}
  ],
  "artifact": {
    "domain": "broadcast_ad",
    "text": "방송 전에 검토할 장면·대사·자막의 중립적 재구성"
  },
  "question": "다음 제작물을 방송 전에 검토하라...",
  "evidence_structure": "single_page",
  "gold": {
    "screening_label": "review_required",
    "severity": "administrative_guidance",
    "official_result": "권고",
    "rules": [
      {"rule_id": "AD_REVIEW_ART23_P2_I1", "application": "triggered"}
    ],
    "rationale": "공식 의결문을 바탕으로 한 정답 해설"
  },
  "review_status": "auto_draft"
}
```

### 필드 의미

| 필드 | 의미 |
|---|---|
| `qa_id` | artifact·rule set·결과 기반 stable ID |
| `decision_ids` | 동일 콘텐츠를 통합하기 전 공식 의결번호들 |
| `source` | 공식 PDF 식별자와 페이지 |
| `artifact` | 모델에게 실제로 주는 방송 전 사실관계 |
| `question` | 모든 사례에 공통으로 사용하는 중립 질문 |
| `evidence_structure` | 필요한 조문 page의 현재 연결 구조 |
| `screening_label` | `no_flag` 또는 `review_required` |
| `severity` | none/administrative guidance/statutory sanction |
| `official_result` | 방심위 원 의결 결과 |
| `rules` | 검색해야 할 Gold rule과 적용 여부 |
| `rationale` | 모델에게 주지 않는 Gold 해설 |
| `review_status` | 자동 초안인지 사람이 보완한 seed인지 |

## 결과 label

```text
문제없음             → no_flag / none
의견제시·권고        → review_required / administrative_guidance
주의·경고·그 이상   → review_required / statutory_sanction
```

이는 공식 결과를 지우는 변환이 아니다. 원 결과는 `official_result`에 보존한다. `review_required`도 최종 위법 확정이 아니라 방송 전 수정·전문 검토가 필요한 위험 신호다.

## `manual_seed`

문제없음 사례도 “무슨 조항을 검토했으나 왜 충족되지 않았는지”가 있어야 retrieval 평가가 가능하다. Gold rule이 빈 배열이면 아무 규정도 찾지 않은 모델이 우연히 정답을 맞힐 수 있다.

현재 no_flag 1개는 사람이 검토 조항을 연결했고 다음처럼 저장한다.

```json
{
  "application": "considered_not_triggered",
  "review_status": "manual_seed"
}
```

`manual_seed`는 법적 결과가 아니라 annotation provenance다.

## 제외 기준

- 적재 corpus에서 Gold rule을 찾을 수 없음
- 방송 후 추가 제출자료·사후 수정에 판단이 의존함
- PDF 내부 의결번호 중복
- 내용이나 artifact 추출 실패
- 수동 rule ID가 reference corpus에 없음

## 검수 원칙

1. artifact에 조문 번호·법적 쟁점·위반 결론을 넣지 않는다.
2. rationale이나 official result를 모델 입력으로 주지 않는다.
3. rationale이 artifact에 없는 사실을 만들지 않는지 확인한다.
4. 실제 방송 전 제작 상황으로 성립하는지 확인한다.
5. Gold rule과 공식 PDF 원문을 대조한다.
6. 동일 콘텐츠가 train/test에 동시에 들어가지 않도록 향후 `case group`으로 분할한다.
7. `auto_draft`를 사람 검수 없이 최종 Gold로 공개하지 않는다.

## 전체 연구와의 관계

이 데이터는 `law`의 BM25/Dense/Graph/LLMWiki를 동일 조건에서 평가하는 benchmark가 된다. 공식 의결 PDF 자체는 검색 corpus가 아니며, retrieval 방법에는 `artifact`와 법령 DB만 제공한다.

전체 연구 질문과 baseline 설계는 [`../law/docs/DESIGN.md`](../law/docs/DESIGN.md)를 참조한다.
