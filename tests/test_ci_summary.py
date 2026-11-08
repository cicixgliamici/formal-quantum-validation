"""Keep failed, skipped, and missing test evidence visible in CI summaries."""

from pathlib import Path

from scripts.summarize_tests import render_summary


def test_reports_failures_errors_and_skips(tmp_path: Path) -> None:
    report = tmp_path / "python.xml"
    report.write_text(
        '<testsuites><testsuite tests="5" failures="1" errors="1" skipped="2"/>'
        '<testsuite tests="2" failures="0" errors="0" skipped="0"/></testsuites>',
        encoding="utf-8",
    )
    summary = render_summary(tmp_path, "failure")
    assert "**failure**" in summary
    assert "| python | 7 | 1 | 1 | 2 |" in summary


def test_missing_report_is_not_reported_as_passed(tmp_path: Path) -> None:
    summary = render_summary(tmp_path, "failure")
    assert "No JUnit report was produced" in summary
    assert "**failure**" in summary
