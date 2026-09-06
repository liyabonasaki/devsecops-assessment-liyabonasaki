# Secret Detection Engine

A Python-based secret scanner that detects hardcoded credentials, API keys, tokens, and
passwords in source code and configuration files. Designed to integrate into CI/CD pipelines
as a quality gate.

## Features

- **14 secret pattern categories** - AWS keys, GitHub tokens, Stripe keys, Google API keys,
  JWT tokens, private keys, DB connection strings, passwords, and more
- **Smart false-positive filtering** - ignores `${ENV_VAR}` references, `process.env.*`,
  placeholder values (`changeme`, `xxxxx`, `<your-key>`), and commented-out lines
- **Confidence scoring** - each finding includes a 0-100% confidence score
- **Severity levels** - `CRITICAL / HIGH / MEDIUM / LOW` with an optional minimum filter
- **Actionable remediation** - every finding includes a specific fix recommendation
- **Dual output formats** - human-readable text and machine-parseable JSON
- **CI quality gate** - exits with code `1` when CRITICAL or HIGH secrets are found

## Requirements

- Python 3.8+
- No external dependencies - uses only the standard library

## Usage

```bash
# Scan a directory (text output)
python secret_detector.py --path ./app

# Scan a directory (JSON output)
python secret_detector.py --path ./app --format json

# Filter to HIGH and above only
python secret_detector.py --path ./app --severity HIGH

# Write JSON report to file
python secret_detector.py --path ./app --format json --output report.json

# Scan a single file
python secret_detector.py --path ../../application/country-service/src/main/resources/application.properties
```

## Example Output

```
======================================================================
  SECRET DETECTION SCAN REPORT
======================================================================
  Path      : /workspace/app
  Timestamp : 2026-09-04T10:00:00Z
  Files     : 12 scanned
  Findings  : 3 total
======================================================================
  CRITICAL : 1   HIGH : 2   MEDIUM : 0   LOW : 0
======================================================================

  [1] HIGH | HARDCODED_PASSWORD | Confidence: 85%
      File      : src/main/resources/application.properties:6
      Content   : spring.datasource.password=SuperSecret123!
      Detail    : Hardcoded password detected in configuration
      FP Risk   : LOW
      Fix       : Move to environment variable or secrets manager (e.g. AWS Secrets Manager, Vault).

======================================================================
  RESULT: FAILED - secrets detected
======================================================================
```

## Exit Codes

| Code | Meaning |
|------|---------|
| `0`  | No CRITICAL/HIGH secrets found - pipeline continues |
| `1`  | CRITICAL or HIGH secrets detected - pipeline should fail |
| `2`  | Invalid arguments or path not found |

## Running Tests

```bash
# Run all test cases
python -m pytest tests/ -v

# Or run directly
python tests/test_secret_detector.py
```

### Test Cases

| # | Scenario | Expected |
|---|----------|----------|
| 1 | `clean_config.properties` - env-var references only | 0 findings, PASSED |
| 2 | `dirty_config.properties` - hardcoded DB password + API key | >=2 findings, FAILED |
| 3 | `dirty_env.js` - AWS key, Stripe key, GitHub token, Google key | >=4 findings, FAILED |
| 4 | Severity filter `CRITICAL` on dirty file | Only CRITICAL findings returned |
| 5 | Summary structure on directory scan | All summary keys present and consistent |

## Detected Secret Types

| Pattern | Severity | Confidence |
|---------|----------|-----------|
| AWS Access Key ID (`AKIA...`) | CRITICAL | 95% |
| AWS Secret Access Key | CRITICAL | 95% |
| GitHub / GitLab PAT | CRITICAL | 90% |
| Stripe API Key | CRITICAL | 95% |
| Private Key (PEM) | CRITICAL | 99% |
| Hardcoded Password | HIGH | 85% |
| Generic API Key | HIGH | 80% |
| Bearer / OAuth Token | HIGH | 70% |
| DB Connection String | HIGH | 88% |
| Slack Webhook URL | HIGH | 95% |
| Google API Key | HIGH | 90% |
| JWT Token | HIGH | 85% |
| Secret Variable | MEDIUM | 75% |

## False Positive Handling

The scanner actively suppresses common noise sources:

- `${ENV_VAR}` and `$ENV_VAR` - environment variable references
- `process.env.*` - Node.js env lookups
- Values containing `changeme`, `placeholder`, `dummy`, `xxxxx`
- Explicit `<your-api-key>` style placeholders
- Values shorter than 8 characters

## Integration with CI/CD

This script is designed to be called from `.github/workflows/secure-pipeline.yml`:

```yaml
- name: Secret Detection Scan
  run: |
    python scripts/secret-detection/secret_detector.py \
      --path . \
      --format json \
      --severity HIGH \
      --output reports/secret-scan.json
```

The non-zero exit code on findings will automatically fail the GitHub Actions step.
