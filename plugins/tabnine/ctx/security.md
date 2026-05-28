# Security and CVE resolution

This is the tool for any **security search** or **work to resolve security issues** via `ctx-cli`. The centerpiece is `get_cve_resolution_status` — it returns the CVE inbox with the **suggested fix embedded in the entity**: each row's `data.recommendedAction` is either a ready-to-apply unified diff or a markdown advisory.

## When to reach for this

| Task | Tool |
|---|---|
| List CVEs in the resolution pipeline, with the suggested fix attached | `get_cve_resolution_status` |
| Filter by severity / criticality (critical, high, …) | `find_entities` with `entityTypes=["Vulnerability"]` — severity is in `data.severity` |
| Look up the resolution for one specific CVE | `get_cve_resolution_status -p cveId=<id>` |
| Vet a package before adding or upgrading it | `dependency_check` |

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

Each row's `data` includes `recommendedAction`, `prUrl`, `prHeadSha`, `agentRunId`, `resolutionRoute`, `status`. **When `recommendedActionKind=diff`, the diff is ready to apply as-is** — no transformation needed.

## Filter by severity / criticality

`get_cve_resolution_status` does not take a severity filter directly — severity lives on the `Vulnerability` entity. Workflow:

```bash
# Step 1 — find high/critical vulnerabilities (semantic search; severity returned inline)
ctx-cli mcp call find_entities -p query="critical" -p 'entityTypes=["Vulnerability"]' -p limit=50 -o json

# Step 2 — for each cveId of interest, fetch the suggested resolution
ctx-cli mcp call get_cve_resolution_status -p cveId=<cveId-from-step-1> -o json
```

Each `Vulnerability` entity returns:

- `data.severity` — `low` \| `medium` \| `high` \| `critical`
- `data.exploitMaturity` — `Proof of Concept`, `Mature`, etc.
- `data.cveId`, `data.cwe`, `data.affectedPackage`, `data.affectedVersions`, `data.ecosystem`, `data.isPatchable`, `data.isUpgradable`, `data.alertSource` (`snyk` \| `checkmarx`)

Sort or filter client-side (e.g. `jq 'map(select(.data.severity=="critical"))'`).

## Vet a package — `dependency_check`

Before adding or upgrading any dependency:

```bash
ctx-cli mcp call dependency_check -p packageName=lodash -p ecosystem=npm -o json
```

Returns current vulnerabilities, upgrade history, **revert detection** (`PREVIOUSLY_REVERTED` flag with `priorRevertCount` — "this bump broke CI N times before"), migration examples, and recommended internal alternatives. Replaces 5 primitives in one call.

`ecosystem` accepts `npm`, `maven`, `pypi`, `go`. Omit to search all.

## See also

- `get_cve_blast_radius -p cveId=<id>` — transitive impact of one CVE (services + dep chains, up to 10 hops). Use when prioritizing the inbox.
- `get_security_alerts -p repo=<org/name>` — raw vulnerability list for a single repository (vulnerabilities, not resolutions).
- `list_all_vulnerabilities` — diagnostic enumeration of every `Vulnerability` entity in the graph.

## Do not call these

The CVE auto-remediation pipeline runs these tools from background agents — calling them ad-hoc will trip dedup gates or write inconsistent state:

- `sync_snyk_vulnerabilities` / `reconcile_snyk_vulnerabilities`
- `sync_checkmarx_vulnerabilities` / `reconcile_checkmarx_vulnerabilities`
- `sweep_pending_cves`

> Note: `get_cve_resolution_status` and `get_cve_blast_radius` are currently **tier-2** tools, so they will not appear in the default `ctx-cli mcp list` output. Use them by name as documented here.
