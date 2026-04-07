"""Pydantic models for the Contract Risk Analyzer environment."""
from __future__ import annotations

from typing import Any, List, Optional

from pydantic import Field

try:
    from openenv.core.env_server import Action, Observation, State
except Exception:  # pragma: no cover - fallback if openenv import path differs
    from pydantic import BaseModel as _BM

    class Action(_BM):  # type: ignore
        pass

    class Observation(_BM):  # type: ignore
        pass

    class State(_BM):  # type: ignore
        pass


RISK_CLAUSE_TYPES = [
    "unlimited_liability",
    "unilateral_termination",
    "broad_ip_assignment",
    "weak_data_protection",
    "non_compete",
    "indemnification",
    "limitation_of_liability",
    "automatic_renewal",
    "most_favored_nation",
    "change_of_control",
    "audit_rights",
    "uncapped_penalties",
    "governing_law",
]

RISK_LEVELS = ["low", "medium", "high", "critical"]


class FlaggedClause(Action):
    clause_id: str
    risk_type: str
    risk_level: str
    explanation: str = ""


class ContractAction(Action):
    """Action submitted by the agent."""

    action_type: str = Field(..., description="'analyze_clause' or 'submit_final'")
    # analyze_clause fields
    clause_id: Optional[str] = None
    risk_type: Optional[str] = None
    risk_level: Optional[str] = None
    explanation: Optional[str] = None
    # submit_final fields
    flagged_clauses: Optional[List[dict]] = None
    overall_risk_score: Optional[float] = None
    compliance_notes: Optional[List[str]] = None


class ContractObservation(Observation):
    """Observation returned by the environment."""

    task_id: str = ""
    difficulty: str = ""
    contract_text: str = ""
    clauses: List[dict] = Field(default_factory=list)
    instructions: str = ""
    feedback: str = ""
    done: bool = False
    reward: float = 0.0
    max_steps: int = 0
    current_step: int = 0


class ContractRiskState(State):
    """Internal episode state."""

    task_id: str = ""
    difficulty: str = ""
    contract_title: str = ""
    gold_annotations: dict = Field(default_factory=dict)
    agent_analyses: List[dict] = Field(default_factory=list)
    current_step: int = 0
    max_steps: int = 0
    done: bool = False
