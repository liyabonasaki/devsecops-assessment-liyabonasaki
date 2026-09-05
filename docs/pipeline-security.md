# Block 2: Pipeline Security

## Overview

The secure CI/CD pipeline is implemented in `.github/workflows/secure-pipeline.yml`.
It integrates **5 security scanners** across **4 parallel job tracks**, with explicit
quality gates that control whether a build passes or is blocked.

## Pipeline Architecture

```
Push / PR
    │
    ▼
┌─────────────────────────┐
│  Job 1: Secret Detection │  ← Runs first, blocks all downstream on failure
│  • Custom Python scanner │
└────────────┬────────────┘
             │ (needs: secret-detection)
    ┌────────┴────────┐
    ▼                 ▼
┌──────────────┐  ┌───────────────┐
│ Job 2:       │  │ Job 3:        │
│ Frontend     │  │ Backend       │  ← Parallel
│ Security     │  │ Security      │
│ • npm audit  │  │ • OWASP DC    │
│ • Semgrep JS │  │ • Semgrep Java│
│ • License    │  └───────┬───────┘
└──────┬───────┘          │
       └────────┬──────────┘
                ▼
    ┌───────────────────────┐
    │ Job 4: Container Scan  │
    │ • Trivy IaC config     │
    │ • Trivy image (backend)│
    │ • Trivy image (front)  │
    └───────────┬───────────┘
                ▼
    ┌───────────────────────┐
    │ Job 5: Summary        │
    │ Consolidated results  │  ← Always runs (if: always())
    └───────────────────────┘
```

## Security Controls

### Scanner 1: Secret Detection (Job 1)
- **Tool**: Custom Python engine (`scripts/secret-detection/secret_detector.py`)
- **What it catches**: Hardcoded passwords, API keys, AWS credentials, GitHub tokens, JWTs
- **Quality gate**: `EXIT 1` on any HIGH or CRITICAL finding → blocks entire pipeline
- **Why first**: Fastest check; no point running expensive scans if secrets are already exposed

### Scanner 2: npm Dependency Audit (Job 2)
- **Tool**: `npm audit --audit-level=high`
- **What it catches**: Known CVEs in frontend JavaScript dependencies
- **Quality gate**: Fails on HIGH or CRITICAL vulnerability count > 0
- **Output**: `reports/npm-audit.json`

### Scanner 3: Semgrep SAST (Jobs 2 & 3)
- **Tool**: Semgrep with `p/javascript`, `p/react`, `p/java`, `p/spring`, `p/secrets` rulesets
- **What it catches**:
  - Frontend: XSS, insecure eval, prototype pollution, hardcoded secrets in JS
  - Backend: SQL injection, XXE, insecure deserialization, Spring Security misconfigurations
- **Quality gate**: Warnings posted to PR via SARIF upload to GitHub Code Scanning
- **Output**: `semgrep.sarif`, `reports/semgrep-java.json`

### Scanner 4: OWASP Dependency-Check (Job 3)
- **Tool**: `org.owasp:dependency-check-maven`
- **What it catches**: Known CVEs in Java/Maven dependencies cross-referenced against NVD
- **Quality gate**: `failBuildOnCVSS=7` — fails on CVSS ≥ 7 (HIGH/CRITICAL)
- **Output**: `reports/dependency-check-report.json`

### Scanner 5: Trivy (Job 4)
- **Tool**: `aquasecurity/trivy-action`
- **Modes**:
  - **Config scan** (`trivy config .`) — checks Dockerfiles and docker-compose for misconfigurations
  - **Image scan** — scans built container images for OS and library CVEs
- **Quality gate**: Fails on any CRITICAL container vulnerability
- **Output**: `reports/trivy-iac.json`, `reports/trivy-backend.json`, `reports/trivy-frontend.json`

### Scanner 6: License Compliance (Job 2)
- **Tool**: `license-checker`
- **What it catches**: GPL, AGPL, LGPL, CC-BY-NC licenses in frontend dependencies
- **Quality gate**: Warning only — does not block (legal review is a manual process)

## Quality Gate Logic

```
Finding Severity │ Action
─────────────────┼──────────────────────────────────────────
CRITICAL         │ FAIL immediately — merge blocked
HIGH             │ FAIL the relevant job — merge blocked
MEDIUM           │ WARN — annotated in PR, does not block
LOW              │ INFO — logged to artifacts only
```

The final `pipeline-summary` job enforces a combined gate: if **any** upstream security
job fails, the summary job exits 1 and the overall workflow is marked failed.

## Reports and Artifacts

All scan outputs are uploaded as GitHub Actions artifacts and retained for **30 days**:

| Artifact Name | Contents |
|---|---|
| `secret-scan-report` | `secret-scan.json` |
| `frontend-security-reports` | `npm-audit.json` |
| `backend-security-reports` | `dependency-check-report.json`, `semgrep-java.json` |
| `container-security-reports` | `trivy-iac.json`, `trivy-backend.json`, `trivy-frontend.json` |

## Secrets Required

Add the following to your GitHub repository secrets (`Settings → Secrets → Actions`):

| Secret | Required | Purpose |
|--------|----------|---------|
| `SEMGREP_APP_TOKEN` | Optional | Publish results to Semgrep Cloud dashboard |
| `SEMGREP_DEPLOYMENT_ID` | Optional | Required if using Semgrep Cloud |
| `NVD_API_KEY` | Recommended | Faster NVD database updates for OWASP DC |

## Pipeline Triggers

| Event | Trigger |
|-------|---------|
| Push to `candidate-assessment` | Always runs |
| Push to `main` | Always runs |
| Pull request to `main` | Always runs |
| Manual | `workflow_dispatch` |

## Concurrency

Concurrent runs on the same branch are cancelled to avoid redundant scans and save
GitHub Actions minutes.
