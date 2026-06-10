# Skill: build-with-tests

_Enforce test-driven development discipline for every code change._

## Purpose

Ensure every code change is accompanied by tests. No code without tests.

## Rules

1. Write tests BEFORE or ALONGSIDE implementation, never after
2. Every new state in engine.py gets a test
3. Every new response key gets a test
4. Every new DB operation gets a test
5. Existing tests must still pass after changes
6. Target: >80% code coverage on new code

## Test Structure

```
tests/
  test_engine_<feature>.py    — engine state machine tests
  test_responses_new.py       — new response key tests  
  test_<utility>_new.py       — utility function tests
```

## Running Tests

```bash
python -m pytest tests/ -v
```

## Pre-commit Gate

Tests MUST pass before any commit is allowed.
