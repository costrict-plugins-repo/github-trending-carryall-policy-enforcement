# Carryall Policy Enforcement — Claude Code Plugin

Deterministic IAM for AI agents. Carryall is a **control plane** — it handles policy compilation, cryptographic envelope signing, and audit trails. You bring your own **data plane** (vault backend, database, file system, or any storage layer your agents access).

This separation is by design: your data stays where you control it. Carryall never stores or proxies your data — it only governs who can access what, for how long, and why.

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Claude Code / AI Agent                         │
│                                                 │
│  "Read Q1 budget for cost analysis"             │
│         │                                       │
│         ▼                                       │
│  ┌─────────────────────────────────────┐        │
│  │  Carryall (control plane)           │        │
│  │  ── compile_policy ──────────────── │        │
│  │  Intent → PDP → Minimal scopes     │        │
│  │  Ed25519-signed envelope (300s TTL) │        │
│  │  Tamper-evident audit trail         │        │
│  └──────────────┬──────────────────────┘        │
│                 │ signed envelope                │
│                 ▼                                │
│  ┌─────────────────────────────────────┐        │
│  │  Your data plane (BYO)              │        │
│  │  ── vaults, databases, APIs ─────── │        │
│  │  Verifies envelope → serves data    │        │
│  └─────────────────────────────────────┘        │
└─────────────────────────────────────────────────┘
```

## Install

```
claude plugin marketplace add tronmongoose/agent.carryall_plugin
claude plugin install carryall-policy-enforcement@carryall
```

## Prerequisites

- `authority-runtime` Python package (the Carryall control plane SDK)
- Agent keys initialized: `carryall init` + `carryall keys generate <agent-id>`
- `CARRYALL_SLOS_CONFIG` pointing to your data plane integration config
- `CARRYALL_KEYS_DIR` pointing to your agent key directory
- `OPENAI_API_KEY` set (used by the policy compiler — gpt-4o-mini)

## Tools

| Tool | Description |
|------|-------------|
| `carryall_compile_policy` | Translate intent → minimal-scope signed envelope |
| `carryall_check_access` | Pre-flight permission check |
| `carryall_list_vaults` | List available vaults (requires envelope) |
| `carryall_get_metadata` | Get document metadata and access policies (requires envelope) |
| `carryall_read_document` | Read a document from a vault (requires envelope) |
| `carryall_write_document` | Write a document to a vault (requires envelope) |
| `carryall_query_documents` | Search vault documents (requires envelope) |
| `carryall_audit_log` | Query the tamper-evident audit trail (requires envelope) |

## Workflow

1. Call `carryall_compile_policy` with your agent identity, intent, and available scopes
2. Use the returned signed envelope with any data access tool
3. All actions are logged — viewable via the Authority Dashboard

## Bring your own data plane

Carryall ships with a built-in `MemoryBackend` for testing and a `SlosBackend` for production vault access. The integration config points Carryall at your data plane:

```json
{
  "mcp_command": "./your-data-plane-binary",
  "mcp_args": ["mcp"],
  "mcp_cwd": "/path/to/your/data"
}
```

Any backend that accepts signed envelopes and verifies Ed25519 signatures can serve as a data plane. The `--mock` mode lets you develop and test without any backend at all.

## Deployment modes

```bash
# Stdio (default — for Claude Code)
python3 -m authority_runtime.cli mcp serve

# HTTP (for Bedrock AgentCore, remote clients)
python3 -m authority_runtime.cli mcp serve --transport http --port 8765

# Mock (no data plane required — for testing and development)
python3 -m authority_runtime.cli mcp serve --mock
```

## Source

[github.com/tronmongoose/agent.carryall_plugin](https://github.com/tronmongoose/agent.carryall_plugin)
