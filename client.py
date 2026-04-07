"""Client for the Contract Risk Analyzer environment."""
from __future__ import annotations

from .models import ContractAction, ContractObservation, ContractRiskState

try:
    from openenv.core.client import EnvClient
except Exception:  # pragma: no cover
    try:
        from openenv.core.env_client import EnvClient  # type: ignore
    except Exception:
        EnvClient = object  # type: ignore


class ContractRiskClient(EnvClient):  # type: ignore[misc]
    """Thin client wrapper. The generic EnvClient handles HTTP plumbing."""

    action_cls = ContractAction
    observation_cls = ContractObservation
    state_cls = ContractRiskState
