# Detail Quality Compiler

A local construction-detail quality system that checks synthetic detail libraries for reuse readiness, missing metadata, and risky documentation gaps.

`pirros-detail-quality-compiler` favors explicit fixtures, deterministic checks, and reviewable artifacts over hidden services or live data.

## Intent

Detail Quality Compiler: From Project History to Firm-Wide Standards.

## What the code proves

- Synthetic detail records with discipline, assembly, metadata, and review outcomes.
- Quality scoring for reuse candidates, missing context, and documentation drift.
- Evidence-backed recommendations and static dashboard output.

## Local run

```bash
uv sync
uv run app init-demo
uv run app ingest fixtures/
uv run app analyze
uv run app verify
uv run app dashboard
uv run app benchmark
uv run app export-demo-pack
uv run pytest -q
uv run ruff check .
```

## Produced files

- `outputs/dashboard.html`
- `outputs/decision_report.md`
- `outputs/evidence_graph.mmd`
- `outputs/risk_or_quality_report.csv`
- `outputs/benchmark.md`
- `outputs/demo_pack.md`

## Gatekeeping

```bash
uv run ruff check .
uv run pytest -q
uv run app verify
```

## Operational boundary

The `pirros-detail-quality-compiler` public surface is source, tests, lockfile, and docs. It does not need credentials, browser state, customer records, or hosted services.
