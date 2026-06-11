from __future__ import annotations

import csv
import json

import pytest

from or_ci.cli import main


def test_evidence_batch_writes_pack_for_existing_inputs(tmp_path) -> None:
    statement_path = tmp_path / "statement.txt"
    problem_path = tmp_path / "problem.json"
    submission_path = tmp_path / "submission.py"
    manifest_path = tmp_path / "manifest.csv"
    out_dir = tmp_path / "out"

    statement_path.write_text("Minimize price times one fixed unit.", encoding="utf-8")
    _write_cli_problem(problem_path)
    _write_cli_submission(submission_path)
    _write_manifest(
        manifest_path,
        [
            {
                "record_id": "existing-record",
                "statement": str(statement_path),
                "problem": str(problem_path),
                "submission": str(submission_path),
            }
        ],
    )

    exit_code = main(["evidence-batch", "--manifest", str(manifest_path), "--out-dir", str(out_dir)])

    assert exit_code == 0
    ledger = _read_csv(out_dir / "ledger.csv")
    assert ledger[0]["record_id"] == "existing-record"
    assert ledger[0]["row_type"] == "existing_or_ci_inputs"
    assert ledger[0]["row_status"] == "evidence_pack_written"
    assert ledger[0]["classification"] == "SUCCESS"
    pack = json.loads((out_dir / "packs" / "existing-record.json").read_text(encoding="utf-8"))
    assert pack["schema_version"] == "or_ci_evidence_pack_v1"
    assert pack["verification_report"]["problem_id"] == "BWOR-CLI"
    summary = json.loads((out_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary["schema_version"] == "or_ci_evidence_batch_v1"
    assert summary["succeeded"] == 1
    assert "OR-CI PASS is not proof of source-statement correctness." in summary["source_fidelity_boundary"]["non_claims"]


def test_evidence_batch_materializes_linear_formulation(tmp_path, require_gurobi_license) -> None:
    statement_path = tmp_path / "statement.txt"
    formulation_path = tmp_path / "formulation.json"
    manifest_path = tmp_path / "manifest.csv"
    out_dir = tmp_path / "out"

    statement_path.write_text("Choose x to maximize revenue under a capacity limit.", encoding="utf-8")
    formulation_path.write_text(
        json.dumps(
            {
                "vars": ["units"],
                "obj_declaration": {
                    "type": "objective",
                    "direction": "maximize",
                    "terms": {"units": "4"},
                },
                "const_declarations": [
                    {
                        "type": "upperbound",
                        "operator": "LESS_OR_EQUAL",
                        "var": "units",
                        "limit": "3",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    _write_manifest(
        manifest_path,
        [
            {
                "record_id": "formulation-record",
                "problem_id": "BWOR-BATCH-999",
                "statement": str(statement_path),
                "formulation": str(formulation_path),
            }
        ],
    )

    exit_code = main(["evidence-batch", "--manifest", str(manifest_path), "--out-dir", str(out_dir)])

    assert exit_code == 0
    generated_problem = json.loads((out_dir / "generated" / "formulation-record" / "problem.json").read_text(encoding="utf-8"))
    assert generated_problem["id"] == "BWOR-BATCH-999"
    assert generated_problem["instance"]["objective"]["sense"] == "max"
    assert generated_problem["instance"]["constraints"][0]["sense"] == "<="
    ledger = _read_csv(out_dir / "ledger.csv")
    assert ledger[0]["row_type"] == "materialized_formulation"
    assert ledger[0]["row_status"] == "evidence_pack_written"
    assert ledger[0]["verification_status"] == "PASS"
    assert ledger[0]["classification"] == "SUCCESS"
    pack = json.loads((out_dir / "packs" / "formulation-record.json").read_text(encoding="utf-8"))
    assert pack["answer_evidence"]["original_objective_value"] == pytest.approx(12.0)


def test_evidence_batch_ledgers_unsupported_formulation(tmp_path) -> None:
    statement_path = tmp_path / "statement.txt"
    formulation_path = tmp_path / "formulation.json"
    manifest_path = tmp_path / "manifest.csv"
    out_dir = tmp_path / "out"

    statement_path.write_text("Unsupported structured relation.", encoding="utf-8")
    formulation_path.write_text(
        json.dumps(
            {
                "vars": ["x"],
                "obj_declaration": {"type": "objective", "direction": "maximize", "terms": {"x": "1"}},
                "const_declarations": [{"type": "nonlinear_magic"}],
            }
        ),
        encoding="utf-8",
    )
    _write_manifest(
        manifest_path,
        [{"record_id": "unsupported-record", "statement": str(statement_path), "formulation": str(formulation_path)}],
    )

    exit_code = main(["evidence-batch", "--manifest", str(manifest_path), "--out-dir", str(out_dir)])

    assert exit_code == 0
    ledger = _read_csv(out_dir / "ledger.csv")
    assert ledger[0]["record_id"] == "unsupported-record"
    assert ledger[0]["row_status"] == "formulation_unsupported"
    assert ledger[0]["error_type"] == "FormulationAdapterError"
    assert "unsupported constraint type" in ledger[0]["error_message"]
    summary = json.loads((out_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary["succeeded"] == 0
    assert summary["failed"] == 1
    assert summary["counts_by_row_status"] == {"formulation_unsupported": 1}


def test_evidence_batch_uses_manual_xy_constraint_specs(tmp_path, require_gurobi_license) -> None:
    statement_path = tmp_path / "statement.txt"
    formulation_path = tmp_path / "formulation.json"
    manifest_path = tmp_path / "manifest.csv"
    manual_path = tmp_path / "manual.csv"
    out_dir = tmp_path / "out"

    statement_path.write_text("Make at least as many acai berry smoothies as banana smoothies.", encoding="utf-8")
    formulation_path.write_text(
        json.dumps(
            {
                "vars": ["acai berry smoothie", "banana smoothie"],
                "obj_declaration": {
                    "type": "objective",
                    "direction": "maximize",
                    "terms": {"acai berry smoothie": "1", "banana smoothie": "1"},
                },
                "const_declarations": [
                    {"type": "xy"},
                    {
                        "type": "sum",
                        "operator": "LESS_OR_EQUAL",
                        "limit": "2",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    _write_manifest(
        manifest_path,
        [{"record_id": "manual-record", "statement": str(statement_path), "formulation": str(formulation_path)}],
    )
    with manual_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "record_id",
                "constraint_type",
                "constraint_index",
                "left_var",
                "relation_operator",
                "right_var",
                "status",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "record_id": "manual-record",
                "constraint_type": "xy",
                "constraint_index": "0",
                "left_var": "acai berry smoothies",
                "relation_operator": "GREATER_OR_EQUAL",
                "right_var": "banana smoothie",
                "status": "active",
            }
        )

    exit_code = main(
        [
            "evidence-batch",
            "--manifest",
            str(manifest_path),
            "--manual-constraints",
            str(manual_path),
            "--out-dir",
            str(out_dir),
        ]
    )

    assert exit_code == 0
    ledger = _read_csv(out_dir / "ledger.csv")
    assert ledger[0]["row_status"] == "evidence_pack_written"
    generated_problem = json.loads((out_dir / "generated" / "manual-record" / "problem.json").read_text(encoding="utf-8"))
    assert generated_problem["instance"]["constraints"][0]["coefficients"] == {
        "acai berry smoothie": 1.0,
        "banana smoothie": -1.0,
    }


def _write_manifest(path, rows: list[dict[str, str]]) -> None:
    fieldnames = ["record_id", "problem_id", "statement", "problem", "submission", "formulation"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _read_csv(path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _cli_problem() -> dict:
    return {
        "id": "BWOR-CLI",
        "problem_type": "LP",
        "instance": {"price": 4.0},
        "metamorphic": {
            "cost_scaling": {
                "coefficient_paths": ["instance.price"],
                "factors": [2.0],
                "tolerance_abs": 1e-6,
                "tolerance_rel": 1e-6,
            }
        },
        "evaluation_only": {"answer": 4.0, "label": "not_for_build_model"},
    }


def _write_cli_problem(path) -> None:
    path.write_text(json.dumps(_cli_problem()), encoding="utf-8")


def _write_cli_submission(path) -> None:
    path.write_text(
        """
from gurobipy import GRB


class Var:
    VarName = "x"
    LB = 0.0
    UB = 1.0
    VType = GRB.CONTINUOUS


class Expr:
    def __init__(self, var, coeff):
        self.var = var
        self.coeff = coeff

    def size(self):
        return 1

    def getVar(self, index):
        return self.var

    def getCoeff(self, index):
        return self.coeff

    def getConstant(self):
        return 0.0


class Constr:
    ConstrName = "fix_x"
    Sense = "="
    RHS = 1.0

    def __init__(self, row):
        self.row = row


class FakeModel:
    NumSOS = 0
    NumQConstrs = 0
    NumGenConstrs = 0
    NumPWLObjVars = 0
    NumQNZs = 0
    IsMultiObj = 0
    ModelSense = GRB.MINIMIZE
    Status = GRB.OPTIMAL

    def __init__(self, price):
        self.x = Var()
        self.ObjVal = price
        self.objective = Expr(self.x, price)
        self.constraint = Constr(Expr(self.x, 1.0))

    def update(self):
        pass

    def getVars(self):
        return [self.x]

    def getConstrs(self):
        return [self.constraint]

    def getRow(self, constr):
        return constr.row

    def getObjective(self):
        return self.objective

    def setParam(self, *args):
        pass

    def optimize(self):
        pass


def build_model(data):
    if "evaluation_only" in data:
        raise RuntimeError("evaluation data was leaked")
    return FakeModel(data["price"])
""",
        encoding="utf-8",
    )
