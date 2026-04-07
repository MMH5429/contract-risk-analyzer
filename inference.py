"""Baseline inference script for the Contract Risk Analyzer environment.

Required environment variables:
    API_BASE_URL  - LLM endpoint (OpenAI-compatible)
    MODEL_NAME    - Model identifier
    HF_TOKEN      - Auth token (used as API key for the LLM endpoint)
    ENV_BASE_URL  - (optional) URL of the running OpenEnv server. Defaults to
                    http://localhost:8000
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List

import requests

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore


ENV_BASE_URL = os.environ.get("ENV_BASE_URL", "http://localhost:8000")
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.environ.get("HF_TOKEN", os.environ.get("OPENAI_API_KEY", ""))

TASK_IDS = [
    "easy_contract_review",
    "medium_contract_review",
    "hard_contract_review",
]

SYSTEM_PROMPT = (
    "You are an expert contract risk analyst. Identify risky clauses in legal "
    "contracts. Risk types must be one of: unlimited_liability, "
    "unilateral_termination, broad_ip_assignment, weak_data_protection, "
    "non_compete, indemnification, limitation_of_liability, automatic_renewal, "
    "most_favored_nation, change_of_control, audit_rights, uncapped_penalties, "
    "governing_law. Risk levels: low, medium, high, critical. Respond ONLY with "
    "valid JSON of the form: {\"flagged\": [{\"clause_id\": str, \"risk_type\": "
    "str, \"risk_level\": str, \"explanation\": str}], \"compliance_notes\": "
    "[str]}."
)


def _post(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    r = requests.post(f"{ENV_BASE_URL}{path}", json=payload, timeout=60)
    r.raise_for_status()
    return r.json()


def _llm_client() -> Any:
    if OpenAI is None:
        raise RuntimeError("openai package not installed.")
    return OpenAI(api_key=HF_TOKEN or "sk-placeholder", base_url=API_BASE_URL)


def _call_llm(client: Any, contract_text: str, clauses: List[dict]) -> Dict[str, Any]:
    user_msg = (
        "Contract:\n" + contract_text + "\n\nClauses:\n" +
        "\n".join(f"[{c['id']}] {c['text']}" for c in clauses)
    )
    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content or "{}"
        return json.loads(content)
    except Exception as exc:  # pragma: no cover - fallback heuristic
        print(f"[WARN] LLM call failed: {exc}. Using heuristic fallback.")
        return _heuristic_fallback(clauses)


def _heuristic_fallback(clauses: List[dict]) -> Dict[str, Any]:
    keyword_map = [
        ("unlimited liability", "unlimited_liability", "critical"),
        ("terminate", "unilateral_termination", "high"),
        ("intellectual property", "broad_ip_assignment", "high"),
        ("personal data", "weak_data_protection", "high"),
        ("compete", "non_compete", "high"),
        ("indemnif", "indemnification", "high"),
        ("liability", "limitation_of_liability", "medium"),
        ("renew", "automatic_renewal", "medium"),
        ("most favored", "most_favored_nation", "medium"),
        ("change of control", "change_of_control", "medium"),
        ("audit", "audit_rights", "medium"),
        ("penalt", "uncapped_penalties", "high"),
        ("governing law", "governing_law", "medium"),
    ]
    flagged = []
    for c in clauses:
        text = c["text"].lower()
        for kw, rtype, level in keyword_map:
            if kw in text:
                flagged.append(
                    {
                        "clause_id": c["id"],
                        "risk_type": rtype,
                        "risk_level": level,
                        "explanation": f"Keyword match: {kw}",
                    }
                )
                break
    return {"flagged": flagged, "compliance_notes": ["gdpr data processing basis", "ccpa opt out right"]}


def run_task(client: Any, task_id: str) -> float:
    print(f"[START] task={task_id}")
    obs = _post("/reset", {"task_id": task_id})
    contract_text = obs.get("contract_text", "")
    clauses = obs.get("clauses", [])

    result = _call_llm(client, contract_text, clauses)
    flagged: List[dict] = result.get("flagged", [])
    compliance: List[str] = result.get("compliance_notes", [])

    for f in flagged:
        action = {
            "action_type": "analyze_clause",
            "clause_id": f.get("clause_id"),
            "risk_type": f.get("risk_type"),
            "risk_level": f.get("risk_level"),
            "explanation": f.get("explanation", ""),
        }
        _post("/step", action)
        print(f"[STEP] clause={f.get('clause_id')} risk={f.get('risk_type')}")

    final = _post(
        "/step",
        {
            "action_type": "submit_final",
            "flagged_clauses": flagged,
            "overall_risk_score": min(1.0, len(flagged) / max(1, len(clauses))),
            "compliance_notes": compliance,
        },
    )
    score = float(final.get("reward", 0.0))
    print(f"[END] task={task_id} score={score:.3f}")
    return score


def main() -> int:
    try:
        client = _llm_client()
    except Exception as exc:
        print(f"[WARN] {exc}. Falling back to heuristic-only mode.")
        client = None

    scores = []
    for tid in TASK_IDS:
        try:
            scores.append(run_task(client, tid))
        except Exception as exc:
            print(f"[ERROR] task={tid} error={exc}")
            scores.append(0.0)

    avg = sum(scores) / len(scores) if scores else 0.0
    print(f"[SUMMARY] tasks={len(scores)} avg_score={avg:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
