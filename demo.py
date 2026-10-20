#!/usr/bin/env python3
"""
Carryall Policy Enforcement — Live Demo

Shows the core workflow:
  1. Generate agent key pair (one-time setup)
  2. Compile policy: intent → minimal-scope signed envelope (PDP, no LLM)
  3. Access check: finance-agent ALLOWED, startup-agent DENIED
  4. Document read with valid envelope

Run: python3 demo.py
No external services required.
"""

import sys
import time
from authority_runtime import (
    generate_key_pair,
    create_simple_envelope,
    PolicyDecisionPoint,
    BUILTIN_SCOPE_RULES,
    MemoryBackend,
    IntentAttributes,
)

# ── ANSI colours ──────────────────────────────────────────────────────────────
G = "\033[92m"; R = "\033[91m"; B = "\033[94m"
DIM = "\033[2m"; BOLD = "\033[1m"; RESET = "\033[0m"

DEMO_PAUSE = 1.5  # seconds between steps for recording

def pause():
    sys.stdout.flush()
    time.sleep(DEMO_PAUSE)

def banner(text):
    print(f"\n{BOLD}{B}{'─' * 60}{RESET}")
    print(f"{BOLD}{B}  {text}{RESET}")
    print(f"{BOLD}{B}{'─' * 60}{RESET}\n")
    sys.stdout.flush()

def ok(msg):    print(f"  {G}✔{RESET}  {msg}"); sys.stdout.flush()
def deny(msg):  print(f"  {R}✘{RESET}  {msg}"); sys.stdout.flush()
def info(msg):  print(f"     {DIM}{msg}{RESET}"); sys.stdout.flush()

# ── 1. Setup ──────────────────────────────────────────────────────────────────
banner("STEP 1 — Agent Key Generation")

finance_priv, finance_pub = generate_key_pair()
startup_priv, startup_pub = generate_key_pair()

ok(f"finance-agent  pub={finance_pub[:24]}…")
ok(f"startup-agent  pub={startup_pub[:24]}…")
info("Ed25519 key pairs — envelopes are cryptographically bound to agent identity")
pause()

# ── 2. Policy compilation (PDP, deterministic) ────────────────────────────────
banner("STEP 2 — Policy Compilation (PolicyDecisionPoint)")

pdp = PolicyDecisionPoint(rules=BUILTIN_SCOPE_RULES)

intent = IntentAttributes(
    domains=["finance"],
    operations=["read"],
    purpose="read Q1 budget summary for cost analysis",
    cross_domain=False,
    sensitivity_hint="confidential",
    extraction_confidence=0.97,
)

available_scopes = [
    "vault:finance:read",
    "vault:finance:write",
    "vault:startup:read",
    "audit:read",
]

decision = pdp.decide(intent, available_scopes=available_scopes)

ok(f"Intent:         \"{intent.purpose}\"")
ok(f"Scopes granted: {decision.granted_scopes}")
ok(f"Scopes denied:  {[s for s in available_scopes if s not in decision.granted_scopes]}")
ok(f"Rules fired:    {decision.rule_ids_applied}")
info("Deterministic: same intent → same scopes, every time. No LLM in the loop.")
pause()

# ── 3. Create signed envelope ─────────────────────────────────────────────────
banner("STEP 3 — Signed AuthorityEnvelope")

envelope = create_simple_envelope(
    agent_id="finance-agent",
    scopes=decision.granted_scopes,
    private_key=finance_priv,
    skill_name="finance-read",
    resources=["slos://vaults/finance/*"],
    ttl_seconds=300,
)

ok(f"Envelope ID:  {envelope.envelope_id}")
ok(f"Agent:        {envelope.agent_id}")
ok(f"Scopes:       {envelope.authority.scopes}")
ok(f"Signature:    {envelope.signature[:40]}…")
ok(f"Expires:      {envelope.expires_at}")
info("Tampering with scopes or agent_id invalidates the Ed25519 signature.")
pause()

# ── 4. Access enforcement ─────────────────────────────────────────────────────
banner("STEP 4 — Access Enforcement (MemoryBackend)")

backend = MemoryBackend(initial_data={
    "finance": {
        "q1-budget-2026": {
            "content": "# Q1 2026 Budget\n\nTotal: $2.4M\n- Engineering: $1.1M\n- Sales: $800k\n- Marketing: $500k",
            "title": "Q1 2026 Budget",
            "sensitivity": "confidential",
            "allowed_agents": ["finance-agent", "executive-agent"],
            "denied_agents": ["startup-agent"],
        }
    }
})

uri = "slos://vaults/finance/q1-budget-2026"

# finance-agent with vault:finance:read scope — ALLOWED
result = backend.check_access(envelope, "read", uri)
if result.decision.value == "allow":
    ok(f"finance-agent  → {G}ALLOW{RESET}  {uri}")
    info(f"reason: {result.reason}")
else:
    deny(f"finance-agent  → DENY  (unexpected)")

# startup-agent with wrong scope — DENIED
startup_envelope = create_simple_envelope(
    agent_id="startup-agent",
    scopes=["vault:startup:read"],
    private_key=startup_priv,
    skill_name="startup-read",
    ttl_seconds=300,
)
result2 = backend.check_access(startup_envelope, "read", uri)
if result2.decision.value == "deny":
    deny(f"startup-agent  → {R}DENY{RESET}   {uri}")
    info(f"reason: {result2.reason}")
else:
    ok(f"startup-agent  → ALLOW (unexpected)")
pause()

# ── 5. Document read ──────────────────────────────────────────────────────────
banner("STEP 5 — Document Read")

doc = backend.read_document("q1-budget-2026", "Q1 cost analysis", envelope.agent_id)
ok(f"Title:   {doc['title']}")
ok(f"Vault:   {doc['vault']}")
ok(f"Purpose: {doc['purpose']}")
print()
for line in doc["content"].strip().split("\n"):
    print(f"  {DIM}{line}{RESET}")

# ── Done ──────────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{G}  Done.{RESET}  Install the plugin:\n")
print(f"  {DIM}claude plugin marketplace add tronmongoose/agent.carryall_plugin")
print(f"  claude plugin install carryall-policy-enforcement@carryall{RESET}\n")
