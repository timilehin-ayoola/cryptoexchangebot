# Skill: feature-factory

_Orchestrates the full 7-agent pipeline for a new feature._

## Purpose

Take a feature idea from the user and run the complete software factory chain:
research → story → spec → build → test → validate → review.

## When to Use

- User says "add feature X" or "implement Y"
- Any new functionality that touches engine.py, database.py, or responses.py

## Pipeline Steps

### Step 1: Research
**Agent:** codebase-researcher
**Input:** Feature idea
**Output:** Relevant files, architecture summary, risks
**Parallel:** Can run in parallel with other read-only agents

### Step 2: Story Writing
**Agent:** story-writer
**Input:** Feature idea + research findings
**Output:** User story with acceptance criteria and edge cases
**Approval Gate:** HUMAN MUST APPROVE before proceeding

### Step 3: Spec Writing
**Agent:** spec-writer
**Input:** Approved story + research findings
**Output:** Technical implementation spec
**Approval Gate:** HUMAN MUST APPROVE before proceeding

### Step 4: Backend Build
**Agent:** backend-builder
**Input:** Approved spec + approved story + research findings
**Output:** Modified source files
**Runs:** test suite after implementation

### Step 5: Test Verification
**Agent:** test-verifier
**Input:** Approved story + spec + modified files
**Output:** Test results report
**Loop:** If tests fail, send back to backend-builder with specific failures

### Step 6: Implementation Validation
**Agent:** implementation-validator
**Input:** Story + spec + test results + modified files
**Output:** Validation report (Critical/Important/Minor findings)
**Loop:** If critical findings, send back to backend-builder

### Step 7: PR Review
**Agent:** pr-reviewer
**Input:** All artifacts + modified files
**Output:** Final review report
**Outcome:** Ready for human merge

## Human Approval Points

1. **After Step 2 (Story):** User reviews and approves the story
   - Options: APPROVE / CHANGES REQUESTED / REJECTED
2. **After Step 3 (Spec):** User reviews and approves the spec
   - Options: APPROVE / CHANGES REQUESTED / REJECTED
3. **After Step 6-7 (Validation + Review):** User does final review
   - Options: MERGE / REQUEST CHANGES / REJECT

## Parallel Execution

Read-only agents (codebase-researcher, story-writer, spec-writer) can run in parallel
when they don't depend on each other's output.

Write agents (backend-builder, test-verifier) MUST run sequentially.

## Error Handling

- If any agent fails, stop the pipeline and report
- If tests fail, loop back to backend-builder (max 3 iterations)
- If validator finds critical issues, loop back to backend-builder (max 2 iterations)
- If human rejects at any gate, stop and incorporate feedback

## Output Artifacts

Every feature produces:
1. `wiki/features/<feature-name>-story.md`
2. `wiki/features/<feature-name>-spec.md`
3. `wiki/features/<feature-name>-test-results.md`
4. `wiki/features/<feature-name>-validation.md`
5. Modified source files
6. New test files
