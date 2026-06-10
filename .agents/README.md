# .agents/ — Software Factory Configuration

This directory contains the agent orchestration system for the Nigerian P2P Crypto Exchange Bot.

## Structure

```
.agents/
  AGENTS.md                        ← Project context (read by every agent)
  PIPELINE.md                      ← Pipeline definition and flow
  codebase-researcher/AGENT.md     ← Stage 1: Read-only code exploration
  story-writer/AGENT.md            ← Stage 2: User story creation
  spec-writer/AGENT.md             ← Stage 3: Technical spec writing
  backend-builder/AGENT.md         ← Stage 4a: Code implementation
  test-verifier/AGENT.md           ← Stage 4b: Test writing and execution
  implementation-validator/AGENT.md ← Stage 5: Validation review
  pr-reviewer/AGENT.md             ← Stage 6: Final PR review
  skills/
    feature-factory/SKILL.md       ← Orchestrator skill (runs the chain)
    build-with-tests/SKILL.md      ← TDD enforcement skill
  hooks/
    pre-commit.sh                  ← Pre-commit quality gate
    subagent-stop.sh               ← Agent completion logger
```

## How It Works

1. **Apex** (orchestrator) receives a feature request
2. Runs the **feature-factory** skill
3. Skill delegates to each agent in sequence
4. **Human approval gates** after story, spec, and final validation
5. Loop-back on test failures or critical findings
6. All artifacts saved to `wiki/`

## Pipeline

```
Research → Story → [GATE] → Spec → [GATE] → Build → Test → Validate → Review → [GATE] → Merge
```

See `PIPELINE.md` for full details.

## Key Rules

- **Read-only agents** (researcher, story-writer, spec-writer, validator, reviewer) can run in parallel
- **Write agents** (builder, test-verifier) run sequentially
- **3 human approval gates** — no auto-proceed
- **Loop-back** on failures (max 3 test loops, 2 validation loops)
- All artifacts saved to `wiki/features/` for audit trail
