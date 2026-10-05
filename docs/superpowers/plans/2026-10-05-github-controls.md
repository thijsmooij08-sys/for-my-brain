# GitHub Controls Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add repository-owned GitHub CI, security scanning, supply-chain provenance, Docker checks, and governance without changing PolyTrader runtime or trading authority.

**Architecture:** GitHub Actions runs read-only verification on pull requests and pushes. Security workflows report or gate code/dependency/container findings; none can enable live trading or access wallet credentials. Repository governance files make the paper-only safety boundaries visible to contributors.

**Tech Stack:** GitHub Actions, Python/Ruff/Pyright, npm/Vite, Docker Compose, CodeQL, Dependency Review, OpenSSF Scorecard, artifact attestations, Trivy, Hadolint.

**Spec:** `AGENTS.md`, `docs/INVARIANTS.md`, `docs/SECURITY.md`, and `docs/integrations/GITHUB_ECOSYSTEM.md`.

## Global Constraints

- `LIVE_TRADING_ENABLED=false` remains authoritative.
- CI must never receive wallet keys, exchange credentials, or provider secrets.
- Third-party Actions are pinned to immutable commit SHAs and use least-privilege permissions.
- Existing local verification commands remain authoritative.
- No external trading bot source or secure execution client is imported.

## Review Focus

- A pull request must fail when deterministic tests, lint, typing, migrations, or frontend build fail.
- Workflow permissions must not grant write access to application code or deployment environments.
- Container scanning must not publish or execute an image as a trading service.
- Attestations must prove build provenance without embedding secrets.
- Governance must protect RiskManager, accounting, execution, and live-off invariants.

---

### Task 1: Continuous integration workflow

**Files:**
- Create: `.github/workflows/ci.yml`
- Modify: `.gitignore` (exclude local agent logs)

- [ ] Add pull-request and main-branch CI using immutable official setup actions.
- [ ] Run `scripts/verify.ps1` and Docker Compose configuration validation.
- [ ] Validate workflow YAML and shell syntax locally.

### Task 2: Security and dependency workflows

**Files:**
- Create: `.github/workflows/codeql.yml`
- Create: `.github/workflows/dependency-review.yml`
- Create: `.github/workflows/scorecard.yml`
- Create: `.github/dependency-review-config.yml`

- [ ] Enable Python and JavaScript/TypeScript CodeQL scanning.
- [ ] Gate new critical/high dependency vulnerabilities and disallowed licenses.
- [ ] Run Scorecard with read-only permissions and SARIF upload.

### Task 3: Container and provenance controls

**Files:**
- Create: `.github/workflows/container-security.yml`
- Create: `.github/workflows/attest.yml`

- [ ] Build the API and frontend images without pushing them.
- [ ] Run pinned Hadolint and Trivy checks.
- [ ] Produce build provenance only for a successful, non-secret build; do not publish or deploy.

### Task 4: Repository governance

**Files:**
- Create: `.github/CODEOWNERS`
- Create: `.github/pull_request_template.md`
- Create: `.github/ISSUE_TEMPLATE/bug_report.yml`
- Create: `.github/ISSUE_TEMPLATE/feature_request.yml`
- Create: `SECURITY.md`
- Create: `CONTRIBUTING.md`
- Modify: `docs/integrations/GITHUB_ECOSYSTEM.md`

- [ ] Require review of safety-sensitive paths.
- [ ] Require contributors to report verification results and preserve paper-only boundaries.
- [ ] Document GitHub branch-protection settings that must be enabled after the first push.

### Task 5: Verification and publication

- [ ] Parse every workflow and YAML file.
- [ ] Run backend tests, Ruff, Pyright, frontend build, supply-chain checks, and Docker Compose config.
- [ ] Inspect the final diff for secrets and live-execution paths.
- [ ] Commit the changes and push to the explicitly linked empty repository only after all checks pass.

