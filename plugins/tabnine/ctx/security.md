# Security and CVE resolution

This is the tool for any **security search** or **work to resolve security issues** via `ctx-cli`. The centerpiece is `get_cve_resolution_status` — it returns the CVE inbox with the **suggested fix embedded in the entity**: each row's `data.recommendedAction` is either a ready-to-apply unified diff or a markdown advisory.

## When to reach for this

| Task | Tool |
|---|---|
| List CVEs in the resolution pipeline, with the suggested fix attached | `get_cve_resolution_status` |
| Filter by severity / criticality (critical, high, …) | `get_cve_resolution_status` + post-filter `data.severity` with jq |
| Look up the resolution for one specific CVE | `get_cve_resolution_status -p cveId=<id>` |
| CWE / exploit maturity for a known CVE | `find_entities` with `entityTypes=["Vulnerability"]` |
| List **SAST** findings in the resolution pipeline, with the suggested fix attached | `get_sast_resolution_status` |
| Look up the resolution for one specific SAST rule | `get_sast_resolution_status -p ruleId=<rule>` |

## Triage the CVE inbox — `get_cve_resolution_status`

All filters are optional — call with none to enumerate every `CVEResolution` in the tenant. **Each row carries the suggested fix in `data.recommendedAction`** (full diff text or markdown advisory).

```bash
# Auto-fix diffs ready to apply (no PR open yet)
ctx-cli mcp call get_cve_resolution_status -p recommendedActionKind=diff -p status=fix_pending_review -o json

# Auto-fix PRs awaiting review/merge
ctx-cli mcp call get_cve_resolution_status -p resolutionRoute=auto_fix -p status=fix_pending_review -o json

# CVEs that need a human (manual triage queue)
ctx-cli mcp call get_cve_resolution_status -p resolutionRoute=human_required -o json

# One specific CVE across all repos
ctx-cli mcp call get_cve_resolution_status -p cveId=CVE-2021-44228 -o json

# All resolutions for a single repository
ctx-cli mcp call get_cve_resolution_status -p repository=acme/payment-svc -o json
```

Filters:

| Param | Values |
|---|---|
| `status` | `resolved` \| `fix_pending_review` \| `fix_merged` \| `fix_closed` \| `escalated` \| `failed` |
| `resolutionRoute` | `auto_fix` \| `human_required` \| `vex_attestation` |
| `recommendedActionKind` | `diff` \| `advisory` |
| `cveId` | e.g. `CVE-2021-44228` |
| `repository` | e.g. `acme/order-service` |
| `limit` | default 25, hard cap 500 |

Each row's `data` includes `severity`, `recommendedAction`, `recommendedActionKind`, `resolutionRoute`, `status`, `prUrl`, `prNumber`, `prHeadSha`, `fixType`, `fixVersion`, `agentRunId`, `resolvedAt`. **When `recommendedActionKind=diff`, the diff is ready to apply as-is** — no transformation needed.

## Filter by severity / criticality

`data.severity` is on every CVEResolution row directly — no extra lookup needed. `get_cve_resolution_status` does not yet expose a server-side severity filter, so post-filter client-side:

```bash
# All critical-severity resolutions
ctx-cli mcp call get_cve_resolution_status -p limit=500 -o json \
  | jq '.result | map(select(.data.severity == "critical"))'

# High+critical CVEs still needing a human
ctx-cli mcp call get_cve_resolution_status -p resolutionRoute=human_required -p limit=500 -o json \
  | jq '.result | map(select(.data.severity == "critical" or .data.severity == "high"))'
```

Severity values: `low` \| `medium` \| `high` \| `critical`.

For deeper context on the underlying vulnerability (CWE, exploit maturity, affected versions), follow the `cveId` to its `Vulnerability` entity:

```bash
ctx-cli mcp call find_entities -p query="<cveId>" -p 'entityTypes=["Vulnerability"]' -o json
```

The `Vulnerability` entity exposes `data.cwe`, `data.exploitMaturity` (`Proof of Concept`, `Mature`, …), `data.affectedVersions`, `data.isPatchable`, `data.isUpgradable`, `data.alertSource` (`snyk` \| `checkmarx`).

## Triage the SAST inbox — `get_sast_resolution_status`

The SAST analog of `get_cve_resolution_status`, for **source-code** findings (Snyk Code / Checkmarx SAST) that the `sast-auto-resolver` agent has triaged. All filters are optional.

```bash
# Code-fix PRs awaiting review/merge
ctx-cli mcp call get_sast_resolution_status -p resolutionRoute=auto_fix -p status=fix_pending_review -o json

# Findings that need a human (manual triage queue)
ctx-cli mcp call get_sast_resolution_status -p resolutionRoute=human_required -o json

# Suppressed findings (false positive / not exploitable) — the reason is in data.justification
ctx-cli mcp call get_sast_resolution_status -p resolutionRoute=not_applicable -o json

# All resolutions for one SAST rule, or one repository
ctx-cli mcp call get_sast_resolution_status -p ruleId=sql-injection -o json
ctx-cli mcp call get_sast_resolution_status -p repository=acme/api-service -o json
```

Filters:

| Param | Values |
|---|---|
| `status` | `resolved` \| `fix_pending_review` \| `fix_merged` \| `escalated` \| `failed` |
| `resolutionRoute` | `auto_fix` \| `human_required` \| `not_applicable` |
| `suppressionType` | `false_positive` \| `not_exploitable` \| `vulnerable_code_not_in_execute_path` \| `mitigated_elsewhere` \| `accepted_risk` |
| `ruleId` | e.g. `sql-injection` |
| `repository` | e.g. `acme/api-service` |
| `file` | e.g. `src/services/user-service.ts` |
| `limit` | default 25, hard cap 500 |

Each row's `data` includes `ruleId`, `cwe`, `owasp`, `file`, `line`, `severity`, `engine` (`snyk` \| `checkmarx`), `fixDescription`, `prUrl`, `prNumber`, `recommendedAction`, `escalationReason`, `suppressionType`, `resolvedAt`. **Route 2 (`auto_fix`) fixes are code patches at `file:line`, not version bumps.** `data.severity` is on every row — post-filter client-side the same way as CVEs (`jq '.result | map(select(.data.severity == "critical"))'`).

## Do not call these

The CVE and SAST auto-remediation pipelines run these tools from background agents — calling them ad-hoc will trip dedup gates or write inconsistent state:

- `sync_snyk_vulnerabilities` / `reconcile_snyk_vulnerabilities`
- `sync_checkmarx_vulnerabilities` / `reconcile_checkmarx_vulnerabilities`
- `sweep_pending_cves`
- `sweep_pending_sast`
