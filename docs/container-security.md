# Block 3: Container Security

## Overview

Two production-ready, hardened Docker images with a secure Docker Compose deployment.
Both images follow multi-stage build patterns and apply defence-in-depth at every layer.

## Image Architecture

```
application/
├── country-service/
│   └── Dockerfile          ← Spring Boot (Java 11) — 2-stage build
└── country-flags-app/
    ├── Dockerfile           ← React 18 + Nginx — 2-stage build
    └── nginx.conf           ← Hardened Nginx configuration

infrastructure/
├── docker-compose.yml       ← Secure orchestration
└── .env.example             ← Credentials template (never commit .env)
```

## Security Controls Applied

### 1. Multi-Stage Builds

| Stage | Image | Purpose | Ships to production? |
|-------|-------|---------|---------------------|
| builder (backend) | `eclipse-temurin:11-jdk-alpine` | Compile JAR | ❌ No |
| runtime (backend) | `eclipse-temurin:11-jre-alpine` | Run JAR | ✅ Yes |
| builder (frontend) | `node:18-alpine` | `npm build` | ❌ No |
| runtime (frontend) | `nginx:1.27-alpine` | Serve static files | ✅ Yes |

**Why it matters**: The build stage contains Maven, npm, all `node_modules`, the JDK,
and build caches — all potential attack surface. None of it reaches the final image.

### 2. Non-Root Users

Both containers run as unprivileged users:

| Service | User | UID | How |
|---------|------|-----|-----|
| country-service | `appuser` | 1001 | Created in Dockerfile via `adduser` |
| country-flags-app | `nginx` | 101 | Built-in nginx:alpine user |

Running as root is explicitly blocked in docker-compose with `user: "1001:1001"`.
If a vulnerability allows code execution inside the container, the attacker gets a
shell with no write access and no sudo — severely limiting lateral movement.

### 3. Read-Only Root Filesystem

Both containers use `read_only: true` in docker-compose. Write access is granted
only where strictly needed, via `tmpfs` mounts:

| Service | tmpfs path | Purpose |
|---------|-----------|---------|
| country-service | `/tmp` | Spring/Tomcat temp files |
| country-flags-app | `/var/cache/nginx` | Nginx proxy cache |
| country-flags-app | `/var/run` | nginx.pid file |

An attacker who achieves RCE cannot write a backdoor, cron job, or modified binary
to disk.

### 4. Linux Capability Dropping

Both services use:
```yaml
cap_drop:
  - ALL
```

This removes all Linux capabilities (e.g. `NET_ADMIN`, `SYS_PTRACE`, `CHOWN`).
Neither Spring Boot nor Nginx requires any special capabilities to operate — they
run fine with zero capabilities.

### 5. No Privilege Escalation

```yaml
security_opt:
  - no-new-privileges:true
```

Prevents setuid/setgid binaries inside the container from gaining additional
privileges, even if a malicious binary is somehow introduced.

### 6. Resource Limits

Prevents a compromised container from exhausting host resources (DoS via CPU/memory):

| Service | Memory Limit | CPU Limit |
|---------|-------------|-----------|
| country-service | 512 MB | 1.0 core |
| country-flags-app | 128 MB | 0.5 core |

### 7. Network Segmentation

```
Internet
    │
    └── host port 127.0.0.1:3000  ← loopback only, not 0.0.0.0
            │
    country-flags-app  (frontend-net + backend-net)
            │
    country-service    (backend-net only)
```

- `country-service` is never directly exposed to the host
- `frontend-net` has ICC (inter-container communication) disabled — containers
  on this network cannot talk to each other laterally
- The backend port (8081) is `expose`-only, not `ports` — invisible to the host

### 8. Secrets Management

Credentials are **never** hardcoded in Dockerfiles or docker-compose.yml.
They are injected at runtime from a `.env` file (excluded from version control):

```bash
# Copy the template and fill in real values
cp infrastructure/.env.example infrastructure/.env
# Edit .env with real passwords
docker compose --env-file infrastructure/.env up
```

The `.gitignore` must include `infrastructure/.env` (see root `.gitignore`).

### 9. Nginx Security Headers (Frontend)

The custom `nginx.conf` adds the following headers on every response:

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Frame-Options` | `SAMEORIGIN` | Prevent clickjacking |
| `X-Content-Type-Options` | `nosniff` | Prevent MIME sniffing |
| `X-XSS-Protection` | `1; mode=block` | Legacy XSS filter |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Limit URL leakage |
| `Content-Security-Policy` | Scoped to `'self'` | Prevent XSS, data injection |
| `Permissions-Policy` | geo/mic/cam disabled | Limit browser API access |

`server_tokens off` hides the Nginx version from attackers.

### 10. Health Checks

Every service has a `HEALTHCHECK` instruction in its Dockerfile and a matching
`healthcheck` in docker-compose. The frontend `depends_on` the backend with
`condition: service_healthy` — the stack only starts when the API is ready.

## Running the Stack

```bash
# 1. Copy and configure credentials
cp infrastructure/.env.example infrastructure/.env
# Edit infrastructure/.env — set DB_PASSWORD

# 2. Build and start
docker compose -f infrastructure/docker-compose.yml --env-file infrastructure/.env up --build

# 3. Access
#    Frontend: http://localhost:3000
#    API:      http://localhost:8081/api/countries  (internal only)

# 4. Stop
docker compose -f infrastructure/docker-compose.yml down
```

## Container Scanning Integration

The pipeline (Block 2) automatically scans both images with **Trivy**:

```bash
# Manual scan — run before pushing
trivy image country-service:latest --severity CRITICAL,HIGH
trivy image country-flags-app:latest --severity CRITICAL,HIGH

# IaC/config scan — check Dockerfiles and compose for misconfigurations
trivy config . --severity CRITICAL,HIGH
```

## Base Image Selection Rationale

| Image | Why chosen |
|-------|-----------|
| `eclipse-temurin:11-jdk-alpine` | Adoptium LTS, smaller than Debian-based, actively patched |
| `eclipse-temurin:11-jre-alpine` | JRE only — removes compiler, jshell, javac from final image |
| `node:18-alpine` | LTS Node, Alpine reduces CVE surface vs Debian node |
| `nginx:1.27-alpine` | Current stable, Alpine base, minimal footprint (~40 MB) |

All base images use pinned minor versions (not `latest`) to ensure reproducible builds.
