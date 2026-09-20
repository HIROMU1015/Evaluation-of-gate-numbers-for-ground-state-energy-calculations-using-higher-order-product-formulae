#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

OUT="${1:?usage: $0 OUTPUT_DIR}"
CACHE_ROOT="${2:-artifacts/server_time_scale_fit_diagnosis_20260920_021411_80219a6/runtime/cache}"
PYTHON="${PYTHON:-venv/bin/python}"
SCRIPT="review_response/run_existing_pf_unified_nh3_stage2.py"
PLAN="$OUT/stage2_plan.json"
FINE="$OUT/fine/raw"
LOGS="$OUT/fine/logs"
mkdir -p "$FINE" "$LOGS" "$OUT/aggregate"

if [[ -n "${CUDA_VISIBLE_DEVICES:-}" ]]; then
  echo "Refusing to override inherited CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES}" >&2
  exit 2
fi

if [[ ! -s "$PLAN" ]]; then
  PYTHONPATH="src:review_response:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages" \
    "$PYTHON" "$SCRIPT" plan --raw-dir "$OUT/raw" --output "$PLAN"
fi

mapfile -t TASKS < <(
  "$PYTHON" -c 'import json,sys; p=json.load(open(sys.argv[1])); [print(t["task_id"]) for t in p["tasks"]]' "$PLAN"
)

run_task() {
  local task="$1"
  local gpu="$2"
  local condition="${task%%__*}"
  local output="$FINE/$task.json"
  local log="$LOGS/${task}__gpu${gpu}.log"
  if [[ -s "$output" ]] && "$PYTHON" -c \
    'import json,sys; raise SystemExit(0 if json.load(open(sys.argv[1])).get("status")=="complete" else 1)' \
    "$output"; then
    echo "skip complete $task" >> "$LOGS/master.log"
    return
  fi
  echo "$(date --iso-8601=seconds) start gpu=$gpu $task" >> "$LOGS/master.log"
  CUDA_VISIBLE_DEVICES="$gpu" \
  PYTHONPATH="src:review_response:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages" \
  OPENBLAS_NUM_THREADS=8 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 \
    "$PYTHON" "$SCRIPT" fine-task \
      --plan "$PLAN" \
      --task-id "$task" \
      --system-cache "$CACHE_ROOT/$condition.pkl" \
      --backend gpu \
      --gpu-id "$gpu" \
      --output "$output" >"$log" 2>&1
  echo "$(date --iso-8601=seconds) finish gpu=$gpu $task" >> "$LOGS/master.log"
}

queue_gpu() {
  local gpu="$1"
  local index=0
  local task
  for task in "${TASKS[@]}"; do
    if (( index % 8 == gpu )); then
      run_task "$task" "$gpu"
    fi
    index=$((index + 1))
  done
}

pids=()
for gpu in 0 1 2 3 4 5 6 7; do
  queue_gpu "$gpu" &
  pids+=("$!")
done
failed=0
for pid in "${pids[@]}"; do
  wait "$pid" || failed=1
done
if (( failed != 0 )); then
  touch "$OUT/STAGE2_FINE_FAILED"
  exit 3
fi
touch "$OUT/STAGE2_FINE_COMPLETE"

PYTHONPATH="src:review_response:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages" \
  "$PYTHON" "$SCRIPT" aggregate \
    --raw-dir "$OUT/raw" \
    --plan "$PLAN" \
    --fine-dir "$FINE" \
    --output-dir "$OUT/aggregate" >"$LOGS/aggregate.log" 2>&1
touch "$OUT/COMPLETE"
