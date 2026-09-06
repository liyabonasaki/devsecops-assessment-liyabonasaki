# Block 4: DevSecOps Architecture Design

**Candidate:** Liyabona Saki  
**Assessment:** DevSecOps Technical Assessment  
**Date:** September 2026

---

## 1. Current State Analysis

### 1.1 What We Have

The provided application is a two-tier web stack:

```
┌-------------------------┐        ┌------------------------------┐
|  country-flags-app       |        |  country-service              |
|  React 18 SPA            |-------▶|  Spring Boot 3 / Java 17     |
|  Port 3000               |  HTTP  |  Port 8081                   |
|  npm / react-scripts     |        |  H2 in-memory DB             |
└-------------------------┘        |  External: restcountries.com  |
                                    └------------------------------┘
```

### 1.2 Current Security Gaps

A structured review of the provided source code reveals the following issues, ordered by risk:

| # | Gap | Location | Risk | Status |
|---|-----|----------|------|--------|
| 1 | Hardcoded DB password (`password`) | `application.properties` | HIGH | Fixed - now `${DB_PASSWORD}` env-var injection |
| 2 | H2 console enabled by default | `application.properties` | MEDIUM | Fixed - now `${H2_CONSOLE_ENABLED:false}` |
| 3 | CORS allows all headers (`allowedHeaders("*")`) | `CorsConfig.java` | MEDIUM | Planned - Phase 1 backlog |
| 4 | Spring Security version mismatch (2.7.0 pinned in Boot 3 project) | `pom.xml` | HIGH | Fixed - removed pin; bumped Boot to 3.5.11 and pinned Spring Security 6.5.11 |
| 5 | No HTTPS - all traffic in cleartext | Both apps | CRITICAL | Planned - Phase 2 (Nginx TLS) |
| 6 | H2 in-memory DB - data lost on restart, no persistence | `application.properties` | MEDIUM | Planned - Phase 2 (PostgreSQL) |
| 7 | No authentication on API endpoints | `CountryController.java` | MEDIUM | Planned - Phase 2 (JWT) |
| 8 | External API call on startup, no timeout/retry config | `DataLoader.java` | LOW | Planned - Phase 3 |
| 9 | `axios@0.27.2` - outdated with CRITICAL CVEs (SSRF, credential leak via follow-redirects) | `package.json` | HIGH | Fixed - upgraded to `axios@^1.7.9` (API-compatible, no code change) |
| 10 | No rate limiting or request size limits | Both apps | MEDIUM | Planned - Phase 2 |
| 11 | No structured logging or audit trail | Both apps | MEDIUM | Planned - Phase 2 |
| 12 | No container images - no hardening | Neither app | HIGH | Fixed - hardened multi-stage Dockerfiles (Block 3) |
| 13 | **Build defect**: source uses Java records but `pom.xml` targets Java 11 (records need 16+) | `pom.xml` + DTOs | HIGH | Fixed - bumped to Java 17 LTS |
| 14 | **Test defect**: security starter causes `@WebMvcTest` controller tests to fail with 401 | `CountryControllerTest.java` | MEDIUM | Fixed - `@AutoConfigureMockMvc(addFilters=false)` |
| 15 | **Container CVEs**: 8 CRITICAL in bundled Tomcat + Spring Security (via old Boot 3.4.3 BOM) | Spring Boot fat JAR | CRITICAL | Fixed - Boot 3.5.11, pinned Tomcat 10.1.59 + Spring Security 6.5.11 |

### 1.3 What's Already Good

- Spring Boot Actuator structure is in place (health endpoints usable)
- Swagger/OpenAPI documentation configured
- JaCoCo code coverage and Maven Checkstyle configured
- React Testing Library and Jest test setup present
- Lombok reduces boilerplate, keeping code clean
- RestTemplate correctly scoped to `@Profile("dev")` for DataLoader

---

## 2. Target Architecture

### 2.1 Architecture Diagram

```
╔══════════════════════════════════════════════════════════════════════════╗
║  DEVELOPER WORKSTATION                                                   ║
║  ┌---------┐  git push   ┌------------------------------------------┐   ║
║  |  VS Code |------------▶|  GitHub (Public Repo)                   |   ║
║  |  + Kiro  |             |  branch: candidate-assessment           |   ║
║  └---------┘             └--------------┬---------------------------┘   ║
╚══════════════════════════════════════════╪═══════════════════════════════╝
                                           | webhook trigger
                         ╔═════════════════▼═══════════════════════════╗
                         ║  GITHUB ACTIONS - SECURE PIPELINE           ║
                         ║                                              ║
                         ║  ┌------------┐  ┌----------------------┐  ║
                         ║  | Secret     |  | (blocked if secrets  |  ║
                         ║  | Detection  |--▶  found)              |  ║
                         ║  └-----┬------┘  └----------------------┘  ║
                         ║        |                                     ║
                         ║  ┌-----▼------┐  ┌---------------------┐   ║
                         ║  | Frontend   |  | Backend Security     |   ║
                         ║  | Security   |  | • OWASP Dep-Check    |   ║
                         ║  | • npm audit|  | • Semgrep Java SAST  |   ║
                         ║  | • Semgrep  |  └---------┬-----------┘   ║
                         ║  | • Licenses |            |               ║
                         ║  └-----┬------┘            |               ║
                         ║        └----------┬---------┘               ║
                         ║               ┌---▼--------------------┐    ║
                         ║               | Container Security      |    ║
                         ║               | • Trivy IaC config scan |    ║
                         ║               | • Trivy image scan x2   |    ║
                         ║               └---┬--------------------┘    ║
                         ║                   | (on main branch only)   ║
                         ║               ┌---▼--------------------┐    ║
                         ║               | Build & Push to GHCR   |    ║
                         ║               | (signed + attested)     |    ║
                         ║               └---┬--------------------┘    ║
                         ╚═══════════════════╪════════════════════════╝
                                             |
                         ╔═══════════════════▼════════════════════════╗
                         ║  DEPLOYMENT ENVIRONMENT                    ║
                         ║                                            ║
                         ║  ┌--------------------------------------┐  ║
                         ║  |  NGINX Reverse Proxy / Load Balancer |  ║
                         ║  |  TLS termination (Let's Encrypt)     |  ║
                         ║  |  WAF rules (rate limiting, headers)  |  ║
                         ║  └--------------┬-----------------------┘  ║
                         ║                 |                           ║
                         ║    ┌------------┴------------┐             ║
                         ║    ▼                         ▼             ║
                         ║  ┌--------------┐  ┌------------------┐   ║
                         ║  | country-     |  | country-service   |   ║
                         ║  | flags-app    |  | Spring Boot       |   ║
                         ║  | nginx:alpine |  | JRE Alpine        |   ║
                         ║  | non-root     |  | non-root UID 1001 |   ║
                         ║  | read-only FS |  | read-only FS      |   ║
                         ║  └--------------┘  └--------┬---------┘   ║
                         ║                             |              ║
                         ║                    ┌--------▼---------┐   ║
                         ║                    |  PostgreSQL       |   ║
                         ║                    |  (replaces H2)   |   ║
                         ║                    |  encrypted at    |   ║
                         ║                    |  rest            |   ║
                         ║                    └------------------┘   ║
                         ║                                            ║
                         ║  ┌--------------------------------------┐  ║
                         ║  |  Secrets Manager (AWS SM / Vault)    |  ║
                         ║  |  • DB credentials                    |  ║
                         ║  |  • API keys                          |  ║
                         ║  |  • TLS certificates                  |  ║
                         ║  └--------------------------------------┘  ║
                         ╚════════════════════════════════════════════╝
                                             |
                         ╔═══════════════════▼════════════════════════╗
                         ║  OBSERVABILITY                             ║
                         ║  • Structured logging -> ELK / CloudWatch  ║
                         ║  • Metrics -> Prometheus + Grafana          ║
                         ║  • Alerts -> PagerDuty / Slack              ║
                         ║  • Security events -> SIEM                  ║
                         ╚════════════════════════════════════════════╝
```

### 2.2 Security Integration Points

Security is embedded at every stage rather than applied as a final gate:

```
Code          ->  Commit        ->  Build         ->  Deploy       ->  Runtime
-----------------------------------------------------------------------------
IDE linting      Pre-commit       Secret scan      Image sign      WAF
Type safety      hooks            Dep audit        SBOM gen        Rate limiting
SAST plugin      Secret scan      SAST (Semgrep)   Env secrets     Anomaly alerts
                 Commit sign      OWASP DC         RBAC            Log monitoring
                                  Trivy IaC        Non-root        SIEM events
                                  Trivy image      Read-only FS    CVE patching
```

---

## 3. Tool Selection and Justification

### 3.1 Security Toolchain

| Category | Tool Chosen | Alternatives Considered | Why This Choice |
|----------|------------|------------------------|-----------------|
| Secret Detection | Custom Python engine | truffleHog, detect-secrets | Full control over patterns, false-positive tuning, no external dependency in pipeline |
| SAST | Semgrep | SonarQube, CodeQL | Free OSS rulesets for Java+JS+React, fast, GitHub-native SARIF integration |
| Dependency Scan (Java) | OWASP Dependency-Check | Snyk, Grype | Free, NVD-backed, Maven plugin - no third-party API key required |
| Dependency Scan (JS) | npm audit | Snyk, Yarn audit | Built-in to npm, no setup needed, reliable for Node.js CVEs |
| Container Scan | Trivy | Snyk, Grype, Clair | Single tool covers IaC + image + SBOM; fast; GitHub Action available |
| IaC Scan | Trivy config | Checkov, tfsec | Already using Trivy; avoids adding another tool |
| License Check | license-checker | FOSSA, licensee | Simple npm package, zero config for Node.js |
| Container Runtime | Docker + Compose | Podman, Kubernetes | Appropriate for the scale; K8s path documented in roadmap |
| Secrets Manager | AWS Secrets Manager | HashiCorp Vault, Doppler | Native AWS integration; Vault documented as alternative |
| Reverse Proxy | Nginx | Traefik, Caddy | Industry standard, well-understood security model |

### 3.2 Why Not X?

**SonarQube over Semgrep**: SonarQube Community requires a running server and persistent DB.
Semgrep runs as a stateless GitHub Action with no infrastructure to maintain, which is
the right fit for an assessment and for early-stage teams.

**Snyk over OWASP DC + npm audit**: Snyk requires an API key and organisation account.
OWASP DC + npm audit achieve the same outcome with zero external dependencies, keeping
the pipeline functional without any credential setup.

**Kubernetes over Docker Compose**: The application is currently two containers with no
horizontal scaling requirement. Introducing Kubernetes now adds complexity that doesn't
solve a real problem yet. The roadmap (Section 5) covers the migration path when
scaling demands it.

---

## 4. Security Architecture Decisions

### 4.1 Defence in Depth Model

Security controls are layered so that the failure of any single control does not
lead to a breach:

```
Layer 1 - Developer (IDE)
  └-- ESLint security rules, type checking, SAST plugin feedback

Layer 2 - Source Control (GitHub)
  └-- Branch protection, required PR reviews, signed commits

Layer 3 - CI Pipeline (GitHub Actions)
  └-- Secret scan -> Dep audit -> SAST -> Container scan -> Quality gate

Layer 4 - Container (Docker)
  └-- Non-root, read-only FS, cap_drop ALL, no-new-privileges

Layer 5 - Network (Nginx + Compose)
  └-- TLS, security headers, CSP, rate limiting, network segmentation

Layer 6 - Runtime (Application)
  └-- Spring Security, input validation, structured error responses

Layer 7 - Observability
  └-- Structured logs, anomaly detection, SIEM, alerting
```

An attacker would need to defeat all 7 layers to achieve a meaningful breach.

### 4.2 Secrets Management Architecture

Current state (assessment): `.env` file injected at runtime, excluded from git.

Target state (production):

```
Application startup
      |
      ▼
AWS ECS Task / K8s Pod
      |
      ├-- IAM Role (no long-lived credentials)
      |
      ▼
AWS Secrets Manager
      |
      ├-- DB_PASSWORD      -> injected as env var
      ├-- API_KEY          -> injected as env var
      └-- TLS_CERT         -> mounted as volume
```

No secrets exist in:
- Source code
- Docker images
- CI environment variables (except ephemeral GitHub Actions secrets)
- Log files (structured logging must redact credential fields)

### 4.3 Network Security Model

```
Internet
    |
    ▼  HTTPS only (HTTP -> 301 redirect)
┌-------------------------------┐
|  WAF / Load Balancer          |  Rate limiting: 100 req/s per IP
|  (AWS ALB + WAF or CloudFront)|  Geo-blocking (optional)
└---------------┬---------------┘
                |  Internal network only
    ┌-----------┴-------------┐
    |  DMZ subnet              |
    |  Nginx reverse proxy     |  TLS termination, security headers
    └-----------┬-------------┘
                |  Private subnet - no direct internet access
    ┌-----------┴-------------------------┐
    |                                      |
    ▼                                      ▼
country-flags-app                  country-service
(frontend-net)                     (backend-net)
    |                                      |
    └--------------------------------------┘
                    |
                    ▼  Encrypted connection (TLS)
             PostgreSQL
             (data subnet - most restricted)
```

### 4.4 API Security Controls

The current API has no authentication. Target state adds:

1. **JWT Bearer tokens** - stateless auth, short-lived (15 min access, 7 day refresh)
2. **Rate limiting** - per-IP and per-user via Spring's `HandlerInterceptor` or API gateway
3. **Input validation** - `@Valid` + Bean Validation on all request parameters
4. **CORS restriction** - replace `allowedHeaders("*")` with explicit header whitelist
5. **Audit logging** - log all API calls with user identity, IP, timestamp, response code

---

## 5. Implementation Roadmap

Prioritised into three phases based on risk reduction value and implementation effort:

### Phase 1 - Immediate (Week 1-2) · Fix Current Vulnerabilities

**Goal**: Eliminate all HIGH/CRITICAL findings identified in Section 1.2

| Priority | Action | Effort | Risk Reduced |
|----------|--------|--------|-------------|
| P1 | Remove hardcoded `password` from `application.properties` | 1h | HIGH |
| P1 | Fix Spring Security version mismatch in `pom.xml` | 1h | HIGH |
| P1 | Upgrade `axios` from 0.27.2 to 1.x (CVE fixes) | 2h | HIGH |
| P2 | Restrict CORS `allowedHeaders` to explicit list | 1h | MEDIUM |
| P2 | Disable H2 console in all non-dev profiles | 30m | MEDIUM |
| P2 | Add `.env` to `.gitignore` (done in this assessment) | 5m | HIGH |
| P3 | Configure `application.properties` to read credentials from env vars | 1h | HIGH |

**Deliverable**: All security scanners pass with zero HIGH/CRITICAL findings.

### Phase 2 - Short Term (Month 1-2) · Harden the Platform

**Goal**: Establish repeatable, automated security practices

| Action | Effort | Outcome |
|--------|--------|---------|
| Deploy both apps as Docker containers (Block 3 Dockerfiles) | 1 day | Reproducible, hardened runtime |
| Activate the GitHub Actions pipeline on every PR (Block 2) | 1 day | Automated security gate |
| Replace H2 with PostgreSQL; enable TLS on DB connection | 2 days | Production-grade persistence |
| Add Spring Security JWT authentication to API | 3 days | Authenticated endpoints |
| Configure Nginx reverse proxy with TLS (Let's Encrypt) | 1 day | HTTPS everywhere |
| Add structured logging (Logback + JSON format) | 1 day | Searchable audit trail |
| Set up Prometheus + Grafana for metrics | 2 days | Operational visibility |
| Implement pre-commit hooks (secret detection, lint) | 1 day | Catch issues before push |

**Deliverable**: Fully containerised, authenticated, HTTPS-only application with
automated CI security gates.

### Phase 3 - Medium Term (Month 3-6) · Scale and Mature

**Goal**: Enterprise-grade security posture

| Action | Effort | Outcome |
|--------|--------|---------|
| Migrate to AWS ECS or Kubernetes | 1-2 weeks | Auto-scaling, self-healing |
| Integrate AWS Secrets Manager / HashiCorp Vault | 3 days | Centralised secret rotation |
| Add DAST scanning (OWASP ZAP) to pipeline | 2 days | Runtime vulnerability detection |
| Implement Software Bill of Materials (SBOM) generation | 1 day | Supply chain transparency |
| Set up SIEM (AWS Security Hub / ELK) | 1 week | Security event correlation |
| Container image signing (Cosign + GitHub Attestation) | 2 days | Supply chain integrity |
| WAF rules + DDoS protection (AWS WAF / Cloudflare) | 3 days | Edge-level protection |
| Incident response runbooks (Block 5 material) | 2 days | Prepared response capability |
| Security training + threat modelling sessions | Ongoing | Security culture |

**Deliverable**: Production-ready, auditable, enterprise security posture.

---

## 6. Team Workflow Optimisation

### 6.1 Shift-Left Security Model

```
Traditional (Shift-Right):
Dev writes code -> QA tests -> Security reviews -> (hopefully) fix -> Deploy
Problem: Security is a bottleneck at the end; fixing late is 10-100x more expensive

Shift-Left (this architecture):
Security tools in IDE -> Pre-commit hooks -> PR gate -> Automated pipeline
Problem solved: Developers get security feedback in seconds, not weeks
```

### 6.2 Developer Experience

Key principle: **security controls should not slow developers down**.

- Pre-commit hooks run in <5 seconds (secret scan only, not full OWASP DC)
- Pipeline parallelises frontend and backend scans to minimise wall-clock time
- MEDIUM findings are warnings, not blockers - developers can keep moving
- Scan reports are attached to every PR - no context switching to find results
- Semgrep provides inline code annotations in GitHub - fix at the exact line

### 6.3 Pull Request Workflow

```
Developer creates PR
        |
        ▼
GitHub Actions pipeline triggers
        |
        ├-- Secret scan (fastest - ~30s)
        |
        ├-- npm audit + Semgrep (parallel, ~3 min)
        |
        ├-- OWASP Dependency-Check + Semgrep Java (parallel, ~5 min)
        |
        └-- Trivy container scans (~2 min)
                |
                ├-- All pass -> PR marked green -> reviewer can merge
                └-- Any fail -> PR blocked -> developer notified with report link
```

---

## 7. Cost and Complexity Trade-offs

| Approach | Cost | Complexity | Security Value | Recommendation |
|----------|------|------------|----------------|----------------|
| Current (no security tooling) | $0 | Low | No Very Low | Replace immediately |
| This assessment (OSS only) | $0 | Medium | Done High | **Implement now** |
| Add Snyk Pro | ~$98/dev/month | Medium | Done Very High | Consider at 5+ devs |
| Full SonarQube server | ~$150/month (cloud) | High | Done Very High | Consider at 10+ devs |
| AWS Security Hub + GuardDuty | ~$50-200/month | Medium | Done Very High | Implement at AWS deployment |
| HashiCorp Vault (self-hosted) | Infra cost only | High | Done Critical | Use AWS SM as simpler alternative |

**Key takeaway**: This assessment demonstrates that a high-quality DevSecOps posture
is achievable at **zero incremental cost** using OSS tools. The foundation is correct;
commercial tools add convenience and advanced features but are not prerequisites.

---

## 8. Compliance Alignment

The architecture maps naturally to common compliance frameworks:

| Control | Framework | Implementation |
|---------|-----------|---------------|
| Access control | SOC2 CC6, ISO27001 A.9 | JWT auth, RBAC, non-root containers |
| Secrets management | SOC2 CC6.7, PCI DSS 3.4 | `.env` -> Secrets Manager migration |
| Vulnerability management | SOC2 CC7.1, NIST CSF ID.RA | OWASP DC, Trivy, npm audit in pipeline |
| Change management | SOC2 CC8.1 | PR reviews, branch protection, CI gates |
| Audit logging | SOC2 CC7.2, ISO27001 A.12.4 | Structured logging, SIEM integration |
| Encryption in transit | PCI DSS 4.1, HIPAA §164.312(e) | TLS everywhere (Phase 2) |
| Container security | CIS Docker Benchmark | Non-root, cap_drop, read-only FS |

---

## 9. Summary

This architecture demonstrates how security can be integrated naturally at every
stage of the software delivery lifecycle without adding significant overhead:

1. **Developers** get immediate feedback through IDE plugins and pre-commit hooks
2. **Every PR** is automatically scanned by 5 security tools before any reviewer looks at it
3. **Container images** are hardened by default - non-root, minimal, read-only
4. **Secrets never touch source code** - enforced by tooling, not just policy
5. **The platform scales** from the current Docker Compose deployment to Kubernetes
   without changing the security model

The most important insight: **security tools only provide value when they are
automated and integrated**. A checklist that depends on a human remembering to run
it will fail. This architecture makes the secure path the default path.
