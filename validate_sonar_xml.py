#!/usr/bin/env python3
"""Validate Sonar generic test execution XML files against an XSD schema.

Defaults:
- Schema: sonar_generic_test_execution.xsd
- Files: generated/*.sonar.xml
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Sonar XML files against sonar_generic_test_execution.xsd"
    )
    parser.add_argument(
        "patterns",
        nargs="*",
        default=["generated/*.sonar.xml"],
        help="Glob pattern(s) for XML files to validate (default: generated/*.sonar.xml)",
    )
    parser.add_argument(
        "--schema",
        default="sonar_generic_test_execution.xsd",
        help="Path to XSD schema file (default: sonar_generic_test_execution.xsd)",
    )
    return parser.parse_args()


def resolve_files(patterns: list[str]) -> list[str]:
    found: list[str] = []
    for pattern in patterns:
        found.extend(glob.glob(pattern))
    return sorted(set(found))


def extract_line_col(err_line: str) -> tuple[str | None, str | None]:
    match = re.search(r":(\d+):(\d+):", err_line)
    if match:
        return match.group(1), match.group(2)
    return None, None


def summarize_xmllint_errors(stderr: str) -> list[str]:
    messages: list[str] = []
    for raw in stderr.splitlines():
        line = raw.strip()
        if not line:
            continue
        if "validates" in line:
            continue
        if "Schemas validity error" in line:
            line_no, col_no = extract_line_col(line)
            detail = line.split("Schemas validity error", 1)[-1].strip(" :")
            if line_no and col_no:
                messages.append(f"line {line_no}, col {col_no}: {detail}")
            else:
                messages.append(detail)
            continue
        if line.endswith("fails to validate"):
            continue
        # Keep remaining parser/schema lines for context.
        messages.append(line)
    return messages


def validate_file(schema: str, xml_file: str) -> tuple[bool, list[str]]:
    cmd = ["xmllint", "--noout", "--schema", schema, xml_file]
    proc = subprocess.run(cmd, capture_output=True, text=True)

    if proc.returncode == 0:
        return True, []

    combined = "\n".join(part for part in [proc.stdout, proc.stderr] if part)
    details = summarize_xmllint_errors(combined)
    if not details:
        details = [combined.strip() or "Unknown validation error"]
    return False, details


def main() -> int:
    args = parse_args()

    if shutil.which("xmllint") is None:
        print(
            "Error: xmllint is required but was not found in PATH. "
            "Install libxml2 or use a system with xmllint available.",
            file=sys.stderr,
        )
        return 2

    schema_path = Path(args.schema)
    if not schema_path.exists():
        print(f"Error: schema not found: {schema_path}", file=sys.stderr)
        return 2

    files = resolve_files(args.patterns)
    if not files:
        print(
            "No XML files matched the supplied pattern(s): "
            + ", ".join(args.patterns),
            file=sys.stderr,
        )
        return 2

    print(f"Schema: {schema_path}")
    print(f"Files: {len(files)}")

    failures = 0
    for xml_file in files:
        ok, details = validate_file(str(schema_path), xml_file)
        rel = os.path.relpath(xml_file)
        if ok:
            print(f"PASS  {rel}")
            continue

        failures += 1
        print(f"FAIL  {rel}")
        for msg in details:
            print(f"  - {msg}")

    if failures:
        print(f"\nValidation failed: {failures} file(s) did not match the schema.")
        return 1

    print("\nValidation succeeded: all files match the schema.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
