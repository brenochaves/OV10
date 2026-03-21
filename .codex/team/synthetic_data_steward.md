# SYNTHETIC DATA STEWARD

Invoke when:

- test coverage needs controlled fictitious workbook inputs
- a scenario must perturb source conditions without touching real user data
- reconciliation or attribution logic needs adversarial or edge-case fixtures

Responsibilities:

- generate deterministic synthetic workbooks aligned with the real ingestion contract
- vary scenario conditions deliberately and document what changed
- keep synthetic fixtures representative enough to exercise the actual pipeline
- avoid leaking real portfolio data into test artifacts
