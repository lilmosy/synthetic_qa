# Synthetic QA 1차 빌드 요약

방송통신심의위원회 공식 월별 의결 PDF를 규정 기반 방송 전 검토 QA로 결정적으로 변환한 초안이다.
모든 QA는 원문 대조 검수 전 `auto_draft`이며, `manual_seed`는 문제없음 경계 사례 1건이다.

## 전체 수량

- 공식 PDF: 37개
- 파싱한 의결행: 324개
- 적재 규정에 매핑된 의결행: 302개
- 동일 콘텐츠·다채널 중복 통합: 97개
- 최종 독립 QA 초안: 205개
- 제외 의결행: 22개

## QA 분포

| 구분 | 값 | 수량 |
|---|---|---:|
| official_result | 경고 | 1 |
| official_result | 권고 | 123 |
| official_result | 문제없음 | 1 |
| official_result | 의견제시 | 45 |
| official_result | 주의 | 35 |
| screening_label | no_flag | 1 |
| screening_label | review_required | 204 |
| severity | administrative_guidance | 168 |
| severity | none | 1 |
| severity | statutory_sanction | 36 |
| domain | broadcast_ad | 37 |
| domain | broadcast_program | 117 |
| domain | product_sales | 51 |
| evidence_structure | multi_page_unlinked | 21 |
| evidence_structure | single_page | 184 |

## 공식 PDF별 수량

`독립 QA`는 동일 광고·프로그램이 여러 채널에서 의결된 경우 하나로 합친 뒤의 수량이다.

| 기간 | 계열 | 공식 출처 | 의결행 | 포함행 | 독립 QA | 제외 |
|---|---|---|---:|---:|---:|---:|
| 2025-01 | 방송광고 | [2025년 1월 방송광고 심의의결 현황](https://www.kocsc.or.kr/main/cop/bbs/selectBoardArticle.do?bbsId=info_Opinion_main&nttId=20662&menuNo=040000&subMenuNo=040700) | 28 | 28 | 3 | 0 |
| 2025-01 | 종합편성·보도전문 | [2025년 1월 종합편성·보도전문채널 심의의결 현황](https://www.kocsc.or.kr/main/cop/bbs/selectBoardArticle.do?bbsId=info_Opinion_main&nttId=20727&menuNo=040000&subMenuNo=040700) | 5 | 5 | 1 | 0 |
| 2025-01 | 상품판매방송 | [2025년 1월 상품판매방송 심의의결 현황](https://www.kocsc.or.kr/main/cop/bbs/selectBoardArticle.do?bbsId=info_Opinion_main&nttId=20684&menuNo=040000&subMenuNo=040700) | 4 | 4 | 4 | 0 |
| 2025-01 | 전문편성 | [2025년 1월 전문편성채널 심의의결 현황](https://www.kocsc.or.kr/main/cop/bbs/selectBoardArticle.do?bbsId=info_Opinion_main&nttId=20675&menuNo=040000&subMenuNo=040700) | 2 | 2 | 2 | 0 |
| 2025-01 | 지상파방송 | [2025년 1월 지상파방송 심의의결 현황](https://www.kocsc.or.kr/main/cop/bbs/selectBoardArticle.do?bbsId=info_Opinion_main&nttId=20672&menuNo=040000&subMenuNo=040700) | 9 | 9 | 9 | 0 |
| 2025-02 | 방송광고 | [2025년 2월 방송광고 심의의결 현황](https://www.kocsc.or.kr/main/cop/bbs/selectBoardArticle.do?bbsId=info_Opinion_main&nttId=20740&menuNo=040000&subMenuNo=040700) | 12 | 12 | 3 | 0 |
| 2025-02 | 종합편성·보도전문 | [2025년 2월 종합편성·보도전문채널 심의의결 현황](https://www.kocsc.or.kr/main/cop/bbs/selectBoardArticle.do?bbsId=info_Opinion_main&nttId=20833&menuNo=040000&subMenuNo=040700) | 7 | 6 | 6 | 1 |
| 2025-02 | 상품판매방송 | [2025년 2월 상품판매방송 심의의결 현황](https://www.kocsc.or.kr/main/cop/bbs/selectBoardArticle.do?bbsId=info_Opinion_main&nttId=20742&menuNo=040000&subMenuNo=040700) | 7 | 7 | 7 | 0 |
| 2025-02 | 전문편성 | [2025년 2월 전문편성채널 심의의결 현황](https://www.kocsc.or.kr/main/cop/bbs/selectBoardArticle.do?bbsId=info_Opinion_main&nttId=20744&menuNo=040000&subMenuNo=040700) | 4 | 4 | 2 | 0 |
| 2025-02 | 지상파방송 | [2025년 2월 지상파방송 심의의결 현황](https://www.kocsc.or.kr/main/cop/bbs/selectBoardArticle.do?bbsId=info_Opinion_main&nttId=20725&menuNo=040000&subMenuNo=040700) | 9 | 8 | 8 | 1 |
| 2025-03 | 방송광고 | [2025년 3월 방송광고 심의의결 현황](https://www.kocsc.or.kr/main/cop/bbs/selectBoardArticle.do?bbsId=info_Opinion_main&nttId=20808&menuNo=040000&subMenuNo=040700) | 8 | 8 | 5 | 0 |
| 2025-03 | 종합편성·보도전문 | [2025년 3월 종합편성·보도전문채널 심의의결 현황](https://www.kocsc.or.kr/main/cop/bbs/selectBoardArticle.do?bbsId=info_Opinion_main&nttId=20834&menuNo=040000&subMenuNo=040700) | 7 | 6 | 6 | 1 |
| 2025-03 | 상품판매방송 | [2025년 3월 상품판매방송 심의의결 현황](https://www.kocsc.or.kr/main/cop/bbs/selectBoardArticle.do?bbsId=info_Opinion_main&nttId=20814&menuNo=040000&subMenuNo=040700) | 8 | 8 | 8 | 0 |
| 2025-03 | 전문편성 | [2025년 3월 전문편성채널 심의의결 현황](https://www.kocsc.or.kr/main/cop/bbs/selectBoardArticle.do?bbsId=info_Opinion_main&nttId=20824&menuNo=040000&subMenuNo=040700) | 5 | 2 | 2 | 3 |
| 2025-03 | 지상파방송 | [2025년 3월 지상파방송 심의의결 현황](https://www.kocsc.or.kr/main/cop/bbs/selectBoardArticle.do?bbsId=info_Opinion_main&nttId=20827&menuNo=040000&subMenuNo=040700) | 19 | 18 | 18 | 1 |
| 2025-04 | 방송광고 | [2025년 4월 방송광고 심의의결 현황](https://www.kocsc.or.kr/main/cop/bbs/selectBoardArticle.do?bbsId=info_Opinion_main&nttId=20900&menuNo=040000&subMenuNo=040700) | 10 | 10 | 4 | 0 |
| 2025-04 | 종합편성·보도전문 | [2025년 4월 종합편성·보도전문채널 심의의결 현황](https://www.kocsc.or.kr/main/cop/bbs/selectBoardArticle.do?bbsId=info_Opinion_main&nttId=21208&menuNo=040000&subMenuNo=040700) | 3 | 2 | 2 | 1 |
| 2025-04 | 상품판매방송 | [2025년 4월 상품판매방송 심의의결 현황](https://www.kocsc.or.kr/main/cop/bbs/selectBoardArticle.do?bbsId=info_Opinion_main&nttId=21038&menuNo=040000&subMenuNo=040700) | 3 | 3 | 3 | 0 |
| 2025-04 | 전문편성 | [2025년 4월 전문편성채널 심의의결 현황](https://www.kocsc.or.kr/main/cop/bbs/selectBoardArticle.do?bbsId=info_Opinion_main&nttId=21009&menuNo=040000&subMenuNo=040700) | 4 | 4 | 4 | 0 |
| 2025-04 | 지상파방송 | [2025년 4월 지상파방송 심의의결 현황](https://www.kocsc.or.kr/main/cop/bbs/selectBoardArticle.do?bbsId=info_Opinion_main&nttId=20886&menuNo=040000&subMenuNo=040700) | 11 | 4 | 2 | 7 |
| 2026-04 | 방송광고 | [2026년 4월 방송광고 심의의결 현황](https://www.kocsc.or.kr/main/cop/bbs/selectBoardArticle.do?bbsId=info_Opinion_main&nttId=21249&menuNo=040000&subMenuNo=040700) | 18 | 18 | 4 | 0 |
| 2026-04 | 종합편성·보도전문 | [2026년 4월 종합편성·보도전문채널 심의의결 현황](https://www.kocsc.or.kr/main/cop/bbs/selectBoardArticle.do?bbsId=info_Opinion_main&nttId=21209&menuNo=040000&subMenuNo=040700) | 4 | 4 | 4 | 0 |
| 2026-04 | 상품판매방송 | [2026년 4월 상품판매방송 심의의결 현황](https://www.kocsc.or.kr/main/cop/bbs/selectBoardArticle.do?bbsId=info_Opinion_main&nttId=21223&menuNo=040000&subMenuNo=040700) | 2 | 2 | 2 | 0 |
| 2026-04 | 전문편성 | [2026년 4월 전문편성채널 심의의결 현황](https://www.kocsc.or.kr/main/cop/bbs/selectBoardArticle.do?bbsId=info_Opinion_main&nttId=21222&menuNo=040000&subMenuNo=040700) | 2 | 2 | 1 | 0 |
| 2026-04 | 지상파방송 | [2026년 4월 지상파방송 심의의결 현황](https://www.kocsc.or.kr/main/cop/bbs/selectBoardArticle.do?bbsId=info_Opinion_main&nttId=21211&menuNo=040000&subMenuNo=040700) | 2 | 2 | 2 | 0 |
| 2026-05 | 방송광고 | [2026년 5월 방송광고 심의의결 현황](https://www.kocsc.or.kr/main/cop/bbs/selectBoardArticle.do?bbsId=info_Opinion_main&nttId=21294&menuNo=040000&subMenuNo=040700) | 26 | 26 | 8 | 0 |
| 2026-05 | 종합편성·보도전문 | [2026년 5월 종합편성·보도전문채널 심의의결 현황](https://www.kocsc.or.kr/main/cop/bbs/selectBoardArticle.do?bbsId=info_Opinion_main&nttId=21361&menuNo=040000&subMenuNo=040700) | 5 | 5 | 5 | 0 |
| 2026-05 | 상품판매방송 | [2026년 5월 상품판매방송 심의의결 현황](https://www.kocsc.or.kr/main/cop/bbs/selectBoardArticle.do?bbsId=info_Opinion_main&nttId=21297&menuNo=040000&subMenuNo=040700) | 4 | 4 | 4 | 0 |
| 2026-05 | 전문편성 | [2026년 5월 전문편성채널 심의의결 현황](https://www.kocsc.or.kr/main/cop/bbs/selectBoardArticle.do?bbsId=info_Opinion_main&nttId=21307&menuNo=040000&subMenuNo=040700) | 3 | 3 | 3 | 0 |
| 2026-05 | 지상파방송 | [2026년 5월 지상파방송 심의의결 현황](https://www.kocsc.or.kr/main/cop/bbs/selectBoardArticle.do?bbsId=info_Opinion_main&nttId=21314&menuNo=040000&subMenuNo=040700) | 7 | 5 | 5 | 2 |
| 2026-06 | 방송광고 | [2026년 6월 방송광고 심의의결 현황](https://www.kocsc.or.kr/main/cop/bbs/selectBoardArticle.do?bbsId=info_Opinion_main&nttId=21394&menuNo=040000&subMenuNo=040700) | 26 | 21 | 10 | 5 |
| 2026-06 | 종합편성·보도전문 | [2026년 6월 종합편성·보도전문채널 심의의결 현황](https://www.kocsc.or.kr/main/cop/bbs/selectBoardArticle.do?bbsId=info_Opinion_main&nttId=21452&menuNo=040000&subMenuNo=040700) | 6 | 6 | 6 | 0 |
| 2026-06 | 상품판매방송 | [2026년 6월 상품판매방송 심의의결 현황](https://www.kocsc.or.kr/main/cop/bbs/selectBoardArticle.do?bbsId=info_Opinion_main&nttId=21413&menuNo=040000&subMenuNo=040700) | 11 | 11 | 11 | 0 |
| 2026-06 | 전문편성 | [2026년 6월 전문편성채널 심의의결 현황](https://www.kocsc.or.kr/main/cop/bbs/selectBoardArticle.do?bbsId=info_Opinion_main&nttId=21409&menuNo=040000&subMenuNo=040700) | 12 | 12 | 12 | 0 |
| 2026-06 | 지상파방송 | [2026년 6월 지상파방송 심의의결 현황](https://www.kocsc.or.kr/main/cop/bbs/selectBoardArticle.do?bbsId=info_Opinion_main&nttId=21395&menuNo=040000&subMenuNo=040700) | 11 | 11 | 11 | 0 |
| 2026-07 (부분 공개분) | 상품판매방송 | [2026년 7월 상품판매방송 심의의결 현황](https://www.kocsc.or.kr/main/cop/bbs/selectBoardArticle.do?bbsId=info_Opinion_main&nttId=21502&menuNo=040000&subMenuNo=040700) | 13 | 13 | 12 | 0 |
| 2026-07 (부분 공개분) | 지상파방송 | [2026년 7월 지상파방송 심의의결 현황](https://www.kocsc.or.kr/main/cop/bbs/selectBoardArticle.do?bbsId=info_Opinion_main&nttId=21491&menuNo=040000&subMenuNo=040700) | 7 | 7 | 7 | 0 |

## 제외 기준

- `duplicate_decision_id_in_source`: 1개
- `external_post_broadcast_evidence`: 1개
- `no_indexed_gold_rule`: 20개

## 주의사항

- 공식 결과는 보존하지만 주 과제 라벨은 `no_flag`와 `review_required`로 단순화했다.
- 의견제시·권고는 `administrative_guidance`, 주의 이상은 `statutory_sanction`으로 별도 보존했다.
- `evidence_structure`는 현재 조문 페이지 수와 명시적 reference edge만으로 계산한다. 순차 재검색 여부는 후속 수동 검수 대상이다.
- 문제없음 사례는 공식 관련조항이 대체로 없으므로, 현재는 수동으로 검토 조항을 연결한 경계 사례 1건만 포함했다.
- 상세 SHA-256, 로컬 파일명, 게시판 URL은 `synthetic_qa_report.json`의 `sources`에 기록했다.
