"""Auditable self-learning scaffold for ARIES/MALLIN.

This module supports curated knowledge records, subject coverage, provenance-aware
retrieval, and evaluation-driven improvement proposals. It does not autonomously
browse the internet, train model weights, rewrite source code, or establish
consciousness/self-awareness. Integrations must supply and review source material.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import re
from typing import Iterable


DEFAULT_SUBJECTS = (
    "mathematics", "computer_science", "engineering", "physics", "chemistry",
    "biology", "medicine_health", "psychology", "neuroscience", "language_grammar",
    "history", "geography", "economics", "law_civics", "philosophy_ethics",
    "education", "arts_literature", "business", "environment_climate",
    "statistics_data_science", "security_privacy", "social_sciences",
)


@dataclass(frozen=True)
class KnowledgeRecord:
    title: str
    subject: str
    content: str
    source_name: str
    source_url: str
    evidence_level: str = "unreviewed"
    reviewed: bool = False
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("title", "subject", "content", "source_name", "source_url"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"{name} must not be empty")
        if self.evidence_level not in {"unreviewed", "primary", "peer_reviewed", "official", "textbook"}:
            raise ValueError("unsupported evidence_level")
        if not self.source_url.startswith(("https://", "http://", "local://")):
            raise ValueError("source_url must be an http(s) or local:// reference")


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9_]+", text.lower()))


def record_id(record: KnowledgeRecord) -> str:
    """Stable content-derived ID, useful for deduplication and audit logs."""
    payload = "\n".join([
        record.title.strip(), record.subject.strip().lower(), record.content.strip(),
        record.source_name.strip(), record.source_url.strip(),
    ])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class KnowledgeLibrary:
    """In-memory reference implementation; production storage is an integration concern."""

    def __init__(self, subjects: Iterable[str] = DEFAULT_SUBJECTS) -> None:
        self.subjects = {s.strip().lower() for s in subjects if s.strip()}
        if not self.subjects:
            raise ValueError("at least one subject is required")
        self._records: dict[str, KnowledgeRecord] = {}
        self._audit: list[dict] = []

    def add(self, record: KnowledgeRecord) -> str:
        subject = record.subject.strip().lower()
        if subject not in self.subjects:
            raise ValueError(f"unknown subject '{record.subject}'; register it explicitly first")
        rid = record_id(record)
        if rid not in self._records:
            self._records[rid] = record
            self._audit.append({
                "event": "knowledge_added",
                "record_id": rid,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "reviewed": record.reviewed,
                "evidence_level": record.evidence_level,
            })
        return rid

    def register_subject(self, subject: str) -> None:
        subject = subject.strip().lower()
        if not subject:
            raise ValueError("subject must not be empty")
        self.subjects.add(subject)
        self._audit.append({
            "event": "subject_registered",
            "subject": subject,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        })

    def search(self, query: str, subject: str | None = None, limit: int = 5) -> list[dict]:
        if not query.strip():
            raise ValueError("query must not be empty")
        if limit < 1:
            raise ValueError("limit must be at least 1")
        q = _tokens(query)
        subject_filter = subject.strip().lower() if subject else None
        candidates = []
        for rid, rec in self._records.items():
            if subject_filter and rec.subject.lower() != subject_filter:
                continue
            words = _tokens(rec.title + " " + rec.content + " " + " ".join(rec.tags))
            overlap = len(q & words)
            if overlap:
                candidates.append((overlap / max(1, len(q)), rid, rec))
        candidates.sort(key=lambda x: (-x[0], x[1]))
        results = []
        for score, rid, rec in candidates[:limit]:
            results.append({
                "record_id": rid,
                "title": rec.title,
                "subject": rec.subject,
                "content": rec.content,
                "source_name": rec.source_name,
                "source_url": rec.source_url,
                "evidence_level": rec.evidence_level,
                "reviewed": rec.reviewed,
                "relevance": round(score, 4),
                "should_be_cited": True,
            })
        return results

    def subject_coverage(self) -> dict:
        counts = {s: 0 for s in sorted(self.subjects)}
        for rec in self._records.values():
            counts[rec.subject.lower()] = counts.get(rec.subject.lower(), 0) + 1
        return {
            "subject_count": len(self.subjects),
            "record_count": len(self._records),
            "subjects_with_records": sum(v > 0 for v in counts.values()),
            "subjects_without_records": [s for s, n in counts.items() if n == 0],
            "records_per_subject": counts,
            "coverage_is_not_mastery": True,
        }

    def record_feedback(self, task_id: str, outcome: str, note: str = "") -> dict:
        """Store evaluation feedback as a reviewable signal, not automatic training."""
        if not task_id.strip() or outcome not in {"pass", "fail", "partial", "needs_review"}:
            raise ValueError("task_id required and outcome must be pass/fail/partial/needs_review")
        event = {
            "event": "evaluation_feedback",
            "task_id": task_id.strip(),
            "outcome": outcome,
            "note": note.strip(),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "requires_review_before_model_change": True,
        }
        self._audit.append(event)
        return dict(event)

    def improvement_proposals(self) -> list[dict]:
        """Summarize repeated failed/partial tasks as candidates for human review."""
        counts: dict[str, dict[str, int]] = {}
        for event in self._audit:
            if event["event"] != "evaluation_feedback":
                continue
            task = event["task_id"]
            counts.setdefault(task, {"pass": 0, "fail": 0, "partial": 0, "needs_review": 0})
            counts[task][event["outcome"]] += 1
        proposals = []
        for task, values in sorted(counts.items()):
            failures = values["fail"] + values["partial"] + values["needs_review"]
            if failures:
                proposals.append({
                    "task_id": task,
                    "outcomes": values,
                    "recommendation": "review examples, identify root cause, add held-out regression tests",
                    "automatic_code_change": False,
                    "automatic_weight_update": False,
                })
        return proposals

    def audit_log(self) -> list[dict]:
        return [dict(event) for event in self._audit]
