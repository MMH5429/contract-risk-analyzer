"""FastAPI app entry point for the Contract Risk Analyzer environment."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI  # noqa: E402

from models import ContractAction  # noqa: E402

from .environment import env_factory  # noqa: E402

app = FastAPI(title="contract_risk_analyzer", version="0.1.0")
_env = env_factory()


@app.get("/health")
def health() -> dict:
    return {"status": "healthy"}


@app.get("/")
def root() -> dict:
    return {"name": "contract_risk_analyzer", "endpoints": ["/health", "/reset", "/step", "/state"]}


@app.post("/reset")
def reset(payload: dict | None = None) -> dict:
    payload = payload or {}
    obs = _env.reset(**payload)
    return obs.model_dump()


@app.post("/step")
def step(payload: dict) -> dict:
    action = ContractAction(**payload)
    obs = _env.step(action)
    return obs.model_dump()


@app.get("/state")
def state() -> dict:
    return _env.state.model_dump()


def main() -> None:
    """Entry point for `python -m server.app` and the [project.scripts] server."""
    import uvicorn

    uvicorn.run(
        "server.app:app",
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "8000")),
    )


if __name__ == "__main__":
    main()
