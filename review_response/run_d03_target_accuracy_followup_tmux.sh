#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "usage: $0 OUTPUT_DIR [GPU_ID]" >&2
  exit 64
fi

PROJECT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
OUTPUT_DIR=$1
GPU_ID=${2:-0}
PYTHON_BIN=/home/AbeHiromu/venvs/trotter-common/bin/python

cd "$PROJECT_ROOT"
mkdir -p "$OUTPUT_DIR"
export PYTHONPATH="src:review_response:."

"$PYTHON_BIN" -m pytest -q review_tests/test_d03_target_accuracy_followup.py \
  2>&1 | tee "$OUTPUT_DIR/precompute_tests.log"

"$PYTHON_BIN" review_response/run_d03_target_accuracy_followup.py run-all \
  --output "$OUTPUT_DIR" --gpu-id "$GPU_ID" \
  2>&1 | tee "$OUTPUT_DIR/scientific_run.log"

"$PYTHON_BIN" -m pytest -q review_tests/test_d03_target_accuracy_followup.py \
  2>&1 | tee "$OUTPUT_DIR/focused_tests.log"
"$PYTHON_BIN" -m pytest -q review_tests \
  2>&1 | tee "$OUTPUT_DIR/review_tests.log"

"$PYTHON_BIN" review_response/run_d03_target_accuracy_followup.py finalize \
  --output "$OUTPUT_DIR" \
  --test-log "$OUTPUT_DIR/focused_tests.log" \
  --test-log "$OUTPUT_DIR/review_tests.log"

git add "$OUTPUT_DIR"
git commit -m "Record D03 target accuracy direct validation"

BRANCH=$(git branch --show-current)
PUSH_LOG=/tmp/d03_target_accuracy_push_${$}.log
if GIT_TERMINAL_PROMPT=0 git push -u origin "$BRANCH" >"$PUSH_LOG" 2>&1; then
  echo "push_status=passed"
else
  PUSH_STATUS=$?
  echo "push_status=failed exit_code=$PUSH_STATUS log=$PUSH_LOG"
  sed -n '1,120p' "$PUSH_LOG"
fi
echo "D03_RUN_COMPLETE output=$OUTPUT_DIR commit=$(git rev-parse HEAD)"
