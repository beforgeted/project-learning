"""Offline output-contract checks; no network, model calls, or arbitrary execution."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import sys

VERSION = "0.4.0"
KINDS = {"required_keys", "nonempty", "equals", "one_of", "subset_of", "human", "model"}
MISSING = object()


def reject_constant(value):
    raise ValueError("Non-finite JSON number")


def finite_float(value):
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError("Non-finite JSON number")
    return parsed


def unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("Duplicate JSON object key")
        obj[key] = value
    return obj


def parse_json(text):
    return json.loads(text, parse_constant=reject_constant, parse_float=finite_float,
                      object_pairs_hook=unique_object)


def text_id(value):
    return isinstance(value, str) and bool(value.strip())


def pointer_tokens(pointer):
    if not isinstance(pointer, str) or (pointer and not pointer.startswith("/")):
        raise ValueError("Check path must be a JSON Pointer relative to output")
    if re.search(r"~(?![01])", pointer):
        raise ValueError("Invalid JSON Pointer escape")
    return [] if not pointer else [p.replace("~1", "/").replace("~0", "~") for p in pointer[1:].split("/")]


def at_pointer(value, pointer):
    for token in pointer_tokens(pointer):
        if isinstance(value, dict):
            value = value.get(token, MISSING)
        elif isinstance(value, list) and re.fullmatch(r"0|[1-9][0-9]*", token):
            index = int(token)
            value = value[index] if index < len(value) else MISSING
        else:
            return MISSING
    return value


def equal_json(left, right):
    if type(left) is bool or type(right) is bool:
        return type(left) is type(right) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(equal_json(left[k], right[k]) for k in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(equal_json(a, b) for a, b in zip(left, right))
    return left == right


def validate_config(config):
    if not isinstance(config, dict) or config.get("schema_version") != "project-learning/checks/1":
        raise ValueError("Unsupported checks schema")
    if set(config) - {"schema_version", "version", "rule_ref", "checks"}:
        raise ValueError("Unknown checks configuration field")
    if not all(text_id(config.get(k)) for k in ("version", "rule_ref")):
        raise ValueError("Checks version and rule_ref are required")
    checks = config.get("checks")
    if not isinstance(checks, list) or not checks:
        raise ValueError("At least one check is required")
    seen = set()
    extras = {"equals": {"expected"}, "one_of": {"values"}, "subset_of": {"values"}, "required_keys": {"keys"}}
    for check in checks:
        if not isinstance(check, dict) or not text_id(check.get("id")):
            raise ValueError("Every check needs a nonempty id")
        if check["id"] in seen:
            raise ValueError("Duplicate check id")
        seen.add(check["id"])
        kind = check.get("kind")
        if not isinstance(kind, str) or kind not in KINDS:
            raise ValueError("Unsupported check kind")
        if set(check) - ({"id", "kind", "path", "description"} | extras.get(kind, set())):
            raise ValueError("Unexpected check field")
        pointer_tokens(check.get("path", ""))
        if kind == "equals" and "expected" not in check:
            raise ValueError("equals requires expected, including explicit null")
        if kind in {"one_of", "subset_of", "required_keys"}:
            key = "keys" if kind == "required_keys" else "values"
            values = check.get(key)
            if not isinstance(values, list) or not values:
                raise ValueError("Check requires a nonempty keys/values array")
            if kind == "required_keys" and not all(isinstance(k, str) for k in values):
                raise ValueError("required_keys entries must be strings")


def validate_samples(samples):
    if not samples:
        raise ValueError("Empty sample set cannot pass acceptance")
    seen = set()
    for row in samples:
        if not isinstance(row, dict) or not all(text_id(row.get(k)) for k in ("sample_id", "run_id", "attempt_id")):
            raise ValueError("Sample needs sample_id, run_id and attempt_id")
        key = (row["sample_id"], row["run_id"], row["attempt_id"])
        if key in seen:
            raise ValueError("Duplicate sample/run/attempt; reconcile duplicate reporting first")
        seen.add(key)
        if row.get("execution_status") not in ("completed", "failed", "not_run"):
            raise ValueError("Invalid sample execution_status")
        if row.get("result_origin") not in ("fresh", "cache", "replay", "unknown"):
            raise ValueError("Sample result_origin is required")


def evaluate_one(row, check):
    if row["execution_status"] == "not_run":
        return "not_run", "Sample was not executed"
    if row["execution_status"] == "failed":
        return "error", "Sample execution failed"
    if "output" not in row:
        return "error", "Completed sample has no available output"
    kind = check["kind"]
    if kind in {"human", "model"}:
        return "not_run", "External evaluator is not executed by this helper"
    actual = at_pointer(row["output"], check.get("path", ""))
    if actual is MISSING:
        return "fail", "Required output path is absent"
    if kind == "required_keys":
        passed = isinstance(actual, dict) and all(k in actual for k in check["keys"])
    elif kind == "nonempty":
        passed = isinstance(actual, (str, list, dict)) and bool(actual.strip() if isinstance(actual, str) else actual)
    elif kind == "equals":
        passed = equal_json(actual, check["expected"])
    elif kind == "one_of":
        passed = any(equal_json(actual, value) for value in check["values"])
    else:
        passed = isinstance(actual, list) and all(any(equal_json(item, allowed) for allowed in check["values"]) for item in actual)
    return ("pass", "Declared condition satisfied") if passed else ("fail", "Declared condition not satisfied")


def evaluate(config, samples):
    validate_config(config)
    validate_samples(samples)
    results = []
    for row in samples:
        for check in config["checks"]:
            state, reason = evaluate_one(row, check)
            results.append({k: row[k] for k in ("sample_id", "run_id", "attempt_id", "result_origin")} |
                           {"check_id": check["id"], "kind": check["kind"], "status": state, "reason": reason})
    counts = {state: 0 for state in ("pass", "fail", "not_run", "error")}
    counts.update(Counter(r["status"] for r in results))
    overall = "incomplete" if counts["not_run"] or counts["error"] else ("fail" if counts["fail"] else "pass")
    return {"evaluator": "project-learning/offline-contract-checks", "evaluator_version": VERSION,
            "result_scope": "configured_output_checks_only", "business_acceptance": "not_assessed",
            "checked_at": datetime.now(timezone.utc).isoformat(), "checks_version": config["version"],
            "rule_ref": config["rule_ref"], "overall": overall, "sample_attempts": len(samples),
            "unique_samples": len({r["sample_id"] for r in samples}),
            "origins": dict(Counter(r["result_origin"] for r in samples)), "check_counts": counts, "results": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checks", type=Path, required=True)
    parser.add_argument("--samples", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        checks_raw, samples_raw = args.checks.read_bytes(), args.samples.read_bytes()
        config = parse_json(checks_raw.decode("utf-8-sig"))
        samples = [parse_json(line) for line in samples_raw.decode("utf-8-sig").splitlines() if line.strip()]
        report = evaluate(config, samples)
        report["source_hashes"] = {"checks_sha256": hashlib.sha256(checks_raw).hexdigest(),
                                   "samples_sha256": hashlib.sha256(samples_raw).hexdigest()}
        rendered = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        with args.output.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(rendered)
        if args.output.read_text(encoding="utf-8") != rendered:
            raise OSError("Report readback mismatch")
        print(json.dumps({"report": str(args.output.resolve()), "overall": report["overall"],
                          "result_scope": report["result_scope"],
                          "check_counts": report["check_counts"]}, ensure_ascii=False))
        return {"pass": 0, "fail": 1, "incomplete": 2}[report["overall"]]
    except (OSError, ValueError, TypeError, OverflowError) as exc:
        print(f"Acceptance check error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
