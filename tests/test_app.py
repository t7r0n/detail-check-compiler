from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from app import core


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def reset_runtime() -> None:
    for name in ["fixtures", "data", "outputs"]:
        path = PROJECT_ROOT / name
        if path.exists():
            shutil.rmtree(path)


def test_end_to_end_flow() -> None:
    reset_runtime()
    created = core.init_demo(PROJECT_ROOT, seed=123, records=64)
    assert created["records"] == 64
    ingest = core.ingest(PROJECT_ROOT)
    assert ingest["records"] == 64
    analysis = core.analyze(PROJECT_ROOT)
    assert analysis["clusters"]
    verification = core.verify(PROJECT_ROOT)
    assert verification["checks"]["evidence_claims_supported"] is True
    dash = core.dashboard(PROJECT_ROOT)
    assert Path(dash["dashboard"]).exists()
    bench = core.benchmark(PROJECT_ROOT)
    assert bench["target_records"] >= 500
    pack = core.export_demo_pack(PROJECT_ROOT)
    assert Path(pack["demo_pack"]).exists()


def test_malformed_fixture_rejected(tmp_path: Path) -> None:
    bad = tmp_path / "fixtures"
    bad.mkdir()
    (bad / "records.jsonl").write_text(json.dumps({"record_id": "missing_fields"}) + "\n")
    with pytest.raises(core.DataContractError):
        core.ingest(PROJECT_ROOT, bad)


def test_unsupported_claim_rejected() -> None:
    reset_runtime()
    core.init_demo(PROJECT_ROOT, seed=321, records=32)
    core.ingest(PROJECT_ROOT)
    core.analyze(PROJECT_ROOT)
    (PROJECT_ROOT / "outputs" / "unsupported_claim.md").write_text(
        "CLAIM: this should be rejected because it has no evidence marker\n",
        encoding="utf-8",
    )
    with pytest.raises(core.VerificationError):
        core.verify(PROJECT_ROOT)


def test_unknown_evidence_rejected() -> None:
    reset_runtime()
    core.init_demo(PROJECT_ROOT, seed=222, records=32)
    core.ingest(PROJECT_ROOT)
    core.analyze(PROJECT_ROOT)
    (PROJECT_ROOT / "outputs" / "unknown_evidence.md").write_text(
        "CLAIM: this cites nonexistent evidence. [EVID: ev_missing]\n",
        encoding="utf-8",
    )
    with pytest.raises(core.VerificationError):
        core.verify(PROJECT_ROOT)


def test_cli_ingest_accepts_documented_positional_argument() -> None:
    reset_runtime()
    first = subprocess.run(
        ["uv", "run", "app", "init-demo"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "records" in first.stdout
    second = subprocess.run(
        ["uv", "run", "app", "ingest", "fixtures/"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "records" in second.stdout



def test_domain_specific_engine_outputs() -> None:
    reset_runtime()
    created = core.init_demo(PROJECT_ROOT, seed=55, records=40)
    assert created["domain_cases"] >= 5
    ingest = core.ingest(PROJECT_ROOT)
    assert ingest["domain_cases"] >= 5
    analysis = core.analyze(PROJECT_ROOT)
    domain = analysis["domain"]
    assert domain["case_count"] >= 5
    assert domain["checks"]
    assert domain["missing_or_blocked_count"] >= 1
    assert all(case["evidence_id"].startswith("domain_ev_") for case in domain["cases"])
    verification = core.verify(PROJECT_ROOT)
    assert verification["checks"]["domain_cases_present"] is True


def test_domain_evidence_ids_are_accepted_by_verifier() -> None:
    reset_runtime()
    core.init_demo(PROJECT_ROOT, seed=66, records=40)
    core.ingest(PROJECT_ROOT)
    analysis = core.analyze(PROJECT_ROOT)
    evidence_id = analysis["domain"]["cases"][0]["evidence_id"]
    (PROJECT_ROOT / "outputs" / "domain_claim.md").write_text(
        f"CLAIM: domain recommendation is evidence backed. [EVID: {evidence_id}]\n",
        encoding="utf-8",
    )
    verification = core.verify(PROJECT_ROOT)
    assert verification["checks"]["evidence_claims_supported"] is True


def test_dashboard_escapes_fixture_html() -> None:
    reset_runtime()
    core.init_demo(PROJECT_ROOT, seed=77, records=24)
    records_path = PROJECT_ROOT / "fixtures" / "records.jsonl"
    first_line, *rest = records_path.read_text(encoding="utf-8").splitlines()
    payload = json.loads(first_line)
    payload["scenario"] = "<script>alert('xss')</script>"
    records_path.write_text("\n".join([json.dumps(payload), *rest]) + "\n", encoding="utf-8")
    core.ingest(PROJECT_ROOT)
    core.analyze(PROJECT_ROOT)
    dashboard = Path(core.dashboard(PROJECT_ROOT)["dashboard"]).read_text(encoding="utf-8")
    assert "<script>alert('xss')</script>" not in dashboard
    assert "&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;" in dashboard
