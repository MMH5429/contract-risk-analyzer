"""Optional helper to refresh tier data from the CUAD dataset.

This is provided for reproducibility. The repo ships with hand-curated JSON
files in data/{easy,medium,hard}, so running this script is NOT required to
use the environment.

Usage:
    pip install datasets
    python scripts/prepare_cuad_data.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

CUAD_TO_RISK_TYPE = {
    "Cap On Liability": "limitation_of_liability",
    "Uncapped Liability": "unlimited_liability",
    "Termination For Convenience": "unilateral_termination",
    "Ip Ownership Assignment": "broad_ip_assignment",
    "Non-Compete": "non_compete",
    "Indemnification": "indemnification",
    "Renewal Term": "automatic_renewal",
    "Most Favored Nation": "most_favored_nation",
    "Change Of Control": "change_of_control",
    "Audit Rights": "audit_rights",
    "Liquidated Damages": "uncapped_penalties",
    "Governing Law": "governing_law",
}


def main() -> None:
    try:
        from datasets import load_dataset
    except ImportError:
        print("Install `datasets` to run this script: pip install datasets")
        return

    ds = load_dataset("theatticusproject/cuad-qa", split="train")
    print(f"Loaded {len(ds)} CUAD examples.")
    print("Hand-curated tier files already exist under data/. This script is "
          "a placeholder for richer regeneration logic.")


if __name__ == "__main__":
    main()
