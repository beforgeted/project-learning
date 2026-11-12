"""Summarize explicit acceptance scope from pinned local reports; no evaluations are run."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
from evaluate_checks import at_pointer, parse_json, pointer_tokens, text_id

VERSION = "0.4.0"
REPORT_STATES = {"pass", "fail", "not_run", "unknown", "error", "incomplete"}
PENDING = {"not_run", "unknown", "error", "incomplete"}


def validate(plan):
    fields = {"schema_version", "plan_id", "revision", "subject", "criteria_authority",
              "authority_ref", "coverage", "excluded_scope", "checks"}
    if not isinstance(plan, dict) or plan.get("schema_version") != "project-learning/acceptance-plan/1":
        raise ValueError("Unsupported acceptance plan schema")
    if set(plan) - fields or not all(text_id(plan.get(k)) for k in ("plan_id", "revision", "authority_ref")):
        raise ValueError("Unknown plan field or missing plan identity/authority reference")
    subject = plan.get("subject")
    if not isinstance(subject, dict) or not all(text_id(subject.get(k)) for k in ("record_id", "revision", "run_id", "data_scope", "acceptance_scope")):
        raise ValueError("Subject needs record_id, revision, run_id, data_scope, acceptance_scope")
    if plan.get("criteria_authority") not in ("agreed", "proposed", "unknown"):
        raise ValueError("Invalid criteria_authority")
    if plan.get("coverage") not in ("complete_for_declared_scope", "partial", "unknown"):
        raise ValueError("Invalid coverage")
    if not isinstance(plan.get("excluded_scope"), list) or not all(text_id(v) for v in plan["excluded_scope"]):
        raise ValueError("excluded_scope must be an explicit array of descriptions")
    checks = plan.get("checks")
    if not isinstance(checks, list) or not checks:
        raise ValueError("At least one check is required")
    seen = set()
    for check in checks:
        if not isinstance(check, dict) or set(check) - {"id", "purpose", "required", "result_ref", "status", "reason"}:
            raise ValueError("Invalid check fields")
        if not all(text_id(check.get(k)) for k in ("id", "purpose")) or type(check.get("required")) is not bool:
            raise ValueError("Check needs id, purpose and boolean required")
        if check["id"] in seen:
            raise ValueError("Duplicate check id")
        seen.add(check["id"])
        if "result_ref" in check:
            ref = check["result_ref"]
            if "status" in check or "reason" in check or not isinstance(ref, dict) or set(ref) != {"path", "sha256", "pointer"}:
                raise ValueError("Result reference must be exclusive and contain path, sha256, pointer")
            if not text_id(ref["path"]) or not isinstance(ref["sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", ref["sha256"]):
                raise ValueError("Result reference needs a path and lowercase SHA-256")
            pointer_tokens(ref["pointer"])
        elif check.get("status") not in ("not_run", "unknown", "error") or not text_id(check.get("reason")):
            raise ValueError("Executed pass/fail requires a report; pending state requires a reason")
    if not any(c["required"] for c in checks):
        raise ValueError("At least one required check is necessary for acceptance")


def summarize(plan, directory):
    validate(plan)
    results = []
    for check in plan["checks"]:
        result = {k: check[k] for k in ("id", "purpose", "required")}
        if "result_ref" not in check:
            result.update({k: check[k] for k in ("status", "reason")})
        else:
            ref = check["result_ref"]
            result["result_ref"] = ref
            try:
                path = directory / ref["path"]
                raw = path.read_bytes()
                actual_hash = hashlib.sha256(raw).hexdigest()
                result["observed_sha256"] = actual_hash
                if actual_hash != ref["sha256"]:
                    raise ValueError("Referenced report hash changed")
                value = at_pointer(parse_json(raw.decode("utf-8-sig")), ref["pointer"])
                if not isinstance(value, str) or value not in REPORT_STATES:
                    raise ValueError("Referenced status is missing or unsupported")
                result.update(status=value, reason="Read pinned report status")
            except (OSError, ValueError, TypeError, OverflowError) as exc:
                result.update(status="error", reason=str(exc))
        results.append(result)
    required = [r for r in results if r["required"]]
    failures = [r["id"] for r in required if r["status"] == "fail"]
    pending = [r["id"] for r in required if r["status"] in PENDING]
    checks_status = "fail" if failures else "incomplete" if pending else "pass"
    if failures:
        acceptance = "fail"
    elif pending or plan["coverage"] == "partial":
        acceptance = "incomplete"
    elif plan["coverage"] == "unknown" or plan["criteria_authority"] == "unknown":
        acceptance = "unknown"
    elif plan["criteria_authority"] == "proposed":
        acceptance = "provisional_pass"
    else:
        acceptance = "pass"
    return {"evaluator": "project-learning/scoped-acceptance", "evaluator_version": VERSION,
            "checked_at": datetime.now(timezone.utc).isoformat(), "plan_id": plan["plan_id"],
            "plan_revision": plan["revision"], "subject": plan["subject"],
            "criteria_authority": plan["criteria_authority"], "authority_ref": plan["authority_ref"],
            "coverage": plan["coverage"], "excluded_scope": plan["excluded_scope"],
            "checks_status": checks_status, "acceptance_status": acceptance,
            "required_execution_complete": not pending, "required_failures": failures,
            "required_pending": pending, "results": results,
            "limitations": "Caller declares report-to-subject mapping and completeness. Hash/status checks do not verify semantic alignment or authorize release."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        raw = args.plan.read_bytes()
        report = summarize(parse_json(raw.decode("utf-8-sig")), args.plan.resolve().parent)
        report["plan_sha256"] = hashlib.sha256(raw).hexdigest()
        rendered = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        with args.output.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(rendered)
        if args.output.read_text(encoding="utf-8") != rendered:
            raise OSError("Report readback mismatch")
        print(json.dumps({"report": str(args.output.resolve()), "checks_status": report["checks_status"],
                          "acceptance_status": report["acceptance_status"], "required_pending": report["required_pending"]}, ensure_ascii=False))
        return 0 if report["acceptance_status"] == "pass" else 1 if report["acceptance_status"] == "fail" else 2
    except (OSError, ValueError, TypeError, OverflowError) as exc:
        print(f"Acceptance summary error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
