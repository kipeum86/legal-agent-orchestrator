#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")

TEAM = {
    "general-legal-research": {"name": "범용 법률 리서치 스페셜리스트", "role": "범용 법률 리서치"},
    "legal-writing-agent": {"name": "법률문서 작성 스페셜리스트", "role": "법률문서 작성"},
    "second-review-agent": {"name": "시니어 리뷰 스페셜리스트", "role": "품질 검토, 최종 승인"},
    "GDPR-expert": {"name": "GDPR 스페셜리스트", "role": "EU 데이터보호법 (GDPR)"},
    "PIPA-expert": {"name": "개인정보보호법 스페셜리스트", "role": "한국 개인정보보호법"},
    "game-legal-research": {"name": "게임산업 리서치 스페셜리스트", "role": "게임산업 국제법"},
    "contract-review-agent": {"name": "계약서 검토 스페셜리스트", "role": "계약서 검토"},
    "legal-translation-agent": {"name": "법률 번역 스페셜리스트", "role": "법률문서 번역"},
}

EVENT_ALIASES = {
    "research_completed": "agent_completed",
    "writing_completed": "agent_completed",
    "review_completed": "agent_completed",
}

STATUS_META = {
    "approved": "✓ 승인",
    "approved_with_revisions": "✓ 수정 후 승인",
    "revision_needed": "↻ 수정 필요",
    "partial": "◐ 부분 완료",
    "failed": "✕ 실패",
}


def _resolve_private_dir(project_root: Path) -> Path:
    return Path(
        os.environ.get("LEGAL_ORCHESTRATOR_PRIVATE_DIR", str(project_root / "output"))
    ).expanduser()


def _resolve_case_dir(case_arg: str, project_root: Path) -> Path:
    raw = Path(case_arg).expanduser()
    if raw.is_absolute():
        return raw.resolve()
    if len(raw.parts) == 1:
        return (_resolve_private_dir(project_root) / raw).resolve()
    return (project_root / raw).resolve()


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def read_json(path: Path) -> Any | None:
    text = read_text(path)
    if text is None:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def parse_jsonl(path: Path) -> list[dict[str, Any]]:
    text = read_text(path)
    if text is None:
        return []

    events: list[dict[str, Any]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            events.append(payload)
    return events


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def to_kst(value: str | None) -> datetime | None:
    dt = parse_iso(value)
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(KST)


def format_datetime(value: str | None) -> str:
    dt = to_kst(value)
    if dt is None:
        return "기록 없음"
    return dt.strftime("%Y-%m-%d %H:%M KST")


def format_time(value: str | None) -> str:
    dt = to_kst(value)
    if dt is None:
        return "--:--"
    return dt.strftime("%H:%M")


def seconds_between(start: str | None, end: str | None) -> int:
    start_dt = parse_iso(start)
    end_dt = parse_iso(end)
    if start_dt is None or end_dt is None:
        return 0
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=timezone.utc)
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=timezone.utc)
    return max(int((end_dt - start_dt).total_seconds()), 0)


def format_duration(total_seconds: int) -> str:
    if total_seconds <= 0:
        return "기록 없음"

    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts: list[str] = []
    if hours:
        parts.append(f"{hours}시간")
    if minutes:
        parts.append(f"{minutes}분")
    if seconds or not parts:
        parts.append(f"{seconds}초")
    return " ".join(parts)


def normalize_status(value: str | None) -> str:
    if not value:
        return "partial"

    normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
    if "approved_with_revisions" in normalized:
        return "approved_with_revisions"
    if "approved" in normalized and "revision" in normalized:
        return "approved_with_revisions"
    if normalized.startswith("approved"):
        return "approved"
    if "revision_needed" in normalized or "needs_revision" in normalized:
        return "revision_needed"
    if "failed" in normalized or "aborted" in normalized:
        return "failed"
    if "partial" in normalized:
        return "partial"
    return "partial"


def canonical_event_type(raw_type: str) -> str:
    return EVENT_ALIASES.get(raw_type, raw_type)


def infer_pattern(events: list[dict[str, Any]]) -> int:
    classified = next((event for event in events if event.get("type") == "case_classified"), None)
    data = classified.get("data", {}) if isinstance(classified, dict) else {}
    pattern = data.get("pattern")

    if isinstance(pattern, str):
        match = re.search(r"([123])", pattern)
        if match:
            return int(match.group(1))

    event_types = {str(event.get("type", "")) for event in events}
    if any(event_type.startswith("debate_") for event_type in event_types):
        return 3
    if any(event_type.startswith("parallel_dispatch") for event_type in event_types):
        return 1
    if "revision_requested" in event_types:
        return 2

    pipeline = data.get("pipeline")
    if isinstance(pipeline, list) and len(pipeline) >= 3:
        return 2
    return 1


def agent_name(agent_id: str, event_data: dict[str, Any] | None = None) -> str:
    if event_data and isinstance(event_data.get("name"), str) and event_data["name"].strip():
        return event_data["name"].strip()
    if agent_id in TEAM:
        return TEAM[agent_id]["name"]
    if agent_id == "orchestrator":
        return "오케스트레이터"
    return agent_id


def agent_role(agent_id: str, event_data: dict[str, Any] | None = None) -> str:
    if event_data and isinstance(event_data.get("role"), str) and event_data["role"].strip():
        return event_data["role"].strip()
    if agent_id in TEAM:
        return TEAM[agent_id]["role"]
    if agent_id == "orchestrator":
        return "사건 조율"
    return "역할 미기록"


def normalize_grade(value: Any) -> str | None:
    if isinstance(value, str) and value in {"A", "B", "C", "D"}:
        return value
    return None


def summarize_grades_from_sources(sources: list[dict[str, Any]]) -> dict[str, int]:
    distribution = {"A": 0, "B": 0, "C": 0, "D": 0}
    for source in sources:
        grade = normalize_grade(source.get("grade"))
        if grade:
            distribution[grade] += 1
    return distribution


def format_grade_breakdown(distribution: dict[str, int]) -> str:
    return " / ".join(f"{grade} {distribution.get(grade, 0)}" for grade in ("A", "B", "C", "D"))


def shorten(text: str, limit: int = 96) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def derive_summary(
    research_meta: dict[str, Any] | None,
    writing_meta: dict[str, Any] | None,
    review_meta: dict[str, Any] | None,
    final_output: dict[str, Any] | None,
) -> str:
    candidates = [
        research_meta.get("summary") if isinstance(research_meta, dict) else None,
        writing_meta.get("summary") if isinstance(writing_meta, dict) else None,
        review_meta.get("summary") if isinstance(review_meta, dict) else None,
        final_output.get("summary") if isinstance(final_output, dict) else None,
    ]
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return "이 케이스의 요약 정보가 충분히 기록되지 않았습니다."


def derive_key_findings(
    research_meta: dict[str, Any] | None,
    writing_meta: dict[str, Any] | None,
    review_meta: dict[str, Any] | None,
) -> list[str]:
    for source in (research_meta, writing_meta, review_meta):
        if isinstance(source, dict) and isinstance(source.get("key_findings"), list):
            findings = [str(item).strip() for item in source["key_findings"] if str(item).strip()]
            if findings:
                return findings[:5]
    return []


def load_meta_bundle(case_dir: Path) -> dict[str, dict[str, Any] | None]:
    return {
        "general-legal-research": read_json(case_dir / "research-meta.json"),
        "legal-writing-agent": read_json(case_dir / "writing-meta.json"),
        "second-review-agent": read_json(case_dir / "review-meta.json"),
    }


def collect_sources(
    events: list[dict[str, Any]],
    meta_bundle: dict[str, dict[str, Any] | None],
    sources_json: dict[str, Any] | None,
    final_output: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], int, dict[str, int]]:
    unique_map: dict[tuple[str, str], dict[str, Any]] = {}

    def upsert_source(title: str, citation: str, grade: str, citer: str) -> None:
        key = (title, citation)
        entry = unique_map.get(key)
        if entry is None:
            unique_map[key] = {
                "title": title,
                "citation": citation,
                "grade": grade,
                "citing_agents": [citer],
            }
            return
        if citer not in entry["citing_agents"]:
            entry["citing_agents"].append(citer)

    if isinstance(sources_json, dict) and isinstance(sources_json.get("agents"), list):
        for agent_payload in sources_json["agents"]:
            if not isinstance(agent_payload, dict):
                continue
            agent_id = str(agent_payload.get("agent_id") or "")
            citer = agent_name(agent_id, {"name": agent_payload.get("agent_name")})
            for source in agent_payload.get("sources", []):
                if not isinstance(source, dict):
                    continue
                title = str(source.get("title") or "제목 미기록")
                citation = str(source.get("citation") or "")
                grade = normalize_grade(source.get("grade")) or "D"
                upsert_source(title, citation, grade, citer)
    else:
        for agent_id, meta in meta_bundle.items():
            if not isinstance(meta, dict):
                continue
            citer = agent_name(agent_id, None)
            for source in meta.get("sources", []):
                if not isinstance(source, dict):
                    continue
                title = str(source.get("title") or "제목 미기록")
                citation = str(source.get("citation") or "")
                grade = normalize_grade(source.get("grade")) or "D"
                upsert_source(title, citation, grade, citer)

    if not unique_map:
        for event in events:
            if event.get("type") != "source_graded":
                continue
            data = event.get("data", {})
            if not isinstance(data, dict):
                data = {}
            upsert_source(
                str(data.get("source") or "제목 미기록"),
                str(data.get("citation") or ""),
                normalize_grade(data.get("grade")) or "D",
                agent_name(str(event.get("agent") or ""), data),
            )

    unique_sources = list(unique_map.values())
    unique_sources.sort(
        key=lambda item: (
            {"A": 0, "B": 1, "C": 2, "D": 3}.get(item["grade"], 4),
            item["title"],
        )
    )

    event_grade_distribution = summarize_grades_from_sources(
        [
            {"grade": event.get("data", {}).get("grade") if isinstance(event.get("data"), dict) else None}
            for event in events
            if event.get("type") == "source_graded"
        ]
    )

    final_data = final_output if isinstance(final_output, dict) else {}
    grade_distribution_raw = final_data.get("grade_distribution")
    if isinstance(grade_distribution_raw, dict):
        grade_distribution = {
            grade: int(grade_distribution_raw.get(grade, 0) or 0) for grade in ("A", "B", "C", "D")
        }
    elif isinstance(sources_json, dict) and isinstance(sources_json.get("grade_distribution"), dict):
        grade_distribution = {
            grade: int(sources_json["grade_distribution"].get(grade, 0) or 0) for grade in ("A", "B", "C", "D")
        }
    elif any(event_grade_distribution.values()):
        grade_distribution = event_grade_distribution
    else:
        grade_distribution = summarize_grades_from_sources(unique_sources)

    total_sources = final_data.get("total_sources")
    if isinstance(total_sources, int) and total_sources > 0:
        total = total_sources
    elif isinstance(sources_json, dict) and isinstance(sources_json.get("total_sources"), int):
        total = int(sources_json["total_sources"])
    else:
        graded_events = [event for event in events if event.get("type") == "source_graded"]
        total = len(graded_events) if graded_events else len(unique_sources)

    return unique_sources, total, grade_distribution


def render_single_event(event: dict[str, Any], pattern: int) -> tuple[str, list[str]]:
    event_type = str(event.get("type") or "")
    agent_id = str(event.get("agent") or "")
    data = event.get("data", {})
    if not isinstance(data, dict):
        data = {}

    ts = format_time(event.get("ts"))
    who = agent_name(agent_id, data)
    bullets: list[str] = []

    if event_type == "case_received":
        heading = f"### {ts} · 사건 접수"
        query = str(data.get("query") or "").strip()
        if query:
            bullets.append(f"- 질의: {query}")
        return heading, bullets

    if event_type == "case_classified":
        heading = f"### {ts} · 분류 → Pattern {pattern}"
        pipeline = data.get("pipeline")
        if isinstance(pipeline, list) and pipeline:
            pipeline_names = " → ".join(agent_name(str(agent), None) for agent in pipeline)
            bullets.append(f"- 파이프라인: {pipeline_names}")
        jurisdiction = data.get("jurisdiction")
        if isinstance(jurisdiction, list) and jurisdiction:
            bullets.append(f"- 관할: {', '.join(str(item) for item in jurisdiction)}")
        domain = str(data.get("domain") or "").strip()
        task = str(data.get("task") or "").strip()
        if domain or task:
            labels = [label for label in (domain, task) if label]
            bullets.append(f"- 작업 유형: {' / '.join(labels)}")
        return heading, bullets

    if event_type == "agent_assigned":
        heading = f"### {ts} · {who} 배정"
        bullets.append(f"- 역할: {agent_role(agent_id, data)}")
        return heading, bullets

    if event_type in {"research_completed", "writing_completed", "review_completed", "agent_completed"}:
        labels = {
            "research_completed": "리서치 완료",
            "writing_completed": "의견서 작성 완료",
            "review_completed": "시니어 리뷰 완료",
            "agent_completed": f"{who} 작업 완료",
        }
        heading = f"### {ts} · {labels.get(event_type, f'{who} 작업 완료')}"
        output_file = str(data.get("output_file") or data.get("result_path") or "").strip()
        sources_count = data.get("sources_count")
        key_findings_count = data.get("key_findings_count")
        comments_count = data.get("comments_count")
        approval = str(data.get("approval") or "").strip()
        if output_file:
            bullets.append(f"- 산출물: {output_file}")
        parts: list[str] = []
        if isinstance(sources_count, int):
            parts.append(f"{sources_count}개 소스")
        if isinstance(key_findings_count, int):
            parts.append(f"{key_findings_count}개 핵심 발견")
        if isinstance(comments_count, int):
            parts.append(f"{comments_count}개 코멘트")
        if parts:
            bullets.append(f"- 요약: {', '.join(parts)}")
        if approval:
            bullets.append(f"- 판정: {STATUS_META.get(normalize_status(approval), approval)}")
        return heading, bullets

    if event_type == "revision_requested":
        heading = f"### {ts} · 수정 요청"
        bullets.append(
            f"- 지적 사항: Critical {int(data.get('critical', 0) or 0)}건 / Major {int(data.get('major', 0) or 0)}건 / Minor {int(data.get('minor', 0) or 0)}건"
        )
        if data.get("cycle") is not None:
            bullets.append(f"- 수정 사이클: {data.get('cycle')}")
        return heading, bullets

    if event_type == "error":
        heading = f"### {ts} · {who} 오류 발생"
        bullets.append(f"- 내용: {str(data.get('message') or '오류 메시지 미기록').strip()}")
        error_type = str(data.get("error_type") or "").strip()
        if error_type:
            bullets.append(f"- 유형: {error_type}")
        return heading, bullets

    if event_type in {"verbatim_verified", "mcp_fallback_verification"}:
        heading = f"### {ts} · 오케스트레이터 검증 완료"
        verifier = str(data.get("verifier") or data.get("method") or "orchestrator").strip()
        bullets.append(f"- 검증자: {verifier}")
        if isinstance(data.get("critical_pass"), int) or isinstance(data.get("major_pass"), int):
            bullets.append(
                f"- 반영 확인: Critical {int(data.get('critical_pass', 0) or 0)}건 / Major {int(data.get('major_pass', 0) or 0)}건"
            )
        final_status = str(data.get("final_status") or "").strip()
        if final_status:
            bullets.append(f"- 최종 상태: {STATUS_META.get(normalize_status(final_status), final_status)}")
        return heading, bullets

    if event_type == "docx_generated":
        heading = f"### {ts} · Word 파일 생성"
        bullets.append(f"- 파일: {str(data.get('output') or 'opinion.docx').strip()}")
        if isinstance(data.get("size_bytes"), int):
            bullets.append(f"- 크기: {int(data['size_bytes']):,} bytes")
        return heading, bullets

    if event_type == "final_output":
        heading = f"### {ts} · 최종 산출물 확정"
        deliverables = data.get("deliverables")
        if isinstance(deliverables, list) and deliverables:
            bullets.append(f"- 결과물: {', '.join(str(item) for item in deliverables)}")
        summary = str(data.get("summary") or "").strip()
        if summary:
            bullets.append(f"- 요약: {shorten(summary, 140)}")
        return heading, bullets

    if event_type == "parallel_dispatch_start":
        heading = f"### {ts} · 병렬 검토 시작"
        participants = data.get("participants")
        if isinstance(participants, list) and participants:
            bullets.append(f"- 참여: {' / '.join(agent_name(str(item), None) for item in participants)}")
        return heading, bullets

    if event_type == "parallel_dispatch_complete":
        heading = f"### {ts} · 병렬 검토 완료"
        if isinstance(data.get("total_sources"), int):
            bullets.append(f"- 총 소스: {int(data['total_sources'])}건")
        return heading, bullets

    if event_type == "parallel_dispatch_partial":
        heading = f"### {ts} · 병렬 검토 부분 완료"
        succeeded = data.get("succeeded")
        failed = data.get("failed")
        if isinstance(succeeded, list) and succeeded:
            bullets.append(f"- 성공: {', '.join(agent_name(str(item), None) for item in succeeded)}")
        if isinstance(failed, list) and failed:
            failed_labels = []
            for item in failed:
                if isinstance(item, dict):
                    failed_labels.append(
                        f"{agent_name(str(item.get('agent') or ''), None)} ({item.get('error', 'error')})"
                    )
            if failed_labels:
                bullets.append(f"- 실패: {', '.join(failed_labels)}")
        return heading, bullets

    if event_type == "debate_initiated":
        heading = f"### {ts} · 토론 시작"
        topic = str(data.get("topic") or "").strip()
        framing = str(data.get("framing") or "").strip()
        if topic:
            bullets.append(f"- 주제: {topic}")
        if framing:
            bullets.append(f"- 구도: {framing}")
        return heading, bullets

    if event_type == "debate_round":
        heading = f"### {ts} · 토론 라운드 {data.get('round')} ({str(data.get('position') or 'opinion').strip()})"
        summary = str(data.get("summary") or "").strip()
        if summary:
            bullets.append(f"- 요약: {summary}")
        parts = []
        if isinstance(data.get("key_claims_count"), int):
            parts.append(f"핵심 주장 {int(data['key_claims_count'])}건")
        if isinstance(data.get("sources_count"), int):
            parts.append(f"소스 {int(data['sources_count'])}건")
        if parts:
            bullets.append(f"- {who}: {', '.join(parts)}")
        return heading, bullets

    if event_type == "debate_round3_decision":
        heading = f"### {ts} · 3라운드 진행 여부 판단"
        if isinstance(data.get("proceed"), bool):
            bullets.append(f"- 결정: {'진행' if data['proceed'] else '생략'}")
        reason = str(data.get("reason") or "").strip()
        if reason:
            bullets.append(f"- 사유: {reason}")
        return heading, bullets

    if event_type == "debate_concluded":
        heading = f"### {ts} · 토론 종료"
        verdict = str(data.get("verdict_summary") or "").strip()
        if verdict:
            bullets.append(f"- 결론: {verdict}")
        return heading, bullets

    if event_type == "user_prompt":
        heading = f"### {ts} · 사용자 확인 요청"
        question = str(data.get("question") or "").strip()
        if question:
            bullets.append(f"- 질문: {question}")
        return heading, bullets

    if event_type == "user_response":
        heading = f"### {ts} · 사용자 응답 수신"
        response = str(data.get("response") or "").strip()
        if response:
            bullets.append(f"- 응답: {response}")
        return heading, bullets

    if event_type == "agent_preflight":
        heading = f"### {ts} · {who} 사전 준비"
        action = str(data.get("action") or "").strip()
        if action:
            bullets.append(f"- 조치: {action}")
        path = str(data.get("path") or "").strip()
        if path:
            bullets.append(f"- 경로: {path}")
        return heading, bullets

    if event_type == "agent_out_of_scope":
        heading = f"### {ts} · {who} 범위 외 판단"
        reason = str(data.get("reason") or "").strip()
        if reason:
            bullets.append(f"- 사유: {reason}")
        fallback_to = str(data.get("fallback_to") or "").strip()
        if fallback_to:
            bullets.append(f"- 대체 라우트: {fallback_to}")
        return heading, bullets

    if event_type == "pipeline_aborted":
        heading = f"### {ts} · 파이프라인 중단"
        reason = str(data.get("reason") or "").strip()
        if reason:
            bullets.append(f"- 사유: {reason}")
        recovery = str(data.get("recovery") or "").strip()
        if recovery:
            bullets.append(f"- 복구 방안: {recovery}")
        return heading, bullets

    heading = f"### {ts} · {canonical_event_type(event_type).replace('_', ' ')}"
    if who:
        bullets.append(f"- 담당: {who}")
    if data:
        bullets.append(f"- 메타: `{json.dumps(data, ensure_ascii=False, sort_keys=True)}`")
    return heading, bullets


def build_timeline_entries(events: list[dict[str, Any]], pattern: int) -> list[str]:
    entries: list[str] = []
    index = 0
    while index < len(events):
        event = events[index]
        event_type = str(event.get("type") or "")
        agent_id = str(event.get("agent") or "")
        data = event.get("data", {})
        if not isinstance(data, dict):
            data = {}

        if event_type == "source_graded":
            grouped = [event]
            cursor = index + 1
            while cursor < len(events):
                candidate = events[cursor]
                if candidate.get("type") != "source_graded" or str(candidate.get("agent") or "") != agent_id:
                    break
                grouped.append(candidate)
                cursor += 1

            grade_distribution = {"A": 0, "B": 0, "C": 0, "D": 0}
            titles: list[str] = []
            for item in grouped:
                payload = item.get("data", {})
                if not isinstance(payload, dict):
                    payload = {}
                grade = normalize_grade(payload.get("grade"))
                if grade:
                    grade_distribution[grade] += 1
                title = str(payload.get("source") or "").strip()
                if title:
                    titles.append(title)

            heading = f"### {format_time(grouped[0].get('ts'))} · {agent_name(agent_id, data)} {len(grouped)}개 소스 확보"
            breakdown = " / ".join(f"{grade} {count}" for grade, count in grade_distribution.items() if count > 0)
            if breakdown:
                heading += f" ({breakdown})"
            entries.append(heading)
            if titles:
                preview = "; ".join(shorten(title, 42) for title in titles[:3])
                if len(titles) > 3:
                    preview += f" 외 {len(titles) - 3}건"
                entries.append(f"- 대표 출처: {preview}")
            entries.append(f"- 담당: {agent_name(agent_id, data)}")
            entries.append("")

            index = cursor
            continue

        heading, bullets = render_single_event(event, pattern)
        entries.append(heading)
        entries.extend(bullets)
        entries.append("")
        index += 1

    while entries and entries[-1] == "":
        entries.pop()
    return entries


def build_agent_sections(
    events: list[dict[str, Any]],
    meta_bundle: dict[str, dict[str, Any] | None],
) -> list[str]:
    grouped_assignments: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        if event.get("type") == "agent_assigned":
            grouped_assignments[str(event.get("agent") or "")].append(event)

    sections: list[str] = []
    for agent_id, assignments in grouped_assignments.items():
        first_assignment = assignments[0]
        agent_events = [event for event in events if str(event.get("agent") or "") == agent_id]
        completion_event = next(
            (
                event
                for event in agent_events
                if canonical_event_type(str(event.get("type") or "")) == "agent_completed"
            ),
            None,
        )

        duration = format_duration(
            seconds_between(first_assignment.get("ts"), completion_event.get("ts") if completion_event else None)
        )
        data = first_assignment.get("data", {})
        if not isinstance(data, dict):
            data = {}
        name = agent_name(agent_id, data)
        role = agent_role(agent_id, data)
        sections.append(f"### {name} — {role} ({duration})")

        if len(assignments) > 1:
            sections.append(f"- 재배정: {len(assignments) - 1}회")

        meta = meta_bundle.get(agent_id)
        findings: list[str] = []
        if isinstance(meta, dict) and isinstance(meta.get("key_findings"), list):
            findings = [str(item).strip() for item in meta["key_findings"] if str(item).strip()]

        if findings:
            for finding in findings[:3]:
                sections.append(f"- 기여: {finding}")
        else:
            sections.append("- 기여: 별도 핵심 발견 메모가 남아 있지 않습니다.")
        sections.append("")

    while sections and sections[-1] == "":
        sections.pop()
    return sections


def title_from_issue(issue: str) -> str:
    compact = re.sub(r"\s+", " ", issue).strip().rstrip(".")
    for separator in ("으로 ", "로 ", "이며 ", "이고 ", "라는 ", "인데 ", "임에도 "):
        if separator in compact:
            candidate = compact.split(separator, 1)[0].strip()
            if 12 <= len(candidate) <= 90:
                return candidate
    if len(compact) > 72:
        cutoff = compact.rfind(" ", 0, 69)
        if cutoff > 20:
            return compact[:cutoff].rstrip() + "..."
        return compact[:69].rstrip() + "..."
    return compact or "제목 미기록"


def group_revision_notes(writing_meta: dict[str, Any] | None) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    if not isinstance(writing_meta, dict):
        return grouped
    revisions = writing_meta.get("revisions_applied")
    if not isinstance(revisions, list):
        return grouped
    for item in revisions:
        if not isinstance(item, dict):
            continue
        severity = str(item.get("severity") or "").strip().lower()
        if severity in {"critical", "major", "minor"}:
            grouped[severity].append(item)
    return grouped


def render_review_section(
    review_meta: dict[str, Any] | None,
    writing_meta: dict[str, Any] | None,
) -> list[str]:
    lines = ["## 시니어 리뷰 결과", ""]
    if not isinstance(review_meta, dict):
        lines.append("리뷰 단계 메타데이터가 없어 시니어 리뷰 결과를 상세히 재구성하지 못했습니다.")
        return lines

    approval = normalize_status(str(review_meta.get("approval") or ""))
    comments = review_meta.get("comments")
    findings = [item for item in comments if isinstance(item, dict)] if isinstance(comments, list) else []
    lines.append("- 리뷰어: 시니어 리뷰 스페셜리스트")
    lines.append(f"- 판정: {STATUS_META.get(approval, approval)}")
    lines.append(f"- 총 코멘트: {len(findings)}건")
    lines.append("")

    revision_notes = group_revision_notes(writing_meta)
    for severity_label, heading_label in [("critical", "Critical"), ("major", "Major"), ("minor", "Minor")]:
        severity_findings = [item for item in findings if str(item.get("severity") or "").lower() == severity_label]
        applied_notes = revision_notes.get(severity_label, [])
        resolved_count = sum(1 for item in applied_notes if str(item.get("status") or "").strip().lower() == "applied")
        if not severity_findings:
            lines.append(f"### {heading_label} (0건)")
            lines.append("발견 없음")
            lines.append("")
            continue

        if resolved_count == len(severity_findings):
            suffix = "전건 반영"
        elif resolved_count > 0:
            suffix = f"{resolved_count}건 반영"
        else:
            suffix = "반영 상태 미상"

        lines.append(f"### {heading_label} ({len(severity_findings)}건 · {suffix})")
        for index, finding in enumerate(severity_findings, start=1):
            issue = str(finding.get("issue") or "세부 지적 없음").strip()
            recommendation = str(finding.get("recommendation") or "수정 권고 미기록").strip()
            location = str(finding.get("location") or "위치 미기록").strip()
            applied_note = ""
            if index - 1 < len(applied_notes):
                applied_note = str(applied_notes[index - 1].get("note") or "").strip()

            lines.append(f"**#{index} {title_from_issue(issue)}**")
            lines.append(f"- 초안 위치: {location}")
            lines.append(f"- 지적: {issue}")
            lines.append(f"- 수정: {applied_note or recommendation}")
            lines.append("")

    while lines and lines[-1] == "":
        lines.pop()
    return lines


def render_sources_section(
    unique_sources: list[dict[str, Any]],
    total_sources: int,
    grade_distribution: dict[str, int],
) -> list[str]:
    lines = ["## 인용 소스", ""]
    lines.append(f"- 총 인용: {total_sources}회")
    lines.append(f"- 등급 분포: {format_grade_breakdown(grade_distribution)}")
    if total_sources != len(unique_sources):
        lines.append(f"- 중복 제거 후 고유 소스: {len(unique_sources)}건")
    lines.append("")
    lines.append("| # | Grade | 인용 | 조문/출처 |")
    lines.append("|---|---|---|---|")

    for index, source in enumerate(unique_sources, start=1):
        title = str(source["title"]).replace("|", "\\|")
        citation = str(source["citation"]).replace("|", "\\|")
        agents = ", ".join(source["citing_agents"]).replace("|", "\\|")
        lines.append(f"| {index:02d} | {source['grade']} | {agents} | {title}<br>{citation} |")

    return lines


def transform_opinion_markdown(body: str) -> str:
    lines = body.splitlines()
    transformed: list[str] = []
    skipped_first_h1 = False

    for line in lines:
        if not skipped_first_h1 and re.match(r"^#\s+", line):
            skipped_first_h1 = True
            continue

        match = re.match(r"^(#{1,6})\s+(.*)$", line)
        if match:
            level = len(match.group(1))
            new_level = 3 if level == 1 else min(6, level + 1)
            transformed.append(f"{'#' * new_level} {match.group(2)}")
            continue

        transformed.append(line)

    return "\n".join(transformed).strip()


def build_attachment_lines(case_dir: Path, final_output: dict[str, Any] | None) -> list[str]:
    label_map = {
        "opinion.docx": "Word 포맷",
        "opinion.md": "최종 의견서 마크다운",
        "debate-opinion.docx": "토론 종합 판단 Word",
        "debate-opinion.md": "토론 종합 판단 마크다운",
        "debate-transcript.docx": "토론 트랜스크립트 Word",
        "debate-transcript.md": "토론 트랜스크립트 마크다운",
        "events.jsonl": "원본 이벤트 로그",
        "review-result.md": "리뷰 전문",
        "research-result.md": "리서치 메모",
        "sources.json": "소스 통합 메타데이터",
        "verbatim-verification.md": "오케스트레이터 검증 메모",
    }

    candidates: list[str] = []
    if isinstance(final_output, dict) and isinstance(final_output.get("deliverables"), list):
        candidates.extend(str(item) for item in final_output["deliverables"])
    candidates.extend(["opinion.docx", "opinion.md", "events.jsonl", "review-result.md", "research-result.md", "sources.json"])

    seen: set[str] = set()
    lines = ["## 첨부", ""]
    for filename in candidates:
        if filename in seen:
            continue
        seen.add(filename)
        path = case_dir / filename
        if not path.exists():
            continue
        lines.append(f"- [{filename}](./{filename}) — {label_map.get(filename, '첨부 파일')}")

    if len(lines) == 2:
        lines.append("- 별도 첨부 파일이 확인되지 않았습니다.")
    return lines


def generate_case_report(case_dir: Path) -> tuple[Path | None, list[str]]:
    warnings: list[str] = []
    if not case_dir.exists() or not case_dir.is_dir():
        warnings.append(f"케이스 디렉토리를 찾지 못해 생성하지 않았습니다: {case_dir}")
        return None, warnings

    events = parse_jsonl(case_dir / "events.jsonl")
    if not events:
        warnings.append(f"events.jsonl이 없어 case-report 생성을 건너뛰었습니다: {case_dir}")
        return None, warnings

    meta_bundle = load_meta_bundle(case_dir)
    research_meta = meta_bundle["general-legal-research"]
    writing_meta = meta_bundle["legal-writing-agent"]
    review_meta = meta_bundle["second-review-agent"]
    sources_json = read_json(case_dir / "sources.json")

    final_output_event = next((event for event in reversed(events) if event.get("type") == "final_output"), None)
    final_output = final_output_event.get("data") if isinstance(final_output_event, dict) else None
    if not isinstance(final_output, dict):
        final_output = None

    query = "질문 원문이 기록되지 않았습니다."
    case_received = next((event for event in events if event.get("type") == "case_received"), None)
    if isinstance(case_received, dict):
        data = case_received.get("data", {})
        if isinstance(data, dict) and isinstance(data.get("query"), str) and data["query"].strip():
            query = data["query"].strip()

    pattern = infer_pattern(events)
    started_at = str(events[0].get("ts") or "") if events else None
    ended_at = str(final_output_event.get("ts") or events[-1].get("ts") or "") if events else None
    approval_source = None
    if isinstance(review_meta, dict):
        approval_source = review_meta.get("approval")
    if approval_source is None and isinstance(final_output, dict):
        approval_source = final_output.get("final_approval") or final_output.get("final_status")
    status = normalize_status(str(approval_source or "partial"))

    participant_names = []
    seen_agents: set[str] = set()
    for event in events:
        if event.get("type") != "agent_assigned":
            continue
        agent_id = str(event.get("agent") or "")
        if agent_id in seen_agents:
            continue
        seen_agents.add(agent_id)
        data = event.get("data", {})
        participant_names.append(agent_name(agent_id, data if isinstance(data, dict) else None))

    unique_sources, total_sources, grade_distribution = collect_sources(
        events,
        meta_bundle,
        sources_json if isinstance(sources_json, dict) else None,
        final_output,
    )

    summary = derive_summary(
        research_meta if isinstance(research_meta, dict) else None,
        writing_meta if isinstance(writing_meta, dict) else None,
        review_meta if isinstance(review_meta, dict) else None,
        final_output,
    )
    key_findings = derive_key_findings(
        research_meta if isinstance(research_meta, dict) else None,
        writing_meta if isinstance(writing_meta, dict) else None,
        review_meta if isinstance(review_meta, dict) else None,
    )

    opinion_body = None
    for candidate in ("opinion.md", "debate-opinion.md"):
        opinion_text = read_text(case_dir / candidate)
        if opinion_text:
            opinion_body = opinion_text
            break

    report_lines: list[str] = [
        f"# Case {case_dir.name}",
        f"> {query}",
        "",
        f"- 패턴: Pattern {pattern}",
        f"- 상태: {STATUS_META.get(status, status)}",
        f"- 처리: {format_datetime(started_at)} → {format_datetime(ended_at)} ({format_duration(seconds_between(started_at, ended_at))})",
        f"- 참여: {' → '.join(participant_names) if participant_names else '참여 에이전트 기록 없음'}",
        f"- 소스: {total_sources}회 인용 ({format_grade_breakdown(grade_distribution)})",
        "",
        "## 요약",
        summary,
        "",
        "## 핵심 발견",
    ]

    if key_findings:
        for index, finding in enumerate(key_findings, start=1):
            report_lines.append(f"{index}. {finding}")
    else:
        report_lines.append("1. 핵심 발견이 별도로 기록되지 않았습니다.")

    report_lines.extend(
        [
            "",
            "## 처리 과정",
            *build_timeline_entries(events, pattern),
            "",
            "## 참여 에이전트",
            *build_agent_sections(events, meta_bundle),
            "",
            *render_review_section(
                review_meta if isinstance(review_meta, dict) else None,
                writing_meta if isinstance(writing_meta, dict) else None,
            ),
            "",
            *render_sources_section(unique_sources, total_sources, grade_distribution),
            "",
            "## 최종 의견서",
            "",
        ]
    )

    if opinion_body:
        report_lines.append(transform_opinion_markdown(opinion_body))
    else:
        report_lines.append("최종 의견서 마크다운이 없어 본문을 인라인으로 삽입하지 못했습니다.")

    report_lines.extend(["", *build_attachment_lines(case_dir, final_output), ""])

    report_path = case_dir / "case-report.md"
    report_path.write_text("\n".join(report_lines).rstrip() + "\n", encoding="utf-8")
    return report_path, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a single narrative case-report.md for one case directory.")
    parser.add_argument(
        "case_dir",
        help="Path to output/{case-id}, samples/{case-id}, or a bare CASE_ID resolved via LEGAL_ORCHESTRATOR_PRIVATE_DIR.",
    )
    args = parser.parse_args()

    case_dir = _resolve_case_dir(args.case_dir, Path.cwd().resolve())
    report_path, warnings = generate_case_report(case_dir)
    for warning in warnings:
        print(f"[warn] {warning}", file=sys.stderr)

    if report_path is None:
        return 0

    print(report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
