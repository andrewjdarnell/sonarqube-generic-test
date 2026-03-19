#!/usr/bin/env python3
"""Convert JUnit XML reports to SonarQube generic test execution format."""

from __future__ import annotations

import argparse
from pathlib import Path
import xml.etree.ElementTree as ET


# Convert a JUnit time value in seconds into Sonar test duration milliseconds.
# from: "0.021" -> to: "21"
def _duration_to_ms(duration_seconds: str | None) -> str:
    try:
        seconds = float(duration_seconds) if duration_seconds is not None else 0.0
    except (TypeError, ValueError):
        seconds = 0.0

    if seconds < 0:
        seconds = 0.0

    return str(int(round(seconds * 1000)))


# Normalize JUnit root shapes into a list of testsuite nodes.
# from: <testsuite>...</testsuite> -> to: [testsuite]
# from: <testsuites><testsuite/></testsuites> -> to: [testsuite]
def _iter_test_suites(root: ET.Element) -> list[ET.Element]:
    if root.tag == "testsuite":
        return [root]
    if root.tag == "testsuites":
        suites = root.findall("testsuite")
        return suites if suites else []
    return []


# Pick the best Sonar file path for a testcase using metadata fallbacks.
# from: classname="tests/a.tftest.hcl" -> to: "tests/a.tftest.hcl"
# from: missing classname + suite name -> to: suite name
def _select_file_path(testcase: ET.Element, testsuite: ET.Element, fallback_path: str) -> str:
    candidate_paths = [
        testcase.get("classname"),
        testsuite.get("name"),
        fallback_path,
    ]

    for candidate in candidate_paths:
        if candidate and candidate.strip():
            return candidate.strip()

    return "unknown-test-file"


# Copy the first non-pass status node from JUnit onto a Sonar testCase.
# from: <failure message="m">details</failure> -> to: <failure message="m">details</failure>
def _append_status_if_any(source_testcase: ET.Element, target_testcase: ET.Element) -> None:
    for tag_name in ("failure", "error", "skipped"):
        status = source_testcase.find(tag_name)
        if status is None:
            continue

        status_el = ET.SubElement(target_testcase, tag_name)
        message = status.get("message", "").strip()
        details = (status.text or "").strip()

        # Sonar generic execution format requires a short status message.
        if not message:
            if details:
                message = details.splitlines()[0].strip() or f"{tag_name} reported"
            else:
                message = f"{tag_name} reported"

        status_el.set("message", message)

        if details:
            status_el.text = details
        return


    # Convert a parsed JUnit XML root into a Sonar generic testExecutions XML root.
    # from: <testsuite><testcase name="x" time="0.1"/></testsuite>
    # to: <testExecutions><file ...><testCase name="x" duration="100"/></file></testExecutions>
def junit_root_to_sonar_test_executions(
    junit_root: ET.Element,
    fallback_test_file_path: str = "",
) -> ET.Element:
    output_root = ET.Element("testExecutions", version="1")
    output_file_nodes: dict[str, ET.Element] = {}

    for testsuite in _iter_test_suites(junit_root):
        for testcase in testsuite.findall("testcase"):
            file_path = _select_file_path(testcase, testsuite, fallback_test_file_path)

            if file_path not in output_file_nodes:
                output_file_nodes[file_path] = ET.SubElement(output_root, "file", path=file_path)

            output_test_case = ET.SubElement(
                output_file_nodes[file_path],
                "testCase",
                name=testcase.get("name", "unnamed-test"),
                duration=_duration_to_ms(testcase.get("time")),
            )
            _append_status_if_any(testcase, output_test_case)

    return output_root


# Convert one on-disk JUnit XML file into one Sonar generic execution XML file.
# from: input junit.xml -> to: output sonar-test-executions.xml
def convert_junit_file_to_sonar_generic(input_path: str | Path, output_path: str | Path) -> None:
    input_path = Path(input_path)
    output_path = Path(output_path)

    tree = ET.parse(input_path)
    junit_root = tree.getroot()

    sonar_root = junit_root_to_sonar_test_executions(
        junit_root,
        fallback_test_file_path=input_path.name,
    )

    output_tree = ET.ElementTree(sonar_root)
    ET.indent(output_tree, space="  ", level=0)
    output_tree.write(output_path, encoding="utf-8", xml_declaration=True)


# Build the CLI parser for input and output file arguments.
# from: argv ["in.xml", "out.xml"] -> to: parsed args.input/args.output
def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert JUnit XML to SonarQube generic test execution XML."
    )
    parser.add_argument("input", help="Path to the input JUnit XML file.")
    parser.add_argument("output", help="Path to write Sonar generic test execution XML.")
    return parser


# CLI entrypoint that parses args and runs file conversion.
# from: python junit_to_sonar.py in.xml out.xml -> to: writes converted XML and exits 0
def main() -> int:
    args = _build_parser().parse_args()
    convert_junit_file_to_sonar_generic(args.input, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
