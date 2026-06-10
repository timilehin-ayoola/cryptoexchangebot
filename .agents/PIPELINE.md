# PIPELINE.md — Dev Squad Software Factory

_Definition of the 7-agent pipeline for this project._

---

## Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        FEATURE REQUEST                                  │
│                    (from Timilehin or Apex)                              │
└─────────────────┬───────────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STAGE 1: RESEARCH                                                      │
│  Agent: codebase-researcher (Scribe)                                    │
│  Tool: Read-only (files, grep, glob)                                    │
│  Output: Architecture summary, relevant files, risks                    │
└─────────────────┬───────────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STAGE 2: STORY                                                         │
│  Agent: story-writer (Narrative)                                        │
│  Tool: Read-only                                                        │
│  Output: User story, acceptance criteria, edge cases                    │
├─────────────────────────────────────────────────────────────────────────┤
│  ★ GATE 1: HUMAN APPROVAL REQUIRED ★                                    │
│  Options: APPROVE / CHANGES REQUESTED / REJECTED                        │
└─────────────────┬───────────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STAGE 3: SPEC                                                          │
│  Agent: spec-writer (Architect)                                         │
│  Tool: Read-only                                                        │
│  Output: Technical implementation spec                                  │
├─────────────────────────────────────────────────────────────────────────┤
│  ★ GATE 2: HUMAN APPROVAL REQUIRED ★                                    │
│  Options: APPROVE / CHANGES REQUESTED / REJECTED                        │
└─────────────────┬───────────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STAGE 4: BUILD (Sequential)                                            │
│                                                                         │
│  4a. backend-builder (Kael)                                             │
│      Tools: Read, Edit, Write, Bash                                     │
│      Output: Modified engine.py, database.py, responses.py, etc.        │
│                                                                         │
│  4b. test-verifier (Guard)                                              │
│      Tools: Read, Write, Bash                                           │
│      Output: Test files + test results                                  │
│      Loop: If tests fail → back to 4a (max 3 iterations)                │
└─────────────────┬───────────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STAGE 5: VALIDATE                                                      │
│  Agent: implementation-validator (Judge)                                │
│  Tool: Read-only                                                        │
│  Output: Validation report (Critical/Important/Minor)                   │
│      Loop: If critical → back to 4a (max 2 iterations)                  │
└─────────────────┬───────────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STAGE 6: REVIEW                                                        │
│  Agent: pr-reviewer                                                     │
│  Tool: Read-only                                                        │
│  Output: Final PR review report                                         │
├─────────────────────────────────────────────────────────────────────────┤
│  ★ GATE 3: HUMAN FINAL REVIEW ★                                        │
│  Options: MERGE / REQUEST CHANGES / REJECT                              │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Agent Roles Summary

| Stage | Agent | Role | Tools | Model Tier |
|-------|-------|------|-------|------------|
| 1 | codebase-researcher | Map relevant code | Read, Grep, Glob | Light |
| 2 | story-writer | Write user story | Read | Light |
| 3 | spec-writer | Write technical spec | Read | Medium |
| 4a | backend-builder | Implement code | Read, Edit, Write, Bash | Heavy |
| 4b | test-verifier | Write and run tests | Read, Write, Bash | Light |
| 5 | implementation-validator | Review implementation | Read | Medium |
| 6 | pr-reviewer | Final PR review | Read | Medium |

---

## Parallel vs Sequential

**Can run in parallel:**
- codebase-researcher + story-writer (if story doesn't need research first)
- codebase-researcher + spec-writer (if spec doesn't need story first)

**Must run sequentially:**
- story-writer → spec-writer (spec depends on story)
- backend-builder → test-verifier (tests need code)
- test-verifier → implementation-validator (validation needs test results)

---

## Artifact Flow

```
research/   → (researcher output, reusable)
wiki/features/
  <feature>-story.md
  <feature>-spec.md
  <feature>-test-results.md
  <feature>-validation.md
tests/      → (new test files)
```

---

## Loop-back Rules

1. **Test failure** → backend-builder fixes, re-runs tests (max 3 loops)
2. **Critical validation finding** → backend-builder fixes (max 2 loops)
3. **Human changes requested** → go back to the relevant stage
4. **Human rejected** → feature cancelled, document why

---

## Time Budget Per Stage

| Stage | Expected Duration |
|-------|-------------------|
| Research | 1-2 min |
| Story | 1-2 min |
| Spec | 2-3 min |
| Build | 3-10 min |
| Test | 2-5 min |
| Validate | 1-3 min |
| Review | 1-2 min |
| **Total (no loops)** | **11-27 min** |

---

## Enforcement

- Agents MUST follow their AGENTS.md definitions
- Agents MUST NOT skip stages
- Human gates are HARD STOPS — no auto-proceed
- All artifacts are saved to wiki/ for audit trail
