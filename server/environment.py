"""Contract Risk Analyzer environment."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

try:
    from openenv.core.env_server import Environment
except Exception:  # pragma: no cover
    class Environment:  # type: ignore
        pass

import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import (  # noqa: E402
    ContractAction,
    ContractObservation,
    ContractRiskState,
)
from .grader import grade_easy, grade_hard, grade_medium

DATA_PATH = Path(os.environ.get("CONTRACT_DATA_PATH", str(Path(__file__).resolve().parent.parent / "data")))


def _load_json(p: Path) -> dict:
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


class ContractRiskEnvironment(Environment):  # type: ignore[misc]
    """Episodic environment for contract risk analysis."""

    def __init__(self) -> None:
        super().__init__() if hasattr(super(), "__init__") else None
        self.tasks: list = _load_json(DATA_PATH / "tasks.json")["tasks"]
        self._state = ContractRiskState()
        self._episode_data: dict = {}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _select_task(self, episode_id: Optional[int], task_id: Optional[str]) -> dict:
        if task_id:
            for t in self.tasks:
                if t["task_id"] == task_id:
                    return t
        if episode_id is not None:
            return self.tasks[int(episode_id) % len(self.tasks)]
        return self.tasks[0]

    def _load_episode(self, task: dict) -> dict:
        data_dir = DATA_PATH / task["data_dir"]
        files = sorted(data_dir.glob("*.json"))
        if not files:
            raise RuntimeError(f"No data files in {data_dir}")
        return _load_json(files[0])

    # ------------------------------------------------------------------
    # OpenEnv API
    # ------------------------------------------------------------------
    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[int] = None,
        task_id: Optional[str] = None,
        **kwargs: Any,
    ) -> ContractObservation:
        task = self._select_task(episode_id, task_id)
        episode = self._load_episode(task)
        self._episode_data = episode

        clauses = episode.get("clauses")
        if clauses is None:
            # Easy: single clause
            clauses = [{"id": "c1", "text": episode["clause_text"]}]
            contract_text = episode["clause_text"]
        else:
            contract_text = episode.get("contract_text", "\n\n".join(c["text"] for c in clauses))

        gold = {
            "clause_type": episode.get("clause_type"),
            "is_risky": episode.get("is_risky", True),
            "risk_level": episode.get("risk_level"),
            "flagged": episode.get("flagged_clauses", []),
            "compliance": episode.get("compliance_requirements", {}),
        }

        self._state = ContractRiskState(
            task_id=task["task_id"],
            difficulty=task["difficulty"],
            contract_title=episode.get("title", task["task_id"]),
            gold_annotations=gold,
            agent_analyses=[],
            current_step=0,
            max_steps=task["max_steps"],
            done=False,
        )

        return ContractObservation(
            task_id=task["task_id"],
            difficulty=task["difficulty"],
            contract_text=contract_text,
            clauses=clauses,
            instructions=(
                "Analyze each clause. Use action_type='analyze_clause' to log findings, "
                "then action_type='submit_final' with flagged_clauses=[{clause_id, risk_type, risk_level}] "
                "and compliance_notes=[...] (hard tier)."
            ),
            feedback="Episode started.",
            done=False,
            reward=0.0,
            max_steps=task["max_steps"],
            current_step=0,
        )

    def step(self, action: ContractAction, **kwargs: Any) -> ContractObservation:
        if self._state.done:
            return self._observation(feedback="Episode already done.", reward=0.0)

        self._state.current_step += 1

        if action.action_type == "analyze_clause":
            self._state.agent_analyses.append(
                {
                    "clause_id": action.clause_id,
                    "risk_type": action.risk_type,
                    "risk_level": action.risk_level,
                    "explanation": action.explanation or "",
                }
            )
            feedback = f"Logged analysis for clause {action.clause_id}."
            if self._state.current_step >= self._state.max_steps:
                return self._auto_finalize("Max steps reached; auto-grading.")
            return self._observation(feedback=feedback, reward=0.0)

        if action.action_type == "submit_final":
            return self._finalize(action)

        return self._observation(feedback=f"Unknown action_type: {action.action_type}", reward=0.0)

    def _finalize(self, action: ContractAction) -> ContractObservation:
        difficulty = self._state.difficulty
        gold = self._state.gold_annotations

        if difficulty == "easy":
            agent_pick = (action.flagged_clauses or [{}])[0] if action.flagged_clauses else (
                self._state.agent_analyses[-1] if self._state.agent_analyses else {}
            )
            reward = grade_easy(agent_pick, gold)
        elif difficulty == "medium":
            reward = grade_medium(action.flagged_clauses or [], gold.get("flagged", []))
        else:  # hard
            reward = grade_hard(
                action.flagged_clauses or [],
                gold.get("flagged", []),
                action.compliance_notes or [],
                gold.get("compliance", {}),
            )

        self._state.done = True
        return self._observation(feedback=f"Final score: {reward:.3f}", reward=float(reward), done=True)

    def _auto_finalize(self, msg: str) -> ContractObservation:
        difficulty = self._state.difficulty
        gold = self._state.gold_annotations
        flagged = [
            {"clause_id": a["clause_id"], "risk_type": a["risk_type"], "risk_level": a["risk_level"]}
            for a in self._state.agent_analyses
        ]
        if difficulty == "easy":
            reward = grade_easy(self._state.agent_analyses[-1] if self._state.agent_analyses else {}, gold)
        elif difficulty == "medium":
            reward = grade_medium(flagged, gold.get("flagged", []))
        else:
            reward = grade_hard(flagged, gold.get("flagged", []), [], gold.get("compliance", {}))
        self._state.done = True
        return self._observation(feedback=msg, reward=float(reward), done=True)

    def _observation(self, feedback: str, reward: float, done: bool = False) -> ContractObservation:
        return ContractObservation(
            task_id=self._state.task_id,
            difficulty=self._state.difficulty,
            contract_text="",
            clauses=[],
            instructions="",
            feedback=feedback,
            done=done or self._state.done,
            reward=reward,
            max_steps=self._state.max_steps,
            current_step=self._state.current_step,
        )

    @property
    def state(self) -> ContractRiskState:
        return self._state


def env_factory() -> ContractRiskEnvironment:
    return ContractRiskEnvironment()
