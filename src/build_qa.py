from __future__ import annotations

import argparse
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml
from pypdf import PdfReader

from common import (
    ROOT,
    compact_hash,
    file_sha256,
    flatten_rule_units,
    load_config,
    load_jsonl,
    normalize_space,
    write_json,
    write_jsonl,
)
SOURCE_CONFIG = ROOT / "configs" / "decision_sources.yaml"
OVERRIDES_CONFIG = ROOT / "configs" / "qa_overrides.yaml"
DEFAULT_INPUT_DIR = ROOT / "data" / "raw" / "decisions"
BOARD_URL = (
    "https://www.kocsc.or.kr/main/cop/bbs/selectBoardArticle.do"
    "?bbsId=info_Opinion_main&nttId={ntt_id}&menuNo=040000&subMenuNo=040700"
)
SUBITEM_LETTERS = {
    label: chr(ord("A") + index)
    for index, label in enumerate("가나다라마바사아자차카타파하")
}

DECISION_ID_RE = re.compile(
    r"(?:제)?(?P<year>20\d{2})-"
    r"(?:(?P<kind>광고|방송)-)?"
    r"(?P<session>\d{1,2})-(?P<number>\d{4})(?:호)?"
)
DATE_RE = re.compile(r"(?P<year>20\d{2})[.\-](?P<month>\d{1,2})[.\-](?P<day>\d{1,2})")
OUTCOME_RE = re.compile(r"문제없음|의견제시|권고|주의|경고|관계자\s*징계|과징금")
RULE_MARKER_RE = re.compile(
    r"[「｢]?\s*(?P<document>"
    r"상품소개\s*및\s*판매방송\s*심의에\s*관한\s*규정|"
    r"방송광고심의에\s*관한\s*규정|"
    r"방송심의에\s*관한\s*규정(?:\s*\(\s*규칙\s*제\d+호\s*\))?"
    r")\s*[」｣]?"
)
CITATION_TOKEN_RE = re.compile(
    r"제(?P<article>\d+)조(?:의(?P<branch>\d+))?(?:\([^)]*\))?"
    r"|제(?P<paragraph>\d+)항"
    r"|제(?P<item>\d+)호"
    r"|(?P<subitem>[가-하])목"
)
ANSWERABILITY_EXCLUDE_RE = re.compile(
    r"약\s*\d+개월\s*후\s*동일\s*방송사|"
    r"방송\s*(?:후|이후)\s*(?:제출|확보)된?\s*(?:자료|소명)|"
    r"추가\s*(?:제출|확보)\s*자료"
)

DOCUMENT_IDS = {
    "방송심의에관한규정": "BR_REVIEW",
    "방송광고심의에관한규정": "AD_REVIEW",
    "상품소개및판매방송심의에관한규정": "SALES_REVIEW",
}
DOMAIN_BY_CATEGORY = {
    "terrestrial": "broadcast_program",
    "comprehensive_news": "broadcast_program",
    "specialty": "broadcast_program",
    "broadcast_ad": "broadcast_ad",
    "product_sales": "product_sales",
}


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def canonical_decision_id(match: re.Match[str]) -> str:
    middle = f"-{match.group('kind')}" if match.group("kind") else ""
    return (
        f"{match.group('year')}{middle}-"
        f"{int(match.group('session')):02d}-{match.group('number')}"
    )


def normalize_pdf_text(text: str) -> str:
    text = text.replace("\x00", "").replace("\u00a0", " ")
    text = re.sub(
        r"상\s*품\s*소\s*개\s*및\s*판\s*매\s*방\s*송\s*심\s*의\s*에\s*관\s*한\s*규\s*정",
        "상품소개 및 판매방송 심의에 관한 규정",
        text,
    )
    text = re.sub(
        r"방\s*송\s*광\s*고\s*심\s*의\s*에\s*관\s*한\s*규\s*정",
        "방송광고심의에 관한 규정",
        text,
    )
    text = re.sub(
        r"방\s*송\s*심\s*의\s*에\s*관\s*한\s*규\s*정",
        "방송심의에 관한 규정",
        text,
    )
    text = re.sub(r"(20\d{2})\s*-\s*방\s*송\s*-\s*", r"\1-방송-", text)
    text = re.sub(r"(20\d{2})\s*-\s*광\s*고\s*-\s*", r"\1-광고-", text)
    text = re.sub(r"(?<=\d)\s*[-‐‑–—]\s*(?=\d)", "-", text)
    text = re.sub(r"(?<=\d)\s*[-‐‑–—]\s*(?=광고|방송)", "-", text)
    text = re.sub(r"(?<=광고|방송)\s*[-‐‑–—]\s*(?=\d)", "-", text)
    text = re.sub(r"제\s*(\d+)\s*조\s*의\s*(\d+)", r"제\1조의\2", text)
    text = re.sub(r"제\s*(\d+)\s*(조|항|호)", r"제\1\2", text)
    text = re.sub(r"([가-하])\s*목", r"\1목", text)
    # The committee PDFs sometimes wrap a Korean word in the middle of a
    # syllable sequence.  Keep this list deliberately narrow: a general
    # Hangul-newline-Hangul join would also erase genuine word boundaries.
    split_word_repairs = {
        "염 증": "염증",
        "증 가": "증가",
        "통 증": "통증",
        "내 용": "내용",
        "표 현": "표현",
        "언 급": "언급",
        "장 면": "장면",
        "대 해": "대해",
        "발생하 지": "발생하지",
        "제품 과": "제품과",
        "내용 을": "내용을",
        "등 을": "등을",
        "연골세 포": "연골세포",
        "것 에": "것에",
        "발 생하지": "발생하지",
        "묘사하 는": "묘사하는",
        "방 송한": "방송한",
        "않도 록": "않도록",
        "것으 로": "것으로",
        "제 품": "제품",
        "종 합적으로": "종합적으로",
        "충전부 터": "충전부터",
        "판매조 건": "판매조건",
        "위 반되는": "위반되는",
        "지저 분": "지저분",
        "기어다 니는": "기어다니는",
        "패키 지": "패키지",
        "인 덕션": "인덕션",
        "무료체 험": "무료체험",
        "전립 선건강": "전립선건강",
        "있도 록": "있도록",
        "청 소년": "청소년",
        "가톨릭평화방 송": "가톨릭평화방송",
        "서 류": "서류",
        "어린 이": "어린이",
        "시 청자": "시청자",
    }
    for broken, repaired in split_word_repairs.items():
        text = re.sub(r"\s+".join(map(re.escape, broken.split())), repaired, text)
    text = re.sub(r"[ \t]+", " ", text)
    return text


def normalize_date(raw: str) -> str | None:
    match = DATE_RE.search(raw)
    if not match:
        return None
    return (
        f"{match.group('year')}-{int(match.group('month')):02d}-"
        f"{int(match.group('day')):02d}"
    )


def source_inventory(input_dir: Path, source_config: Path) -> list[dict[str, Any]]:
    configured = load_yaml(source_config).get("sources", [])
    sources: list[dict[str, Any]] = []
    for item in configured:
        path = input_dir / item["local_file"]
        if not path.exists():
            raise FileNotFoundError(f"공식 의결 PDF 누락: {path}")
        reader = PdfReader(str(path))
        sources.append({
            "source_id": item["source_id"],
            "period": item["period"],
            "category": item["category"],
            "coverage": item.get("coverage", "complete"),
            "title": item["title"],
            "board_url": BOARD_URL.format(ntt_id=item["ntt_id"]),
            "ntt_id": int(item["ntt_id"]),
            "local_file": item["local_file"],
            "sha256": file_sha256(path),
            "page_count": len(reader.pages),
        })
    return sources


def extract_rows(path: Path, source: dict[str, Any]) -> list[dict[str, Any]]:
    reader = PdfReader(str(path))
    page_texts = [normalize_pdf_text(page.extract_text() or "") for page in reader.pages]
    spans: list[tuple[int, int, int]] = []
    parts: list[str] = []
    cursor = 0
    for page_number, page_text in enumerate(page_texts, 1):
        separator = f"\n\n[[PAGE_{page_number}]]\n\n"
        parts.append(separator)
        cursor += len(separator)
        start = cursor
        parts.append(page_text)
        cursor += len(page_text)
        spans.append((start, cursor, page_number))
    text = "".join(parts)
    matches = list(DECISION_ID_RE.finditer(text))
    rows: list[dict[str, Any]] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        raw = text[start:end]
        nearby = text[max(0, start - 120):match.end() + 80]
        dates = list(DATE_RE.finditer(nearby))
        decision_date = normalize_date(dates[-1].group(0)) if dates else None
        pages = [
            page_number
            for page_start, page_end, page_number in spans
            if page_start < end and page_end > start
        ]
        rows.append({
            "decision_id": canonical_decision_id(match),
            "decision_date": decision_date,
            "source_id": source["source_id"],
            "source_period": source["period"],
            "source_category": source["category"],
            "pages": pages,
            "raw": raw,
        })
    return rows


def outcome_from_raw(raw: str) -> str | None:
    matches = list(OUTCOME_RE.finditer(raw))
    if not matches:
        return None
    return normalize_space(matches[-1].group(0))


def document_id_from_marker(raw: str) -> str | None:
    compact = re.sub(r"\s+", "", raw)
    compact = re.sub(r"\(규칙제\d+호\)", "", compact)
    return DOCUMENT_IDS.get(compact)


def deepest_rule_id(
    document_id: str,
    article: str,
    branch: str | None,
    paragraph: str | None,
    item: str | None,
    subitem: str | None,
) -> str:
    rule_id = f"{document_id}_ART{article}"
    if branch:
        rule_id += f"_{branch}"
    if paragraph:
        rule_id += f"_P{paragraph}"
    if item:
        rule_id += f"_I{item}"
    if subitem:
        rule_id += f"_{SUBITEM_LETTERS.get(subitem, subitem)}"
    return rule_id


def citation_ids(citation: str, document_id: str) -> list[str]:
    output: list[str] = []
    article: str | None = None
    branch: str | None = None
    paragraph: str | None = None
    item: str | None = None
    subitem: str | None = None

    def flush() -> None:
        if not article:
            return
        rule_id = deepest_rule_id(document_id, article, branch, paragraph, item, subitem)
        if rule_id not in output:
            output.append(rule_id)

    for token in CITATION_TOKEN_RE.finditer(citation):
        if token.group("article"):
            flush()
            article = token.group("article")
            branch = token.group("branch")
            paragraph = item = subitem = None
        elif token.group("paragraph") and article:
            if paragraph is not None:
                flush()
            paragraph = token.group("paragraph")
            item = subitem = None
        elif token.group("item") and article:
            if item is not None:
                flush()
            item = token.group("item")
            subitem = None
        elif token.group("subitem") and article:
            if subitem is not None:
                flush()
            subitem = token.group("subitem")
    flush()
    return output


def resolve_to_corpus(rule_id: str, units: dict[str, dict[str, Any]]) -> tuple[str | None, bool]:
    candidate = rule_id
    while candidate:
        if candidate in units:
            return candidate, candidate != rule_id
        if "_" not in candidate:
            break
        candidate = candidate.rsplit("_", 1)[0]
    return None, False


def rule_ids_from_raw(
    raw: str,
    units: dict[str, dict[str, Any]],
) -> tuple[list[str], int, list[str]]:
    markers = list(RULE_MARKER_RE.finditer(raw))
    ids: list[str] = []
    fallback_count = 0
    raw_documents: list[str] = []
    for index, marker in enumerate(markers):
        document_id = document_id_from_marker(marker.group("document"))
        if not document_id:
            continue
        raw_documents.append(normalize_space(marker.group("document")))
        end = markers[index + 1].start() if index + 1 < len(markers) else len(raw)
        tail = raw[marker.end():end]
        outcome = OUTCOME_RE.search(tail)
        if outcome:
            tail = tail[:outcome.start()]
        for candidate in citation_ids(tail, document_id):
            resolved, used_fallback = resolve_to_corpus(candidate, units)
            if resolved and resolved not in ids:
                ids.append(resolved)
                fallback_count += int(used_fallback)
    return ids, fallback_count, raw_documents


def content_from_raw(raw: str) -> str:
    marker = raw.find("○")
    if marker < 0:
        return ""
    text = raw[marker + 1:]
    rule_marker = RULE_MARKER_RE.search(text)
    if rule_marker:
        text = text[:rule_marker.start()]
    text = re.sub(r"\[\[PAGE_\d+\]\]", " ", text)
    return normalize_space(text)


def neutral_artifact(content: str) -> str:
    text = content
    review_marker = re.search(
        r"(?:해당\s*)?방송\s*내용을?\s*확인하고\s*논의한\s*결과\s*[,，]?",
        text,
    )
    if review_marker and "민원" in text[:review_marker.start()]:
        text = text[review_marker.end():]
    split_patterns = [
        r"\s*사안에\s*대해(?:\s*논의한\s*결과)?",
        r"\s*방송한\s*바\s*[,，]?",
        r"\s*(?:내용|장면)[^.!?]{0,160}?방송한\s*바\s*[,，]?",
        r"\s*방송한\s*것(?:은|으로)",
    ]
    for pattern in split_patterns:
        match = re.search(pattern, text)
        if match:
            text = text[:match.start()]
            break

    legal = re.search(
        r"관련\s*심의\s*규정(?:에|의|을|를|\s*위반)|"
        r"관련\s*심의규정(?:에|의|을|를|\s*위반)|"
        r"문제없음\s*으로\s*의결|"
        r"[｢「]방송법[｣」]\s*제100조",
        text,
    )
    if legal:
        text = text[:legal.start()]
    text = re.sub(r"\s*것은\s*$", "", text)
    text = re.sub(r"\s*-\s*$", "", text)
    return normalize_space(text).strip(" ,.-")


def rationale_from_content(content: str, outcome: str) -> str:
    text = content
    result_marker = re.search(r"사안에\s*대해(?:\s*논의한\s*결과)?\s*[,，]?", text)
    if result_marker:
        text = text[result_marker.end():]
    legal_tail = re.search(r"[｢「]방송법[｣」]\s*제100조", text)
    if legal_tail:
        text = text[:legal_tail.start()]
    mitigation = re.search(
        r"\s*-?\s*(?:다만|비록|해당\s*사안에\s*대한\s*문제를\s*인지한\s*후|"
        r"이후\s*(?:사과|수정|삭제|조치)|기존\s*유사사례와의\s*형평성).*$",
        text,
    )
    if mitigation:
        text = text[:mitigation.start()]
    text = re.sub(r"\s*-\s*", " ", text)
    text = normalize_space(text).strip(" ,.-")
    if not text:
        return "공식 의결문에 기재된 사실관계와 관련 규정에 따라 판단한다."
    if outcome == "문제없음" and "문제없음" not in text:
        text += " 해당 표현만으로는 검토 조항의 요건이 충족되지 않는 것으로 판단되었다."
    return text


def screening_label(outcome: str) -> str:
    return "no_flag" if outcome == "문제없음" else "review_required"


def severity(outcome: str) -> str:
    if outcome == "문제없음":
        return "none"
    if outcome in {"의견제시", "권고"}:
        return "administrative_guidance"
    return "statutory_sanction"


def article_ids(rule_ids: list[str], units: dict[str, dict[str, Any]]) -> list[str]:
    return sorted({units[rule_id]["article_rule_id"] for rule_id in rule_ids})


def reference_article_edges(
    edges: list[dict[str, Any]],
    units: dict[str, dict[str, Any]],
) -> set[tuple[str, str]]:
    output: set[tuple[str, str]] = set()
    for edge in edges:
        if edge.get("relation") != "REFERENCES" or not edge.get("target_rule_id"):
            continue
        source = units.get(edge["source_rule_id"])
        target = units.get(edge["target_rule_id"])
        if not source or not target:
            continue
        output.add((source["article_rule_id"], target["article_rule_id"]))
    return output


def evidence_structure(
    rule_ids: list[str],
    units: dict[str, dict[str, Any]],
    reference_edges: set[tuple[str, str]],
) -> str:
    pages = article_ids(rule_ids, units)
    if len(pages) <= 1:
        return "single_page"
    required = set(pages)
    connected = {pages[0]}
    changed = True
    while changed:
        changed = False
        for source, target in reference_edges:
            if source in connected and target in required and target not in connected:
                connected.add(target)
                changed = True
            if target in connected and source in required and source not in connected:
                connected.add(source)
                changed = True
    return "multi_page_linked" if connected == required else "multi_page_unlinked"


def case_fingerprint(artifact: str, rule_ids: list[str], outcome: str) -> str:
    material = re.sub(r"\s+", "", artifact)
    return compact_hash("|".join([material, ",".join(sorted(rule_ids)), outcome]), 24)


def build_qa(
    rows: list[dict[str, Any]],
    corpus: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    config: dict[str, Any],
    overrides: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    units = flatten_rule_units(corpus)
    ref_edges = reference_article_edges(edges, units)
    manual = overrides.get("decisions", {})
    prepared: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    fallback_total = 0

    seen_decision_ids: set[tuple[str, str]] = set()
    for row in rows:
        source_decision_key = (row["source_id"], row["decision_id"])
        if source_decision_key in seen_decision_ids:
            excluded.append({
                "decision_id": row["decision_id"],
                "source_id": row["source_id"],
                "reason": "duplicate_decision_id_in_source",
            })
            continue
        seen_decision_ids.add(source_decision_key)

        outcome = outcome_from_raw(row["raw"])
        content = content_from_raw(row["raw"])
        override = manual.get(row["decision_id"], {})
        artifact = override.get("artifact_text") or neutral_artifact(content)
        parsed_rule_ids, fallback_count, raw_documents = rule_ids_from_raw(row["raw"], units)
        reviewed_rule_ids = override.get("reviewed_rule_ids", [])
        rule_ids = parsed_rule_ids or reviewed_rule_ids

        reason: str | None = None
        if not outcome:
            reason = "outcome_parse_failed"
        elif ANSWERABILITY_EXCLUDE_RE.search(content):
            reason = "external_post_broadcast_evidence"
        elif not content or not artifact:
            reason = "artifact_parse_failed"
        elif not rule_ids:
            reason = "no_indexed_gold_rule"
        elif any(rule_id not in units for rule_id in rule_ids):
            reason = "manual_rule_missing_from_corpus"
        if reason:
            excluded.append({
                "decision_id": row["decision_id"],
                "source_id": row["source_id"],
                "reason": reason,
                "detected_rule_documents": raw_documents,
            })
            continue

        fallback_total += fallback_count
        fingerprint = case_fingerprint(artifact, rule_ids, outcome)
        prepared.append({
            **row,
            "outcome": outcome,
            "content": content,
            "artifact": artifact,
            "rule_ids": rule_ids,
            "fingerprint": fingerprint,
            "manual_annotation": bool(reviewed_rule_ids and not parsed_rule_ids),
            "rationale_override": override.get("rationale"),
        })

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in prepared:
        grouped[row["fingerprint"]].append(row)

    qa_rows: list[dict[str, Any]] = []
    for fingerprint, group in sorted(grouped.items()):
        first = group[0]
        source_refs: list[dict[str, Any]] = []
        for source_id in sorted({row["source_id"] for row in group}):
            source_rows = [row for row in group if row["source_id"] == source_id]
            source_refs.append({
                "source_id": source_id,
                "pages": sorted({page for row in source_rows for page in row["pages"]}),
            })
        application = (
            "considered_not_triggered" if first["outcome"] == "문제없음" else "triggered"
        )
        qa_rows.append({
            "qa_id": f"QA_{fingerprint.upper()}",
            "decision_ids": sorted({row["decision_id"] for row in group}),
            "source": source_refs,
            "artifact": {
                "domain": DOMAIN_BY_CATEGORY[first["source_category"]],
                "text": first["artifact"],
            },
            "question": config["qa"]["question"],
            "evidence_structure": evidence_structure(
                first["rule_ids"], units, ref_edges
            ),
            "gold": {
                "screening_label": screening_label(first["outcome"]),
                "severity": severity(first["outcome"]),
                "official_result": first["outcome"],
                "rules": [
                    {"rule_id": rule_id, "application": application}
                    for rule_id in first["rule_ids"]
                ],
                "rationale": first.get("rationale_override")
                or rationale_from_content(first["content"], first["outcome"]),
            },
            "review_status": "manual_seed" if first["manual_annotation"] else "auto_draft",
        })

    def distribution(values: list[str]) -> dict[str, int]:
        return dict(sorted(Counter(values).items()))

    source_meta = {
        row["source_id"]: {
            "period": row["source_period"],
            "category": row["source_category"],
        }
        for row in rows
    }
    raw_by_source = Counter(row["source_id"] for row in rows)
    included_by_source = Counter(row["source_id"] for row in prepared)
    excluded_by_source = Counter(item["source_id"] for item in excluded)
    cases_by_source = Counter(
        source["source_id"]
        for qa in qa_rows
        for source in qa["source"]
    )

    report = {
        "raw_decision_row_count": len(rows),
        "rows_with_indexed_gold": len(prepared),
        "independent_case_count": len(qa_rows),
        "duplicate_rows_collapsed": len(prepared) - len(qa_rows),
        "excluded_count": len(excluded),
        "excluded_by_reason": distribution([item["reason"] for item in excluded]),
        "excluded_decisions": excluded,
        "citation_fallback_to_parent_count": fallback_total,
        "manual_annotation_count": sum(row["review_status"] == "manual_seed" for row in qa_rows),
        "distribution": {
            "official_result": distribution([row["gold"]["official_result"] for row in qa_rows]),
            "screening_label": distribution([row["gold"]["screening_label"] for row in qa_rows]),
            "severity": distribution([row["gold"]["severity"] for row in qa_rows]),
            "domain": distribution([row["artifact"]["domain"] for row in qa_rows]),
            "evidence_structure": distribution([row["evidence_structure"] for row in qa_rows]),
            "source_period": distribution([
                source_meta[row["source"][0]["source_id"]]["period"] for row in qa_rows
            ]),
            "source_category": distribution([
                source_meta[row["source"][0]["source_id"]]["category"] for row in qa_rows
            ]),
        },
        "source_stats": [
            {
                "source_id": source_id,
                **source_meta[source_id],
                "raw_decision_rows": raw_by_source[source_id],
                "included_decision_rows": included_by_source[source_id],
                "independent_cases": cases_by_source[source_id],
                "excluded_rows": excluded_by_source[source_id],
            }
            for source_id in sorted(source_meta)
        ],
        "multi_page_candidates": [
            {
                "qa_id": row["qa_id"],
                "decision_ids": row["decision_ids"],
                "evidence_structure": row["evidence_structure"],
                "rule_ids": [rule["rule_id"] for rule in row["gold"]["rules"]],
            }
            for row in qa_rows
            if row["evidence_structure"] != "single_page"
        ],
        "build_status": "draft_requires_human_review",
        "note": (
            "공식 의결 PDF에서 결정적으로 추출한 1차 QA다. artifact와 rationale은 원문 대조 검수 후 "
            "최종 gold로 확정해야 하며, 문제없음 수동 seed 1건을 제외하면 관련조항이 명시된 사례만 포함했다."
        ),
    }
    return qa_rows, report


def validate(
    qa_rows: list[dict[str, Any]],
    corpus: list[dict[str, Any]],
    sources: list[dict[str, Any]],
) -> dict[str, Any]:
    units = set(flatten_rule_units(corpus))
    source_ids = {item["source_id"] for item in sources}
    invalid_rule_ids = sorted({
        rule["rule_id"]
        for row in qa_rows
        for rule in row["gold"]["rules"]
        if rule["rule_id"] not in units
    })
    invalid_source_ids = sorted({
        source["source_id"]
        for row in qa_rows
        for source in row["source"]
        if source["source_id"] not in source_ids
    })
    empty_artifacts = [row["qa_id"] for row in qa_rows if not row["artifact"]["text"]]
    empty_rationales = [row["qa_id"] for row in qa_rows if not row["gold"]["rationale"]]
    duplicate_qa_ids = len({row["qa_id"] for row in qa_rows}) != len(qa_rows)
    artifact_leakage_flags = [
        row["qa_id"]
        for row in qa_rows
        if re.search(r"관련\s*심의\s*규정|심의규정에\s*위반|제\d+조", row["artifact"]["text"])
    ]
    valid_labels = {"no_flag", "review_required"}
    invalid_labels = sorted({
        row["gold"]["screening_label"]
        for row in qa_rows
        if row["gold"]["screening_label"] not in valid_labels
    })
    ok = not (
        invalid_rule_ids
        or invalid_source_ids
        or empty_artifacts
        or empty_rationales
        or duplicate_qa_ids
        or invalid_labels
    )
    return {
        "qa_count": len(qa_rows),
        "source_count": len(sources),
        "invalid_rule_ids": invalid_rule_ids,
        "invalid_source_ids": invalid_source_ids,
        "empty_artifacts": empty_artifacts,
        "empty_rationales": empty_rationales,
        "duplicate_qa_ids": duplicate_qa_ids,
        "invalid_labels": invalid_labels,
        "artifact_leakage_flags": artifact_leakage_flags,
        "ok": ok,
    }


def summary_markdown(report: dict[str, Any]) -> str:
    distribution_data = report["distribution"]
    source_by_id = {source["source_id"]: source for source in report["sources"]}
    category_labels = {
        "terrestrial": "지상파방송",
        "comprehensive_news": "종합편성·보도전문",
        "specialty": "전문편성",
        "broadcast_ad": "방송광고",
        "product_sales": "상품판매방송",
    }
    lines = [
        "# Synthetic QA 1차 빌드 요약",
        "",
        "방송통신심의위원회 공식 월별 의결 PDF를 규정 기반 방송 전 검토 QA로 결정적으로 변환한 초안이다.",
        "모든 QA는 원문 대조 검수 전 `auto_draft`이며, `manual_seed`는 문제없음 경계 사례 1건이다.",
        "",
        "## 전체 수량",
        "",
        f"- 공식 PDF: {report['source_count']}개",
        f"- 파싱한 의결행: {report['raw_decision_row_count']}개",
        f"- 적재 규정에 매핑된 의결행: {report['rows_with_indexed_gold']}개",
        f"- 동일 콘텐츠·다채널 중복 통합: {report['duplicate_rows_collapsed']}개",
        f"- 최종 독립 QA 초안: {report['independent_case_count']}개",
        f"- 제외 의결행: {report['excluded_count']}개",
        "",
        "## QA 분포",
        "",
        "| 구분 | 값 | 수량 |",
        "|---|---|---:|",
    ]
    for group in ("official_result", "screening_label", "severity", "domain", "evidence_structure"):
        for value, count in distribution_data[group].items():
            lines.append(f"| {group} | {value} | {count} |")

    lines.extend([
        "",
        "## 공식 PDF별 수량",
        "",
        "`독립 QA`는 동일 광고·프로그램이 여러 채널에서 의결된 경우 하나로 합친 뒤의 수량이다.",
        "",
        "| 기간 | 계열 | 공식 출처 | 의결행 | 포함행 | 독립 QA | 제외 |",
        "|---|---|---|---:|---:|---:|---:|",
    ])
    for stat in sorted(report["source_stats"], key=lambda item: (item["period"], item["category"])):
        source = source_by_id[stat["source_id"]]
        title = source["title"]
        coverage = " (부분 공개분)" if source["coverage"] == "partial" else ""
        lines.append(
            f"| {stat['period']}{coverage} | {category_labels[stat['category']]} | "
            f"[{title}]({source['board_url']}) | {stat['raw_decision_rows']} | "
            f"{stat['included_decision_rows']} | {stat['independent_cases']} | {stat['excluded_rows']} |"
        )

    lines.extend([
        "",
        "## 제외 기준",
        "",
    ])
    for reason, count in report["excluded_by_reason"].items():
        lines.append(f"- `{reason}`: {count}개")
    lines.extend([
        "",
        "## 주의사항",
        "",
        "- 공식 결과는 보존하지만 주 과제 라벨은 `no_flag`와 `review_required`로 단순화했다.",
        "- 의견제시·권고는 `administrative_guidance`, 주의 이상은 `statutory_sanction`으로 별도 보존했다.",
        "- `evidence_structure`는 현재 조문 페이지 수와 명시적 reference edge만으로 계산한다. 순차 재검색 여부는 후속 수동 검수 대상이다.",
        "- 문제없음 사례는 공식 관련조항이 대체로 없으므로, 현재는 수동으로 검토 조항을 연결한 경계 사례 1건만 포함했다.",
        "- 상세 SHA-256, 로컬 파일명, 게시판 URL은 `synthetic_qa_report.json`의 `sources`에 기록했다.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--source-config", type=Path, default=SOURCE_CONFIG)
    parser.add_argument("--overrides", type=Path, default=OVERRIDES_CONFIG)
    parser.add_argument("--corpus", type=Path, default=ROOT / "data" / "reference" / "legal_corpus.jsonl")
    parser.add_argument("--edges", type=Path, default=ROOT / "data" / "reference" / "explicit_edges.jsonl")
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "processed" / "synthetic_qa.jsonl")
    parser.add_argument("--report", type=Path, default=ROOT / "data" / "processed" / "synthetic_qa_report.json")
    parser.add_argument("--summary", type=Path, default=ROOT / "data" / "processed" / "synthetic_qa_summary.md")
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()

    config = load_config()
    corpus = load_jsonl(args.corpus)
    edges = load_jsonl(args.edges)
    sources = source_inventory(args.input_dir, args.source_config)

    rows: list[dict[str, Any]] = []
    for source in sources:
        rows.extend(extract_rows(args.input_dir / source["local_file"], source))
    qa_rows, report = build_qa(rows, corpus, edges, config, load_yaml(args.overrides))
    validation = validate(qa_rows, corpus, sources)
    report["source_count"] = len(sources)
    report["sources"] = sources
    report["validation"] = validation
    if args.validate and not validation["ok"]:
        raise SystemExit(f"QA 검증 실패: {validation}")
    write_jsonl(args.output, qa_rows)
    write_json(args.report, report)
    summary_tmp = args.summary.with_suffix(args.summary.suffix + ".tmp")
    summary_tmp.write_text(summary_markdown(report), encoding="utf-8")
    summary_tmp.replace(args.summary)
    print(f"synthetic_qa: {len(qa_rows)} independent cases -> {args.output}")
    print(f"sources: {len(sources)} official PDFs -> embedded in {args.report}")
    print(f"validation: {'PASS' if validation['ok'] else 'FAIL'}")


if __name__ == "__main__":
    main()
