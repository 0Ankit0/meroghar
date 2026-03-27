#!/usr/bin/env python3
"""Fail CI when domain feature changes do not include requirement+test traceability updates."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

DOMAIN_PREFIX = {
    "iam": "IAM",
    "housing": "HOU",
    "finance": "FIN",
    "operations": "OPS",
    "crm": "CRM",
    "reporting": "RPT",
}
REQUIREMENT_RE = re.compile(r"\b(?:IAM|HOU|TEN|FIN|OPS|CRM|SCH|RPT)-\d{2}\b")


def sh(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True).strip()


def changed_files(base_ref: str) -> list[str]:
    output = sh(["git", "diff", "--name-only", f"{base_ref}...HEAD"])
    return [line for line in output.splitlines() if line]


def changed_added_lines(base_ref: str, path: str) -> str:
    try:
        return sh(["git", "diff", "--unified=0", f"{base_ref}...HEAD", "--", path])
    except subprocess.CalledProcessError:
        return ""


def parse_domains(paths: list[str]) -> dict[str, set[str]]:
    buckets: dict[str, set[str]] = defaultdict(set)
    for path in paths:
        parts = Path(path).parts
        if len(parts) < 3 or parts[0] != "apps":
            continue
        domain = parts[1]
        if domain not in DOMAIN_PREFIX:
            continue
        # Ignore tests and migrations when determining feature changes.
        if "tests" in parts or "migrations" in parts:
            continue
        buckets[domain].add(path)
    return buckets


def main() -> int:
    base_ref = os.environ.get("BASE_REF", "origin/main")
    files = changed_files(base_ref)
    if not files:
        print("No changed files; skipping requirement traceability checks.")
        return 0

    feature_domains = parse_domains(files)
    if not feature_domains:
        print("No domain feature file changes detected; skipping requirement traceability checks.")
        return 0

    doc_diff = changed_added_lines(base_ref, "docs/requirements.md")
    docs_changed = "docs/requirements.md" in files

    errors: list[str] = []

    for domain in sorted(feature_domains):
        prefix = DOMAIN_PREFIX[domain]
        expected_id_pattern = re.compile(rf"\b{prefix}-\d{{2}}\b")

        domain_test_changes = [
            p for p in files if p.startswith(f"apps/{domain}/tests/") and p.endswith(".py")
        ]
        if not domain_test_changes:
            errors.append(
                f"{domain}: feature files changed but no test updates under apps/{domain}/tests/."
            )

        domain_has_req_ids_in_tests = False
        for test_path in domain_test_changes:
            diff_text = changed_added_lines(base_ref, test_path)
            if expected_id_pattern.search(diff_text):
                domain_has_req_ids_in_tests = True
                break

        if not domain_has_req_ids_in_tests:
            errors.append(
                f"{domain}: updated tests are missing {prefix}-NN requirement IDs in added comments/names."
            )

        if not docs_changed:
            errors.append(
                f"{domain}: docs/requirements.md must be updated for domain feature changes."
            )
        elif not expected_id_pattern.search(doc_diff):
            errors.append(
                f"{domain}: docs/requirements.md update must include at least one added {prefix}-NN ID."
            )

    # Global check: any edited tests should use requirement IDs in added lines.
    updated_tests = [p for p in files if p.startswith("apps/") and "/tests/" in p and p.endswith(".py")]
    for test_file in updated_tests:
        test_diff = changed_added_lines(base_ref, test_file)
        if test_diff and not REQUIREMENT_RE.search(test_diff):
            errors.append(f"{test_file}: added test lines should include at least one requirement ID token.")

    if errors:
        print("Requirement traceability check failed:\n")
        for err in errors:
            print(f" - {err}")
        print("\nExpected: requirement ID updates in docs/requirements.md and matching test trace updates.")
        return 1

    print("Requirement traceability check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
