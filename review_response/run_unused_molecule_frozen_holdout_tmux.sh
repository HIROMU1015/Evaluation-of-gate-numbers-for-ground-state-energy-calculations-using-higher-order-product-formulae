#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

OUT="${1:?usage: $0 OUTPUT_DIR GPU_IDS}"
GPU_IDS="${2:?comma-separated physical GPU IDs are required}"
PYTHON="${PYTHON:-/home/AbeHiromu/venvs/trotter-common/bin/python}"
SCRIPT="review_response/run_unused_molecule_frozen_holdout.py"
PYTHONPATH_VALUE="src:review_response:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages"

if [[ -n "${CUDA_VISIBLE_DEVICES:-}" ]]; then
  echo "Refusing to override inherited CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES}" >&2
  exit 2
fi

IFS=',' read -r -a GPUS <<< "$GPU_IDS"
if (( ${#GPUS[@]} == 0 )); then
  echo "No GPUs supplied" >&2
  exit 2
fi

conditions=(
  N2_active_eq_sto3g
  N2_active_stretch150_sto3g
  CO_active_eq_sto3g
  CO_active_stretch150_sto3g
  HF_full_eq_sto3g
  HF_full_stretch150_sto3g
)
formulae=(yoshida4 current_m3 two_term_center m5_best yoshida6_m3)

mkdir -p "$OUT"/{logs,cache,raw,fine/raw,fine/logs,aggregate}
exec > >(tee -a "$OUT/logs/master.log") 2>&1
echo "$(date --iso-8601=seconds) start branch=$(git branch --show-current) commit=$(git rev-parse HEAD) gpus=$GPU_IDS"

PYTHONPATH="$PYTHONPATH_VALUE" "$PYTHON" "$SCRIPT" manifest \
  --independence-search-log "$OUT/independence_search.log" \
  --output "$OUT/manifest.json"

prepare_one() {
  local condition="$1"
  local cache="$OUT/cache/$condition.pkl"
  if [[ -s "$cache" ]] && [[ -s "${cache%.pkl}.metadata.json" ]]; then
    echo "skip prepared $condition"
    return
  fi
  PYTHONPATH="$PYTHONPATH_VALUE" OPENBLAS_NUM_THREADS=8 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 \
    "$PYTHON" "$SCRIPT" prepare --condition "$condition" --component-processes 8 \
      --output "$cache" > "$OUT/logs/prepare_${condition}.log" 2>&1
}

for condition in "${conditions[@]}"; do
  prepare_one "$condition"
done

PYTHONPATH="$PYTHONPATH_VALUE" "$PYTHON" "$SCRIPT" validate-prepared \
  --metadata-dir "$OUT/cache" --output "$OUT/preflight_hamiltonians.json"
touch "$OUT/PREFLIGHT_COMPLETE"

pilot_gpu="${GPUS[0]}"
CUDA_VISIBLE_DEVICES="$pilot_gpu" PYTHONPATH="$PYTHONPATH_VALUE" \
OPENBLAS_NUM_THREADS=8 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 \
  "$PYTHON" "$SCRIPT" pilot \
    --system-cache "$OUT/cache/CO_active_eq_sto3g.pkl" \
    --backend gpu --gpu-id "$pilot_gpu" --output "$OUT/pilot.json" \
    > "$OUT/logs/pilot_gpu${pilot_gpu}.log" 2>&1
touch "$OUT/PILOT_COMPLETE"

run_formula() {
  local condition="$1"
  local formula="$2"
  local gpu="$3"
  local output="$OUT/raw/${condition}__${formula}.json"
  local log="$OUT/logs/${condition}__${formula}__gpu${gpu}.log"
  if [[ -s "$output" ]] && "$PYTHON" -c \
    'import json,sys; raise SystemExit(0 if json.load(open(sys.argv[1])).get("status") in ("complete","short_time_fit_failed") else 1)' \
    "$output"; then
    echo "skip complete $condition $formula"
    return
  fi
  echo "$(date --iso-8601=seconds) stage1 start gpu=$gpu $condition $formula"
  CUDA_VISIBLE_DEVICES="$gpu" PYTHONPATH="$PYTHONPATH_VALUE" \
  OPENBLAS_NUM_THREADS=8 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 \
    "$PYTHON" "$SCRIPT" formula --condition "$condition" \
      --system-cache "$OUT/cache/$condition.pkl" --formula "$formula" \
      --backend gpu --gpu-id "$gpu" --output "$output" > "$log" 2>&1
  echo "$(date --iso-8601=seconds) stage1 finish gpu=$gpu $condition $formula"
}

queue_formula_gpu() {
  local gpu="$1"
  local slot="$2"
  local index=0
  local condition formula
  for condition in "${conditions[@]}"; do
    for formula in "${formulae[@]}"; do
      if (( index % ${#GPUS[@]} == slot )); then
        run_formula "$condition" "$formula" "$gpu"
      fi
      index=$((index + 1))
    done
  done
}

pids=()
for slot in "${!GPUS[@]}"; do
  queue_formula_gpu "${GPUS[$slot]}" "$slot" &
  pids+=("$!")
done
failed=0
for pid in "${pids[@]}"; do wait "$pid" || failed=1; done
if (( failed )); then touch "$OUT/STAGE1_FAILED"; exit 3; fi
touch "$OUT/STAGE1_COMPLETE"

PYTHONPATH="$PYTHONPATH_VALUE" "$PYTHON" "$SCRIPT" plan \
  --raw-dir "$OUT/raw" --output "$OUT/stage2_plan.json"

mapfile -t tasks < <(
  "$PYTHON" -c 'import json,sys; [print(x["task_id"]) for x in json.load(open(sys.argv[1]))["tasks"]]' "$OUT/stage2_plan.json"
)

run_fine() {
  local task="$1"
  local gpu="$2"
  local condition="${task%%__*}"
  local output="$OUT/fine/raw/$task.json"
  if [[ -s "$output" ]] && "$PYTHON" -c \
    'import json,sys; raise SystemExit(0 if json.load(open(sys.argv[1])).get("status")=="complete" else 1)' \
    "$output"; then
    echo "skip fine $task"
    return
  fi
  echo "$(date --iso-8601=seconds) stage2 start gpu=$gpu $task"
  CUDA_VISIBLE_DEVICES="$gpu" PYTHONPATH="$PYTHONPATH_VALUE" \
  OPENBLAS_NUM_THREADS=8 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 \
    "$PYTHON" "$SCRIPT" fine --plan "$OUT/stage2_plan.json" --task-id "$task" \
      --system-cache "$OUT/cache/$condition.pkl" --backend gpu --gpu-id "$gpu" \
      --output "$output" > "$OUT/fine/logs/${task}__gpu${gpu}.log" 2>&1
  echo "$(date --iso-8601=seconds) stage2 finish gpu=$gpu $task"
}

queue_fine_gpu() {
  local gpu="$1"
  local slot="$2"
  local index=0
  local task
  for task in "${tasks[@]}"; do
    if (( index % ${#GPUS[@]} == slot )); then run_fine "$task" "$gpu"; fi
    index=$((index + 1))
  done
}

pids=()
for slot in "${!GPUS[@]}"; do
  queue_fine_gpu "${GPUS[$slot]}" "$slot" &
  pids+=("$!")
done
failed=0
for pid in "${pids[@]}"; do wait "$pid" || failed=1; done
if (( failed )); then touch "$OUT/STAGE2_FAILED"; exit 4; fi
touch "$OUT/STAGE2_COMPLETE"

PYTHONPATH="$PYTHONPATH_VALUE" "$PYTHON" "$SCRIPT" aggregate \
  --raw-dir "$OUT/raw" --plan "$OUT/stage2_plan.json" \
  --fine-dir "$OUT/fine/raw" --output-dir "$OUT/aggregate"
touch "$OUT/COMPLETE"
echo "$(date --iso-8601=seconds) complete"
