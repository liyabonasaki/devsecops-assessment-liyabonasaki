#!/usr/bin/env python3
"""
Secret Detection Engine
-----------------------
Scans source code and configuration files for hardcoded secrets such as
API keys, passwords, tokens, and connection strings. Produces actionable
reports with confidence scores and supports JSON and text output formats.

Usage:
    python secret_detector.py --path ./app
    python secret_detector.py --path ./app --format json
    python secret_detector.py --path ./app --format text --severity HIGH
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


# ---------------------------------------------------------------------------
# Secret pattern definitions
# Each entry: (name, regex, confidence, severity, description)
# ---------------------------------------------------------------------------
SECRET_PATTERNS = [
    # Passwords / credentials in config/properties files
    (
        "HARDCODED_PASSWORD",
        r"(?i)(password|passwd|pwd)\s*[=:]\s*['\"]?([^\s'\"$\{][^\s'\"]{3,})['\"]?",
        85,
        "HIGH",
        "Hardcoded password detected in configuration",
    ),
    # Generic API keys
    (
        "GENERIC_API_KEY",
        r"(?i)(api[_\-]?key|apikey)\s*[=:]\s*['\"]?([A-Za-z0-9\-_]{16,})['\"]?",
        80,
        "HIGH",
        "Potential API key found",
    ),
    # AWS access key ID (prefix + 16 alphanumeric chars, total 20)
    (
        "AWS_ACCESS_KEY",
        r"(?<![A-Z0-9])(AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}",
        95,
        "CRITICAL",
        "AWS Access Key ID detected",
    ),
    # AWS secret access key
    (
        "AWS_SECRET_KEY",
        r"(?i)aws[_\-]?secret[_\-]?access[_\-]?key\s*[=:]\s*['\"]?([A-Za-z0-9/+]{40})['\"]?",
        95,
        "CRITICAL",
        "AWS Secret Access Key detected",
    ),
    # GitHub / GitLab personal access tokens
    (
        "GITHUB_TOKEN",
        r"(?i)(gh[ps]_[A-Za-z0-9_]{36,}|glpat-[A-Za-z0-9\-_]{20,})",
        90,
        "CRITICAL",
        "GitHub/GitLab personal access token detected",
    ),
    # Generic Bearer / OAuth tokens
    (
        "BEARER_TOKEN",
        r"(?i)(bearer|token)\s*[=:]\s*['\"]?([A-Za-z0-9\-_.]{30,})['\"]?",
        70,
        "HIGH",
        "Potential Bearer/OAuth token found",
    ),
    # Private key headers
    (
        "PRIVATE_KEY",
        r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----",
        99,
        "CRITICAL",
        "Private key material detected",
    ),
    # Database connection strings with embedded credentials
    (
        "DB_CONNECTION_STRING",
        r"(?i)(jdbc|mongodb|postgresql|mysql|redis):\/\/[^:]+:[^@\s]{3,}@",
        88,
        "HIGH",
        "Database connection string with embedded credentials",
    ),
    # Generic secrets / tokens assigned to variables
    (
        "SECRET_VARIABLE",
        r"(?i)(secret|token|auth[_\-]?key)\s*[=:]\s*['\"]([A-Za-z0-9\-_!@#$%^&*]{8,})['\"]",
        75,
        "MEDIUM",
        "Variable assignment that may contain a secret",
    ),
    # Slack webhook URLs
    (
        "SLACK_WEBHOOK",
        r"https://hooks\.slack\.com/services/T[A-Z0-9]+/B[A-Z0-9]+/[A-Za-z0-9]+",
        95,
        "HIGH",
        "Slack Incoming Webhook URL detected",
    ),
    # Stripe keys
    (
        "STRIPE_KEY",
        r"(?:sk|pk)_(test|live)_[0-9a-zA-Z]{24,}",
        95,
        "CRITICAL",
        "Stripe API key detected",
    ),
    # Google API keys
    (
        "GOOGLE_API_KEY",
        r"AIza[0-9A-Za-z\-_]{35}",
        90,
        "HIGH",
        "Google API key detected",
    ),
    # JWT tokens (full 3-part)
    (
        "JWT_TOKEN",
        r"eyJ[A-Za-z0-9\-_]+\.eyJ[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+",
        85,
        "HIGH",
        "JWT token detected",
    ),
]

# ---------------------------------------------------------------------------
# False positive filter patterns - reduce noise for well-known placeholders
# ---------------------------------------------------------------------------
FALSE_POSITIVE_PATTERNS = [
    r"(?i)\$\{[^}]+\}",            # ${ENV_VAR} style substitution
    r"(?i)\$[A-Z_][A-Z0-9_]*",     # $ENV_VAR shell variable
    r"process\.env\.",             # Node.js process.env.* references
    r"os\.environ",                # Python os.environ references
    r"System\.getenv",             # Java System.getenv references
    r"(?i)<%=.*%>",                # template tags
    r"(?i)<your[_\- ]",            # <your-api-key> placeholders
    r"(?i)\*{4,}",                 # **** masked values
    r"(?i)xxx+",                   # xxx placeholders
    r"(?i)changeme",               # changeme placeholder
    r"(?i)placeholder",            # explicit placeholder word
    r"(?i)example\.com",           # example domains
    r"(?i)test(password|secret|key|token)",  # obvious test values
    r"(?i)dummy",                  # dummy values
    r"(?i)^#",                     # commented out lines (checked separately)
]

# File extensions to scan
SCANNABLE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rb", ".php",
    ".env", ".properties", ".yml", ".yaml", ".json", ".toml", ".ini",
    ".conf", ".config", ".xml", ".sh", ".bash", ".zsh", ".tf", ".tfvars",
    ".gradle", ".pom", ".dockerfile", "",  # empty = no extension (Dockerfile, Makefile)
}

# Directories to always skip
SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".tox", "venv", ".venv",
    "dist", "build", "target", ".idea", ".vscode", "coverage",
    "reports",  # scanner's own output dir - avoid self-scanning reports
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class Finding:
    file: str
    line_number: int
    line_content: str
    secret_type: str
    description: str
    severity: str
    confidence: int
    false_positive_risk: str  # LOW / MEDIUM / HIGH (likelihood this is a false positive)
    remediation: str


@dataclass
class ScanResult:
    scan_path: str
    scan_timestamp: str
    files_scanned: int
    findings: List[Finding] = field(default_factory=list)
    summary: dict = field(default_factory=dict)
    passed: bool = True


# ---------------------------------------------------------------------------
# Core scanner
# ---------------------------------------------------------------------------
class SecretDetector:
    def __init__(self, path: str, severity_filter: Optional[str] = None,
                 exclude: Optional[List[str]] = None):
        self.root = Path(path).resolve()
        self.severity_filter = severity_filter
        # Path substrings to exclude from scanning (e.g. the scanner's own
        # test fixtures which contain intentional "dirty" samples).
        self.exclude = exclude or []
        self.severity_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        self._compiled_patterns = [
            (name, re.compile(pattern), confidence, severity, desc)
            for name, pattern, confidence, severity, desc in SECRET_PATTERNS
        ]
        self._fp_compiled = [re.compile(p) for p in FALSE_POSITIVE_PATTERNS]

    def _is_excluded(self, file_path: Path) -> bool:
        """True if the file path matches any user-supplied exclude substring."""
        # Normalise to forward slashes so patterns work cross-platform
        normalised = str(file_path).replace("\\", "/")
        return any(pattern.replace("\\", "/") in normalised for pattern in self.exclude)

    def _should_skip_dir(self, dir_name: str) -> bool:
        return dir_name in SKIP_DIRS

    def _is_scannable(self, file_path: Path) -> bool:
        ext = file_path.suffix.lower()
        name = file_path.name.lower()
        # Always scan Dockerfile variants and Makefile
        if name in {"dockerfile", "makefile", ".env"}:
            return True
        return ext in SCANNABLE_EXTENSIONS

    def _is_false_positive(self, line: str, match_value: str) -> tuple:
        """Returns (is_fp: bool, fp_risk: str)"""
        combined = f"{line} {match_value}"
        # Check line is fully commented
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("*"):
            return False, "MEDIUM"  # commented secrets still a risk but lower confidence

        for pattern in self._fp_compiled:
            if pattern.search(combined):
                return True, "HIGH"

        # Short values are likely placeholders
        if len(match_value.strip("'\"")) < 8:
            return True, "HIGH"

        return False, "LOW"

    def _get_remediation(self, secret_type: str) -> str:
        remediations = {
            "HARDCODED_PASSWORD": "Move to environment variable or secrets manager (e.g. AWS Secrets Manager, Vault).",
            "GENERIC_API_KEY": "Store in environment variable; rotate the exposed key immediately.",
            "AWS_ACCESS_KEY": "Revoke key immediately via AWS IAM. Use IAM roles or environment variables.",
            "AWS_SECRET_KEY": "Revoke key immediately via AWS IAM. Never store in source code.",
            "GITHUB_TOKEN": "Revoke token in GitHub settings. Use GitHub Actions secrets for CI/CD.",
            "BEARER_TOKEN": "Store token in secrets manager; rotate if already exposed.",
            "PRIVATE_KEY": "Remove from repo history (git filter-branch / BFG). Store in secrets manager.",
            "DB_CONNECTION_STRING": "Use environment variables for DB credentials; consider connection pooling with secrets injection.",
            "SECRET_VARIABLE": "Use environment variable or secrets manager; remove from source code.",
            "SLACK_WEBHOOK": "Regenerate webhook in Slack. Store URL in environment variable.",
            "STRIPE_KEY": "Revoke key in Stripe dashboard. Use environment variables.",
            "GOOGLE_API_KEY": "Restrict key in Google Console and move to environment variable.",
            "JWT_TOKEN": "Do not hardcode tokens. Generate at runtime and store securely.",
        }
        return remediations.get(secret_type, "Remove secret from source code and store in a secrets manager.")

    def _redact(self, line: str) -> str:
        """Redact most of a secret value for safe display."""
        return line[:120] + ("..." if len(line) > 120 else "")

    def scan_file(self, file_path: Path) -> List[Finding]:
        findings = []
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except (OSError, PermissionError):
            return findings

        lines = content.splitlines()
        for line_num, line in enumerate(lines, start=1):
            for name, pattern, confidence, severity, desc in self._compiled_patterns:
                match = pattern.search(line)
                if not match:
                    continue

                match_value = match.group(0)
                is_fp, fp_risk = self._is_false_positive(line, match_value)
                if is_fp:
                    continue

                # Apply severity filter
                if self.severity_filter:
                    if self.severity_order.get(severity, 0) < self.severity_order.get(self.severity_filter, 0):
                        continue

                finding = Finding(
                    file=str(file_path.relative_to(self.root)),
                    line_number=line_num,
                    line_content=self._redact(line.strip()),
                    secret_type=name,
                    description=desc,
                    severity=severity,
                    confidence=confidence,
                    false_positive_risk=fp_risk,
                    remediation=self._get_remediation(name),
                )
                findings.append(finding)

        return findings

    def scan(self) -> ScanResult:
        result = ScanResult(
            scan_path=str(self.root),
            scan_timestamp=datetime.now(timezone.utc).isoformat(),
            files_scanned=0,
        )

        if self.root.is_file():
            result.files_scanned = 1
            result.findings = self.scan_file(self.root)
        else:
            for dirpath, dirnames, filenames in os.walk(self.root):
                # Prune skip directories in-place
                dirnames[:] = [d for d in dirnames if not self._should_skip_dir(d)]
                for fname in filenames:
                    fpath = Path(dirpath) / fname
                    if self._is_excluded(fpath):
                        continue
                    if self._is_scannable(fpath):
                        result.files_scanned += 1
                        result.findings.extend(self.scan_file(fpath))

        # Build summary
        by_severity = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        by_type: dict = {}
        for f in result.findings:
            by_severity[f.severity] = by_severity.get(f.severity, 0) + 1
            by_type[f.secret_type] = by_type.get(f.secret_type, 0) + 1

        result.summary = {
            "total_findings": len(result.findings),
            "by_severity": by_severity,
            "by_type": by_type,
            "files_scanned": result.files_scanned,
        }

        # Fail if any CRITICAL or HIGH finding
        result.passed = by_severity["CRITICAL"] == 0 and by_severity["HIGH"] == 0

        return result


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------
def format_json(result: ScanResult) -> str:
    data = asdict(result)
    return json.dumps(data, indent=2)


def format_text(result: ScanResult) -> str:
    lines = []
    sep = "=" * 70
    lines.append(sep)
    lines.append("  SECRET DETECTION SCAN REPORT")
    lines.append(sep)
    lines.append(f"  Path      : {result.scan_path}")
    lines.append(f"  Timestamp : {result.scan_timestamp}")
    lines.append(f"  Files     : {result.files_scanned} scanned")
    lines.append(f"  Findings  : {result.summary['total_findings']} total")
    lines.append(sep)

    sev = result.summary["by_severity"]
    lines.append(f"  CRITICAL : {sev['CRITICAL']}   HIGH : {sev['HIGH']}   "
                 f"MEDIUM : {sev['MEDIUM']}   LOW : {sev['LOW']}")
    lines.append(sep)

    if not result.findings:
        lines.append("\n  No secrets detected. Scan PASSED.\n")
    else:
        for i, f in enumerate(result.findings, 1):
            lines.append(f"\n  [{i}] {f.severity} | {f.secret_type} | Confidence: {f.confidence}%")
            lines.append(f"      File      : {f.file}:{f.line_number}")
            lines.append(f"      Content   : {f.line_content}")
            lines.append(f"      Detail    : {f.description}")
            lines.append(f"      FP Risk   : {f.false_positive_risk}")
            lines.append(f"      Fix       : {f.remediation}")

    lines.append("\n" + sep)
    status = "PASSED" if result.passed else "FAILED - secrets detected"
    lines.append(f"  RESULT: {status}")
    lines.append(sep + "\n")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Secret Detection Engine - scans source code for hardcoded secrets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python secret_detector.py --path ./app
  python secret_detector.py --path ./app --format json
  python secret_detector.py --path ./app --severity HIGH
  python secret_detector.py --path ./app --format json --output report.json
        """,
    )
    parser.add_argument("--path", required=True, help="Path to scan (file or directory)")
    parser.add_argument(
        "--format", choices=["text", "json"], default="text", help="Output format (default: text)"
    )
    parser.add_argument(
        "--severity",
        choices=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
        default=None,
        help="Minimum severity level to report",
    )
    parser.add_argument("--output", default=None, help="Write report to file instead of stdout")
    parser.add_argument(
        "--exclude",
        action="append",
        default=None,
        metavar="SUBSTRING",
        help="Exclude paths containing this substring (repeatable). "
             "Example: --exclude tests/samples --exclude node_modules",
    )

    args = parser.parse_args()

    if not Path(args.path).exists():
        print(f"Error: path '{args.path}' does not exist.", file=sys.stderr)
        sys.exit(2)

    detector = SecretDetector(
        path=args.path,
        severity_filter=args.severity,
        exclude=args.exclude,
    )
    result = detector.scan()

    report = format_json(result) if args.format == "json" else format_text(result)

    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        # Guard against Windows consoles (cp1252) that can't encode emoji.
        try:
            print(report)
        except UnicodeEncodeError:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            print(report)

    # Exit code 1 = secrets found (for CI quality gate integration)
    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
