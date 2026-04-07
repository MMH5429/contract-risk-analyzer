---
title: Contract Risk Analyzer
emoji: 📑
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 8000
pinned: false
---

# Contract Risk Analyzer

An OpenEnv environment for the Meta PyTorch Hackathon. Trains agents to identify
risky clauses in legal contracts across three difficulty tiers.

## Tasks

| ID | Difficulty | Description |
|---|---|---|
| `easy_contract_review` | easy | Single clause; identify type + risk |
| `medium_contract_review` | medium | 5–10 clauses; flag risky ones (F1) |
| `hard_contract_review` | hard | 10–15 clauses + GDPR/CCPA compliance |

## Action / Observation

**Action** (`ContractAction`):
- `action_type`: `"analyze_clause"` or `"submit_final"`
- analyze: `clause_id`, `risk_type`, `risk_level`, `explanation`
- submit: `flagged_clauses`, `overall_risk_score`, `compliance_notes`

**Observation** (`ContractObservation`): `task_id`, `difficulty`, `contract_text`,
`clauses`, `instructions`, `feedback`, `done`, `reward`, `max_steps`, `current_step`.

## Risk Clause Types

unlimited_liability, unilateral_termination, broad_ip_assignment,
weak_data_protection, non_compete, indemnification, limitation_of_liability,
automatic_renewal, most_favored_nation, change_of_control, audit_rights,
uncapped_penalties, governing_law.

## Grading

- **Easy**: 0.5 correct clause type + 0.5 correct risk flag
- **Medium**: F1 over (clause_id, risk_type) pairs
- **Hard**: 0.4 × clause F1 + 0.3 × risk-level accuracy + 0.3 × compliance accuracy

All scores clamped to [0.0, 1.0].

## Run Locally

```bash
pip install -r server/requirements.txt
uvicorn server.app:app --host 0.0.0.0 --port 8000
# in another shell:
export ENV_BASE_URL=http://localhost:8000
export API_BASE_URL=https://api.openai.com/v1
export MODEL_NAME=gpt-4o-mini
export HF_TOKEN=sk-...
python inference.py
```

## Docker

```bash
docker build -t contract-risk-analyzer .
docker run -p 8000:8000 contract-risk-analyzer
```

## Deploy to HF Spaces

```bash
openenv push --repo-id <username>/contract-risk-analyzer
```
