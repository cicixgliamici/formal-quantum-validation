"""Publish pytest JUnit counts without turning missing reports into success."""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from pathlib import Path


def render_summary(report_directory: Path, job_status: str) -> str:
    """Keep job status separate from test counts: other CI steps can fail too."""

    lines = [
        "## Test results",
        "",
        f"Job status before reporting: **{job_status}**.",
        "",
        "| Suite | Tests | Failures | Errors | Skipped |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    reports = sorted(report_directory.glob("*.xml"))
    for report in reports:
        root = ET.parse(report).getroot()
        # Pytest wraps suites in a testsuites root; support a single suite too.
        suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
        counts = [
            sum(int(suite.get(attribute, "0")) for suite in suites)
            for attribute in ("tests", "failures", "errors", "skipped")
        ]
        lines.append(f"| {report.stem} | " + " | ".join(map(str, counts)) + " |")
    if not reports:
        lines.extend(["", "No JUnit report was produced; inspect setup and build logs."])
    lines.extend(["", "Counts describe executed tests, not universal correctness."])
    return "\n".join(lines) + "\n"


def main() -> None:
    """Append to GitHub's summary, or print locally for review."""

    summary = render_summary(Path("build/test-results"), os.environ.get("JOB_STATUS", "local"))
    destination = os.environ.get("GITHUB_STEP_SUMMARY")
    if destination:
        with Path(destination).open("a", encoding="utf-8") as stream:
            stream.write(summary)
    else:
        print(summary, end="")


if __name__ == "__main__":
    main()
