"""
Persistent Analysis History Store
==================================
Saves RFP analysis results to a JSON file so they survive server restarts.
Used by:
  - POST /saved-analyses  (manual save)
  - POST /rfps/analyze    (auto-save)
  - GET  /saved-analyses   (list for History page & Bid Generator)

File location: database/db_rfp/analysis_history.json

Thread-safe via a reentrant lock.
"""

import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_HISTORY_DIR = Path(__file__).parent / "db_rfp"
_HISTORY_FILE = _HISTORY_DIR / "analysis_history.json"
_lock = RLock()

# Keep a lightweight index in memory for fast listing
_index_cache: Optional[List[Dict[str, Any]]] = None


def _ensure_dir():
    _HISTORY_DIR.mkdir(parents=True, exist_ok=True)


# ── Low-level I/O ────────────────────────────────────────────────────

def _load_all() -> List[Dict[str, Any]]:
    """Load the full history list from disk."""
    if not _HISTORY_FILE.exists():
        return []
    try:
        with open(_HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception as exc:
        logger.error(f"Failed to read analysis history: {exc}")
        return []


def _save_all(items: List[Dict[str, Any]]):
    """Persist the full list to disk (atomic-ish)."""
    _ensure_dir()
    tmp = str(_HISTORY_FILE) + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, ensure_ascii=False, default=str)
        if os.path.exists(str(_HISTORY_FILE)):
            os.replace(tmp, str(_HISTORY_FILE))
        else:
            os.rename(tmp, str(_HISTORY_FILE))
    except Exception as exc:
        logger.error(f"Failed to persist analysis history: {exc}")
        if os.path.exists(tmp):
            os.unlink(tmp)


def _invalidate_cache():
    global _index_cache
    _index_cache = None


# ── Public API ───────────────────────────────────────────────────────

def save_analysis(
    analysis_result: Dict[str, Any],
    file_name: str = "Unknown",
    saved_by: str = "system",
    source: str = "manual",  # 'manual' | 'auto'
) -> Dict[str, Any]:
    """
    Save an analysis result. Returns the saved record (lightweight, without
    the full analysis_result — that's stored on disk only).
    """
    analysis_id = analysis_result.get("analysis_id") or f"SA-{uuid.uuid4().hex[:8].upper()}"

    rfp_summary = analysis_result.get("rfp_summary") or {}
    comparisons = analysis_result.get("comparisons") or []
    matched_count = len([c for c in comparisons if c.get("match_count", 0) > 0])
    total_reqs = analysis_result.get("total_requirements", len(comparisons))

    # Confidence = avg of top match scores
    confidences = []
    for c in comparisons:
        matches = c.get("matches") or []
        if matches:
            top_score = matches[0].get("match_score") or matches[0].get("score", 0)
            confidences.append(top_score)
    avg_confidence = round(sum(confidences) / len(confidences), 1) if confidences else 0

    # OEM summary
    oem_summary = analysis_result.get("oem_summary") or {}
    oem_names = list(oem_summary.keys()) if isinstance(oem_summary, dict) else []

    record = {
        "id": analysis_id,
        "file_name": file_name,
        "rfp_title": rfp_summary.get("boq_title") or rfp_summary.get("title") or file_name,
        "organization": rfp_summary.get("organization") or rfp_summary.get("buyer") or "",
        "detected_application": analysis_result.get("detected_application", ""),
        "total_requirements": total_reqs,
        "matched": matched_count,
        "confidence": avg_confidence,
        "oem_names": oem_names,
        "agent_mode": (analysis_result.get("agent_info") or {}).get("agent_mode", "unknown"),
        "status": "completed" if matched_count > 0 else ("failed" if total_reqs == 0 else "partial"),
        "saved_at": datetime.now().isoformat(),
        "saved_by": saved_by,
        "source": source,
        # Full analysis result stored for bid generation
        "analysis_result": analysis_result,
    }

    with _lock:
        items = _load_all()
        # Replace if same analysis_id already exists
        items = [it for it in items if it.get("id") != analysis_id]
        items.insert(0, record)  # newest first
        # Cap at 200 analyses
        if len(items) > 200:
            items = items[:200]
        _save_all(items)
        _invalidate_cache()

    logger.info(f"Analysis saved: {analysis_id} — {file_name} ({matched_count}/{total_reqs} matched, {avg_confidence}% confidence)")
    return _to_summary(record)


def list_analyses(include_result: bool = False) -> List[Dict[str, Any]]:
    """
    List all saved analyses, newest first.
    By default returns lightweight summaries (no analysis_result).
    """
    global _index_cache

    with _lock:
        if _index_cache is not None and not include_result:
            return _index_cache

        items = _load_all()
        if include_result:
            return items

        summaries = [_to_summary(it) for it in items]
        _index_cache = summaries
        return summaries


def get_analysis(analysis_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific analysis by ID (includes full analysis_result)."""
    with _lock:
        items = _load_all()
    for it in items:
        if it.get("id") == analysis_id:
            return it
    return None


def delete_analysis(analysis_id: str) -> bool:
    """Delete an analysis by ID. Returns True if found."""
    with _lock:
        items = _load_all()
        before = len(items)
        items = [it for it in items if it.get("id") != analysis_id]
        if len(items) < before:
            _save_all(items)
            _invalidate_cache()
            logger.info(f"Analysis deleted: {analysis_id}")
            return True
    return False


def get_count() -> int:
    with _lock:
        return len(_load_all())


def _to_summary(record: Dict[str, Any]) -> Dict[str, Any]:
    """Strip the heavy analysis_result for listing endpoints."""
    return {k: v for k, v in record.items() if k != "analysis_result"}
