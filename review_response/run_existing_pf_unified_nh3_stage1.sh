#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

OUT="${1:?usage: $0 OUTPUT_DIR}"
CACHE_ROOT="${2:-artifacts/server_time_scale_fit_diagnosis_20260920_021411_80219a6/runtime/cache}"
PYTHON="${PYTHON:-venv/bin/python}"
mkdir -p "$OUT/raw" "$OUT/logs"

if [[ -n "${CUDA_VISIBLE_DEVICES:-}" ]]; then
  echo "Refusing to override inherited CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES}" >&2
  exit 2
fi

conditions=(
  active_equilibrium
  active_stretch150
  full_equilibrium
  full_stretch150
)
formulae=(
  yoshida4
  paper_new4
  m5_best
  current_m3
  two_term_center
  joint_refine_r0_s0046
  yoshida6_m3
  morales_y8m10b
)

for condition in "${conditions[@]}"; do
  test -s "$CACHE_ROOT/${condition}.pkl"
done

cat > "$OUT/manifest.json" <<EOF
{
  "status": "stage1_running",
  "code_commit": "$(git rev-parse HEAD)",
  "branch": "$(git branch --show-current)",
  "conditions": 4,
  "formulae": 8,
  "physical_gpu_ids": [0,1,2,3,4,5,6,7],
  "other_processes_stopped": false,
  "fit_grid": "geomspace(0.02,1.8,34)",
  "fit_noise_floor_hartree": 5e-13
}
EOF

run_job() {
  local condition="$1"
  local formula="$2"
  local gpu="$3"
  local output="$OUT/raw/${condition}__${formula}.json"
  local log="$OUT/logs/${condition}__${formula}__gpu${gpu}.log"
  if [[ -s "$output" ]] && "$PYTHON" -c \
    'import json,sys; raise SystemExit(0 if json.load(open(sys.argv[1]))["status"] in ("complete","short_time_fit_failed") else 1)' \
    "$output"; then
    echo "skip complete $condition $formula" >> "$OUT/logs/master.log"
    return
  fi
  echo "$(date --iso-8601=seconds) start gpu=$gpu $condition $formula" >> "$OUT/logs/master.log"
  CUDA_VISIBLE_DEVICES="$gpu" \
  PYTHONPATH="src:review_response:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages" \
  OPENBLAS_NUM_THREADS=8 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 \
  "$PYTHON" review_response/run_full_electron_nh3_higher_term_diagnosis.py formula \
    --system-cache "$CACHE_ROOT/${condition}.pkl" \
    --formula "$formula" \
    --backend gpu \
    --gpu-id "$gpu" \
    --output "$output" > "$log" 2>&1
  echo "$(date --iso-8601=seconds) finish gpu=$gpu $condition $formula" >> "$OUT/logs/master.log"
}

queue_gpu() {
  local gpu="$1"
  local index=0
  for condition in "${conditions[@]}"; do
    for formula in "${formulae[@]}"; do
      if (( index % 8 == gpu )); then
        run_job "$condition" "$formula" "$gpu"
      fi
      index=$((index + 1))
    done
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
  touch "$OUT/STAGE1_FAILED"
  exit 3
fi
touch "$OUT/STAGE1_COMPLETE"
