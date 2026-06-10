#!/usr/bin/env bash
# SubagentStop hook — runs when an agent finishes a task
# Notifies and logs completion

AGENT_NAME="$1"
TASK_STATUS="$2"  # completed / failed / rejected

LOG_FILE="wiki/logs/agent-$(date +%Y-%m-%d).log"
mkdir -p wiki/logs

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Agent: $AGENT_NAME | Status: $TASK_STATUS" >> "$LOG_FILE"

# If implementation-validator or test-verifier failed, alert
if [ "$AGENT_NAME" = "implementation-validator" ] && [ "$TASK_STATUS" = "failed" ]; then
    echo "⚠️  VALIDATION FAILED — pipeline needs attention."
fi

if [ "$AGENT_NAME" = "test-verifier" ] && [ "$TASK_STATUS" = "failed" ]; then
    echo "⚠️  TESTS FAILED — pipeline needs attention."
fi
