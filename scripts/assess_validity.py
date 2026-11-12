"""Assess time boundaries and declared lifecycle state; does not decide business reuse."""
import argparse
from datetime import date, datetime, time
import hashlib
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
from evaluate_checks import parse_json, text_id

VERSION = "0.4.0"
STATES = {"current_in_scope", "review_required", "expired", "superseded", "unknown"}


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError("Timestamp must be a string")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("Timestamp requires a UTC offset")
    return parsed


def assess(record, as_of):
    if not isinstance(record, dict) or not all(text_id(record.get(k)) for k in ("id", "revision")):
        raise ValueError("Record needs id and revision")
    validity = record.get("validity")
    if validity is None:
        validity = {}
    if not isinstance(validity, dict):
        raise ValueError("validity must be an object or null")
    declared = validity.get("state", "unknown")
    if not isinstance(declared, str) or declared not in STATES:
        raise ValueError("Invalid declared validity state")
    bounds = {}
    date_only = []
    for key in ("effective_from", "effective_until", "review_due_at"):
        value = validity.get(key)
        if value is None:
            bounds[key] = None
        elif isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            bounds[key] = datetime.combine(date.fromisoformat(value), time.min, tzinfo=as_of.tzinfo)
            date_only.append(key)
        else:
            bounds[key] = timestamp(value)
    start, end, review = (bounds[k] for k in ("effective_from", "effective_until", "review_due_at"))
    if start is not None and end is not None and start >= end:
        raise ValueError("effective_from must precede effective_until")
    state, reasons = declared, []
    if validity.get("superseded_by") or declared == "superseded":
        state, reasons = "superseded", ["Declared replacement or superseded state"]
    elif declared == "expired" or (end is not None and as_of >= end):
        state, reasons = "expired", ["Declared expired or effective_until reached"]
    elif start is not None and as_of < start:
        state, reasons = "review_required", ["Not yet effective at as_of"]
    elif declared == "review_required" or (review is not None and as_of >= review):
        state, reasons = "review_required", ["Declared review requirement or review_due_at reached"]
    elif declared == "unknown":
        reasons = ["No verified current-in-scope declaration; dates alone do not establish validity"]
    else:
        reasons = ["No time blocker found for the existing current-in-scope declaration"]
    return {"evaluator": "project-learning/temporal-assessment", "evaluator_version": VERSION,
            "record_id": record["id"], "revision": record["revision"], "as_of": as_of.isoformat(),
            "declared_state": declared, "effective_state": state, "reasons": reasons,
            "unknown_boundaries": [k for k in ("effective_from", "effective_until") if bounds[k] is None],
            "date_only_fields": date_only, "date_only_timezone": str(as_of.tzinfo),
            "business_compatibility": "not_assessed", "can_reuse": None,
            "limitations": "Time assessment only. Unknown bounds do not mean perpetual validity. Original record is not modified."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", type=Path, required=True)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        raw = args.record.read_bytes()
        report = assess(parse_json(raw.decode("utf-8-sig")), timestamp(args.as_of))
        report["record_sha256"] = hashlib.sha256(raw).hexdigest()
        rendered = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        with args.output.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(rendered)
        if args.output.read_text(encoding="utf-8") != rendered:
            raise OSError("Report readback mismatch")
        print(json.dumps({"report": str(args.output.resolve()), "effective_state": report["effective_state"],
                          "business_compatibility": report["business_compatibility"]}, ensure_ascii=False))
        return 0 if report["effective_state"] == "current_in_scope" else 1
    except (OSError, ValueError, TypeError, OverflowError) as exc:
        print(f"Validity assessment error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
