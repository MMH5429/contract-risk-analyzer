"""Grading functions for contract risk analyzer tasks."""
from __future__ import annotations

from typing import Dict, List


_EPS = 1e-3


def _clamp(x: float) -> float:
    """Clamp to the open interval (0, 1) as required by the grader spec."""
    return max(_EPS, min(1.0 - _EPS, float(x)))


def grade_easy(agent: dict, gold: dict) -> float:
    """0.5 for correct clause type + 0.5 for correct risk flag."""
    if not isinstance(agent, dict) or not isinstance(gold, dict):
        return _clamp(0.0)
    score = 0.0
    if agent.get("risk_type") == gold.get("clause_type"):
        score += 0.5
    agent_risky = bool(agent.get("is_risky", agent.get("risk_level") in {"medium", "high", "critical"}))
    if agent_risky == bool(gold.get("is_risky", True)):
        score += 0.5
    return _clamp(score)


def _to_set(items: List[dict]) -> set:
    out = set()
    for it in items or []:
        cid = it.get("clause_id")
        rtype = it.get("risk_type")
        if cid and rtype:
            out.add((cid, rtype))
    return out


def grade_medium(agent_flagged: List[dict], gold_flagged: List[dict]) -> float:
    """F1 of (clause_id, risk_type) pairs."""
    a = _to_set(agent_flagged)
    g = _to_set(gold_flagged)
    if not g and not a:
        return _clamp(1.0)
    if not a or not g:
        return _clamp(0.0)
    tp = len(a & g)
    if tp == 0:
        return _clamp(0.0)
    precision = tp / len(a)
    recall = tp / len(g)
    f1 = 2 * precision * recall / (precision + recall)
    return _clamp(f1)


def grade_hard(
    agent_flagged: List[dict],
    gold_flagged: List[dict],
    agent_compliance: List[str],
    gold_compliance: Dict[str, dict],
) -> float:
    """0.4 * clause F1 + 0.3 * risk-level accuracy + 0.3 * compliance accuracy."""
    clause_f1 = grade_medium(agent_flagged, gold_flagged)

    # Risk-level accuracy on intersected clauses
    gold_levels = {c.get("clause_id"): c.get("risk_level") for c in gold_flagged or []}
    agent_levels = {c.get("clause_id"): c.get("risk_level") for c in agent_flagged or []}
    matched = [cid for cid in gold_levels if cid in agent_levels]
    if matched:
        correct = sum(1 for cid in matched if gold_levels[cid] == agent_levels[cid])
        level_acc = correct / len(matched)
    else:
        level_acc = 0.0 if gold_levels else 1.0

    # Compliance accuracy: how many required compliance keys did the agent mention?
    notes_text = " ".join((agent_compliance or [])).lower()
    required_keys: List[str] = []
    for regime, checks in (gold_compliance or {}).items():
        for key, val in (checks or {}).items():
            if isinstance(val, dict) and val.get("required"):
                required_keys.append(f"{regime}:{key}")
    if required_keys:
        hits = 0
        for rk in required_keys:
            regime, key = rk.split(":", 1)
            if regime in notes_text and key.replace("_", " ") in notes_text:
                hits += 1
            elif key.replace("_", " ") in notes_text:
                hits += 1
        comp_acc = hits / len(required_keys)
    else:
        comp_acc = 1.0

    score = 0.4 * clause_f1 + 0.3 * level_acc + 0.3 * comp_acc
    return _clamp(score)
