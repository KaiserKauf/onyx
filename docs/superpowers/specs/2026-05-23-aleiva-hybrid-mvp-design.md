# Aleiva Hybrid MVP Design (Onyx-based)

## Context

This design defines a first implementation slice for an "AleivaOS"-style system on top of the existing Onyx repository.

Priorities agreed in this chat:

- Primary: `project/code autopilot` and `second brain`
- Secondary (later phases): `trading architecture` and `voice-first control`
- Deployment model: `hybrid` (local-first, optional cloud extensions)
- Autonomy target: `full local autonomy` with strict guardrails
- Success target: `balanced` outcomes (speed + quality + knowledge gain)

## Problem To Solve

Build an autonomous local system that can:

1. Work on code tasks end-to-end (plan, implement, verify, improve)
2. Persist and reuse knowledge from prior runs
3. Improve future runs based on measured outcomes
4. Stay safe, auditable, and stable under full autonomy

## Scope

### In Scope (Phase 1)

- Auto-build agent core with role-based flow
- Second-brain core with persistent learning storage
- Lightweight graph relations for retrieval quality
- Balanced KPI measurement and adaptive policy switching
- Local-first execution with hard guardrails

### Out of Scope (Phase 1)

- Full production trading execution engine
- System-wide OS-level voice control
- Dedicated external graph database rollout (Neo4j/TigerGraph/etc.)
- Fully automatic self-modifying model/prompt infrastructure without controls

## Architecture Overview

The MVP introduces a new bounded module:

- `backend/onyx/aleiva_core/`

With six subcomponents:

1. `orchestrator/`
   - Run lifecycle: `plan -> execute -> verify -> learn`
   - Task prioritization and strategy routing
2. `agents/`
   - `planner_agent`, `coder_agent`, `verifier_agent`, `critic_agent`
3. `second_brain/`
   - Persistent run artifacts, decisions, fixes, failure patterns
4. `memory_graph/`
   - Lightweight relation layer: Task, File, Decision, TestResult, Commit
5. `runtime/`
   - Command execution with policy, budgets, retry controls
6. `eval_loop/`
   - Balanced KPI collection and policy adaptation

## Data Flow

1. Goal intake (manual trigger or schedule)
2. Planner creates a task graph and risk tags
3. Coder executes changes in isolated git context
4. Verifier runs staged checks (`quick -> targeted -> full`)
5. Critic evaluates outcomes and recommends recovery or completion
6. Run artifacts and learnings are persisted in second brain + relation graph
7. Eval loop updates KPIs and may tune runtime policy for the next run

## Guardrails For Full Autonomy

### Git Safety

- No destructive commands (`reset --hard`, force push, checkout discard)
- Work on isolated branches/worktrees for autonomous runs
- Explicit block for direct mutation of protected branches

### Runtime Safety

- Allowlist for executable command classes in Phase 1
- Blocklist for dangerous shell patterns and broad filesystem operations
- Timeout and retry budgets at run and step levels

### Data Safety

- No secret exfiltration behavior
- Restricted handling for `.env`, credential, and key files
- Audit logs for every command and file mutation intent

### Quality Safety

- Promotion gate requires:
  - tests passing
  - no new critical lint/type failures
  - risk score below configured threshold

## Balanced Optimization Model (Speed + Stability)

Policy modes:

- `balanced` (default)
- `fast_lane` (higher throughput, lighter checks where safe)
- `stability_lane` (stricter checks, lower risk tolerance)

Automatic adaptation:

- If speed drops with stable quality -> raise throughput weights
- If quality regresses -> enforce stricter validation path
- If knowledge reuse declines -> increase retrieval weighting and memory cleanup

## Second Brain Design

### Stored Entities

- Run metadata (goal, strategy, timestamps)
- Decision records (why a path was chosen)
- Change summaries (what changed and intent)
- Error records (class, root cause, fix attempts, outcome)
- Verification records (checks run, pass/fail)
- Reuse records (which memory artifact improved result)

### Relation Types (Light Graph)

- `depends_on`
- `changed_in`
- `fixed_by`
- `invalidated_by`
- `related_to`

### Quality Controls

- Confidence scoring per memory item
- Expiration/decay policy
- Duplicate merge
- Contradiction flagging (do not blindly apply conflicting memory)

## Milestone Plan (14 Days)

### Days 1-3: Orchestrator Skeleton

- Create module structure under `backend/onyx/aleiva_core/`
- Add run lifecycle and role dispatch contracts
- Add core event schema for run traces

### Days 4-6: Runtime + Guardrails

- Implement safe command runner and policy engine
- Implement budgets (time, retries, run limits)
- Add failure classification and recovery playbooks

### Days 7-10: Second Brain MVP

- Implement persistence adapters and retrieval API
- Implement lightweight relation mapping
- Wire planner/critic to use second-brain retrieval context

### Days 11-14: Eval + Autopilot

- Add KPI collection for speed/quality/knowledge
- Add policy auto-switching (`balanced`, `fast_lane`, `stability_lane`)
- Validate with 2-3 real autonomous runs on project tasks

## Acceptance Criteria

### Functional

- At least 3 successful end-to-end autonomous runs
- Automatic recovery loop triggers and converges for common failures
- Second brain updated and reused in subsequent runs

### Quality

- No new critical regressions in successful runs
- Changes are auditable and reasoned
- Scope and safety policies respected

### Balanced KPI

- Speed trend improves across sample runs
- Quality stays stable or improves
- Knowledge reuse has measurable positive impact

## Hardening (Weeks 3-4)

- ROI-based task prioritization (`impact * confidence / effort`)
- Better flaky-test handling and rerun heuristics
- Domain-specific memory ranking
- Drift detection and automatic degradation to `stability_lane`
- Improved critic model for risk classification

## Later Extensions

### Trading Architecture

- Add domain-specific agent roles for research, strategy checks, and risk review
- Add strict non-execution mode first (analysis and recommendation only)
- Add execution connectors only after governance and audit maturity

### Voice-First Control

- Start with command intents for run control (`start`, `pause`, `status`, `report`)
- Keep voice as control channel; do not bypass guardrails
- Expand to conversational orchestration after control reliability is proven

## Risks And Mitigations

- Risk: over-automation causes unstable edits
  - Mitigation: strict guardrails + policy adaptation + risk tiers
- Risk: memory pollution and contradictions
  - Mitigation: confidence scoring, decay, contradiction tagging
- Risk: runtime cost explosion from autonomous loops
  - Mitigation: hard budgets, retry caps, and lane switching

## Design Continuity And Experience Rules

### AleivaOS Matrix Design Canon (Always-On)

The UI and interaction style must remain consistent over time:

- Visual identity: modern, high-contrast, matrix-inspired UI language
- Interaction identity: responsive, interactive, state-aware interfaces
- Continuity rule: all new modules must inherit the same design tokens and motion principles
- Drift prevention: no feature may introduce a conflicting visual system

### Interactive Guidance For New Users

Every major workflow must include guided onboarding:

- First-run guided flow with progressive disclosure
- Contextual hints per screen and per action
- "What happens next" previews before autonomous operations
- Recovery guidance when errors occur (clear next action)

### UX Governance Rules

- Define and version a central design-token contract (color, spacing, typography, motion)
- Enforce reusable component primitives for all new surfaces
- Require accessibility and responsiveness checks for each new interactive flow
- Block release of UI changes that violate design canon or onboarding requirements

## Non-Forgetting And Continuous Improvement Protocol

### Required Persistence Artifacts (Per Run)

Each autonomous run must persist all of the following:

- Goal and success criteria snapshot
- Planner decisions and rationale
- Code and config changes summary
- Verification outcomes and failure classifications
- Recovery attempts and final disposition
- Reuse notes (which prior knowledge influenced outcome)

### Completeness Gate (No Missing Sections)

Before a run is marked complete:

- Validate required artifacts exist and are non-empty
- Validate at least one post-run learning record is stored
- Validate unresolved critical issues are either fixed or explicitly deferred
- Reject completion if mandatory run sections are missing

### Memory Hygiene And Recall Rules

- Deduplicate repeated learnings with confidence updates
- Tag contradictory learnings and prevent blind auto-application
- Apply freshness/decay to low-confidence stale memory
- Require retrieval context for planner and critic before execution decisions

### Improvement Without Omission

- Every iteration must produce:
  - one measurable improvement hypothesis
  - one safety check outcome
  - one retained learning entry
- If any of these are missing, the iteration is incomplete

## Open Decisions (To Confirm During Planning)

1. Initial persistence backend details for second brain entities
2. Exact risk-tier classifier rules and thresholds
3. Minimum required validation matrix per task type
4. First three real tasks used for MVP acceptance runs

## V2 Extensions (Prioritized)

### Quick Wins (Week 1 after MVP)

- Policy-as-code for runtime guardrails
  - Move allowlist/blocklist and safety thresholds into versioned config
  - Benefit: faster tuning and better auditability
- Dry-run simulation mode
  - Agent produces planned commands and expected diff summary without applying changes
  - Benefit: safer rollout for high-autonomy workflows
- Run explainability report
  - Auto-generate a concise run report (goal, decisions, changes, checks, outcome)
  - Benefit: trust and easier team handoff

### Mid-Term (Weeks 2-4)

- Task portfolio manager
  - Prioritize backlog by `impact * confidence / effort` with risk weighting
  - Benefit: better throughput on high-value work
- Knowledge hygiene pipeline
  - Scheduled deduplication, contradiction tagging, and stale-memory decay
  - Benefit: sustained second-brain relevance over time
- Prompt/skill A/B versioning
  - Compare planner/coder/critic strategy variants against balanced KPIs
  - Benefit: measurable improvement instead of subjective tuning

### Advanced (Month 2+)

- Risk-tier execution sandboxes
  - Separate safe/normal/experimental lanes with different limits and policies
  - Benefit: higher experimentation speed without destabilizing core workflows
- Regression radar
  - Detect recurring failure signatures across modules and preemptively adjust policy
  - Benefit: lower repeated-failure loops and faster convergence
- Domain expansion packs
  - Add specialized capability packs for trading analysis and voice-first orchestration
  - Benefit: clean growth path without overloading the MVP core

### Prioritization Rule

Use this rule when selecting extension work:

1. Must improve at least one balanced KPI (`speed`, `quality`, or `knowledge_reuse`)
2. Must not reduce safety baseline (guardrails and audit requirements stay intact)
3. Prefer low-complexity, high-leverage upgrades before new domain features

## Implementation Status

- [x] Core run artifacts and completeness gate
- [x] Guardrail policy and safe runtime wrapper
- [x] Second-brain persistence and relation helpers
- [x] Orchestrator and balanced lane switching
- [x] API run trigger endpoints and main router wiring
- [x] V2 quick win: policy-as-code defaults from versioned config
- [x] V2 quick win: dry-run explainability response fields

