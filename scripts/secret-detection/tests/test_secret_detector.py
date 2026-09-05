#!/usr/bin/env python3
"""
Unit tests for the Secret Detection Engine.
Run with: python -m pytest tests/ -v
Or directly: python tests/test_secret_detector.py
"""

import sys
import os
import unittest
from pathlib import Path

# Add parent directory to path so we can import secret_detector
sys.path.insert(0, str(Path(__file__).parent.parent))
from secret_detector import SecretDetector, ScanResult


SAMPLES_DIR = Path(__file__).parent / "samples"


class TestCleanFile(unittest.TestCase):
    """Test Case 1: A clean config file with env-var references should produce zero findings."""

    def test_clean_config_no_findings(self):
        detector = SecretDetector(path=str(SAMPLES_DIR / "clean_config.properties"))
        result = detector.scan()
        self.assertEqual(result.summary["total_findings"], 0,
                         f"Expected 0 findings in clean file, got {result.summary['total_findings']}: "
                         f"{[f.secret_type for f in result.findings]}")

    def test_clean_config_passes(self):
        detector = SecretDetector(path=str(SAMPLES_DIR / "clean_config.properties"))
        result = detector.scan()
        self.assertTrue(result.passed, "Clean config should pass the quality gate")


class TestDirtyPropertiesFile(unittest.TestCase):
    """Test Case 2: A properties file with hardcoded credentials should be detected."""

    def setUp(self):
        self.detector = SecretDetector(path=str(SAMPLES_DIR / "dirty_config.properties"))
        self.result = self.detector.scan()

    def test_finds_password(self):
        types = [f.secret_type for f in self.result.findings]
        self.assertIn("HARDCODED_PASSWORD", types,
                      "Should detect hardcoded spring.datasource.password")

    def test_finds_api_key(self):
        types = [f.secret_type for f in self.result.findings]
        self.assertIn("GENERIC_API_KEY", types,
                      "Should detect hardcoded external.api.key")

    def test_fails_quality_gate(self):
        self.assertFalse(self.result.passed,
                         "Dirty config should fail the quality gate")

    def test_env_var_reference_not_flagged(self):
        # ${SOME_OTHER_VALUE} must not appear in findings
        flagged_lines = [f.line_content for f in self.result.findings]
        for line in flagged_lines:
            self.assertNotIn("${SOME_OTHER_VALUE}", line,
                             "Environment variable references must not be flagged as secrets")


class TestDirtyJavaScriptFile(unittest.TestCase):
    """Test Case 3: A JS file with AWS keys, Stripe keys, and GitHub tokens should all be detected."""

    def setUp(self):
        self.detector = SecretDetector(path=str(SAMPLES_DIR / "dirty_env.js"))
        self.result = self.detector.scan()

    def test_finds_aws_key(self):
        types = [f.secret_type for f in self.result.findings]
        self.assertIn("AWS_ACCESS_KEY", types, "Should detect AWS Access Key ID")

    def test_finds_stripe_key(self):
        types = [f.secret_type for f in self.result.findings]
        self.assertIn("STRIPE_KEY", types, "Should detect Stripe live key")

    def test_finds_google_api_key(self):
        types = [f.secret_type for f in self.result.findings]
        self.assertIn("GOOGLE_API_KEY", types, "Should detect Google API key")

    def test_finds_github_token(self):
        types = [f.secret_type for f in self.result.findings]
        self.assertIn("GITHUB_TOKEN", types, "Should detect GitHub personal access token")

    def test_env_var_not_flagged(self):
        # process.env.DB_PASSWORD must not be flagged
        flagged_lines = [f.line_content for f in self.result.findings]
        for line in flagged_lines:
            self.assertNotIn("process.env.DB_PASSWORD", line,
                             "process.env references must not be flagged")

    def test_confidence_scores_present(self):
        for finding in self.result.findings:
            self.assertGreater(finding.confidence, 0, "All findings must have a confidence score > 0")
            self.assertLessEqual(finding.confidence, 100, "Confidence must be <= 100")

    def test_remediation_present(self):
        for finding in self.result.findings:
            self.assertTrue(len(finding.remediation) > 10,
                            "Each finding must include a remediation recommendation")


class TestSeverityFilter(unittest.TestCase):
    """Test Case 4: Severity filter should exclude findings below the threshold."""

    def test_critical_filter_excludes_medium(self):
        detector = SecretDetector(
            path=str(SAMPLES_DIR / "dirty_config.properties"),
            severity_filter="CRITICAL",
        )
        result = detector.scan()
        for finding in result.findings:
            self.assertIn(finding.severity, ["CRITICAL"],
                          f"With CRITICAL filter, found {finding.severity} finding: {finding.secret_type}")

    def test_high_filter_excludes_medium(self):
        detector = SecretDetector(
            path=str(SAMPLES_DIR / "dirty_config.properties"),
            severity_filter="HIGH",
        )
        result = detector.scan()
        for finding in result.findings:
            self.assertIn(finding.severity, ["CRITICAL", "HIGH"],
                          f"With HIGH filter, found {finding.severity} finding")


class TestScanSummary(unittest.TestCase):
    """Test Case 5: Summary structure is always present and consistent."""

    def test_summary_keys_present(self):
        detector = SecretDetector(path=str(SAMPLES_DIR))
        result = detector.scan()
        self.assertIn("total_findings", result.summary)
        self.assertIn("by_severity", result.summary)
        self.assertIn("by_type", result.summary)
        self.assertIn("files_scanned", result.summary)

    def test_summary_totals_match_findings(self):
        detector = SecretDetector(path=str(SAMPLES_DIR))
        result = detector.scan()
        total_from_severity = sum(result.summary["by_severity"].values())
        # total_findings must match sum across severity levels
        self.assertEqual(result.summary["total_findings"], len(result.findings))


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  Running Secret Detection Engine Tests")
    print("=" * 60 + "\n")
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    test_result = runner.run(suite)
    sys.exit(0 if test_result.wasSuccessful() else 1)
