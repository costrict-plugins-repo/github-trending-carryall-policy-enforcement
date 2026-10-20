---
name: carryall-policy
description: Guides policy-aware vault access via Carryall. Enforces compile_policy → envelope → action workflow for all sensitive data operations.
---

# Carryall Policy Enforcement

**Always call `carryall_compile_policy` FIRST** before accessing any sensitive vault data or performing any action that requires scoped permissions.

## Core workflow

1. **Get an envelope** — call `carryall_compile_policy` with:
   - `agent_id`: your agent identity (see table below)
   - `intent`: plain English description of the task
   - `available_scopes`: list of scopes you might need

2. **Use the envelope** — pass the returned signed envelope to:
   - `carryall_read_document(envelope, uri, purpose)` — read a document
   - `carryall_write_document(envelope, ...)` — create or update a document
   - `carryall_query_documents(envelope, domain, query)` — search documents
   - `carryall_check_access(envelope, scope, resource)` — pre-flight access check
   - `carryall_audit_log(envelope)` — query the audit trail

3. **Every action is audited** — all tool calls are logged with agent, scope, resource, and timestamp in a tamper-evident audit trail.

## Agent identities (use least privilege)

| agent_id | Vaults | Use for |
|----------|--------|---------|
| `executive-agent` | all (read), meta (write) | Cross-domain queries, audits |
| `finance-agent` | finance | Budget, transactions, subscriptions |
| `startup-agent` | startup | Projects, strategy, market research |
| `health-agent` | health | Health records (restricted) |
| `personal-agent` | personal | Journal, learning, email |
| `community-agent` | community | 6529 community data |

## Vault URIs

```
slos://vaults/finance/...     — financial data
slos://vaults/startup/...     — startup projects
slos://vaults/health/...      — health records
slos://vaults/personal/...    — personal data
slos://vaults/community/...   — community intelligence
slos://vaults/meta/...        — system metadata, audit logs
```

## Example

```
carryall_compile_policy(
  agent_id="finance-agent",
  intent="read Q1 budget summary for cost analysis",
  available_scopes=["vault:finance:read"]
)
→ returns signed AuthorityEnvelope (valid 300s, scope-bound)

carryall_read_document(
  envelope=<returned envelope>,
  uri="slos://vaults/finance/budgets/q1-2026.md",
  purpose="Q1 cost analysis"
)
```

## Security rules

- Never skip `carryall_compile_policy` — accessing data without an envelope bypasses the audit trail
- Use the agent with the **least privilege** needed for the task
- Envelopes expire (default 300s) — get a fresh one for each task
- The PolicyDecisionPoint is deterministic: same intent → same scopes, every time
