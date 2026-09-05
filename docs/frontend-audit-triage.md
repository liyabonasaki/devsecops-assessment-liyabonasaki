# Frontend Dependency Audit — Triage & Accepted Findings

This document explains the risk-based policy the pipeline applies to `npm audit`
findings in the `country-flags-app` frontend, and records which findings are
**accepted with a remediation plan** versus which are **blocking**.

## The Situation

The provided frontend is a **Create React App (CRA)** project built with
`react-scripts@5.0.1`. A full `npm audit` reports ~36 HIGH/CRITICAL advisories.
Investigating them shows they fall into two very different risk categories.

## Risk-Based Gate Policy

The pipeline runs **two** npm audits:

| Audit | Command | Behaviour |
|-------|---------|-----------|
| Production dependencies | `npm audit --omit=dev --audit-level=critical` | **BLOCKING** — fails the build |
| Full tree (incl. dev/build tooling) | `npm audit --audit-level=high` | **INFORMATIONAL** — reported, never blocks |

### Why this is the correct posture

A vulnerability's real risk depends on **where it runs**, not just its CVSS score:

- **Production dependencies** (`react`, `react-dom`, `react-router-dom`, `axios`,
  `@mui/material`) are bundled and served to the browser. A vulnerability here
  reaches end users → **must block**.
- **Dev / build-time dependencies** (`webpack-dev-server`, `postcss`, `svgo`,
  `nth-check`, `terser`, the CRA toolchain) run only on the developer's machine
  or the CI build agent. They are **not** present in the static bundle Nginx
  serves in production → high severity, but low real-world risk in this context.

Blocking delivery on unfixable dev-tool advisories would be security theatre: it
stops shipping without reducing user-facing risk.

## Accepted Findings (Dev/Build Tooling)

The majority of the ~36 advisories originate from the `react-scripts` dependency
tree. They are **accepted** because:

1. They do not ship to the browser bundle (build-time only).
2. They cannot be fixed without `npm audit fix --force`, which downgrades
   `react-scripts` and **breaks the build**.
3. CRA itself is deprecated (the React team no longer recommends it), so patching
   its transitive tree is not a sustainable path.

Representative examples:

| Advisory (transitive) | Comes via | Why accepted |
|-----------------------|-----------|-------------|
| `nth-check` ReDoS | `react-scripts` → `svgo` → `css-select` | Build-time SVG optimisation only |
| `postcss` parsing | `react-scripts` → `resolve-url-loader` | Build-time CSS processing only |
| `webpack-dev-server` source leak | `react-scripts` | Dev server only; never used in prod (Nginx serves static files) |

## Remediation Plan

Tracked in `docs/architecture-design.md` (Phase 2):

1. **Migrate CRA → Vite.** Vite has a dramatically smaller, actively-maintained
   dependency tree and eliminates the vast majority of these advisories. This is
   the strategic fix.
2. Re-run the full audit after migration; the informational count should drop to
   near zero, at which point the gate can be tightened to block on HIGH as well.

## Changes Already Made

- **Removed `codecov@3.8.2`** from `devDependencies`. It was deprecated, unused,
  and the source of the license-check flag. Coverage is handled by JaCoCo
  (backend) and can use GitHub's native coverage tooling (frontend) instead.
- Removed the now-unused `istanbul-lib-coverage` dev dependency it pulled in.

## How to Reproduce Locally

```bash
cd application/country-flags-app
npm ci

# Blocking gate (production deps, CRITICAL only) — should pass
npm audit --omit=dev --audit-level=critical

# Full informational audit (incl. dev tooling)
npm audit --audit-level=high
```
