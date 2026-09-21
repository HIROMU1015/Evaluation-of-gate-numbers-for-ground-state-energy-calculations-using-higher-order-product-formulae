#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
PYTHON=/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/venv/bin/python
COMMON_SITE=/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages
RUNNER="$ROOT/review_response/run_h01_approximate_state_calibration.py"
ARTIFACT=${1:?usage: resume_h01_truth_after_duplicate_fix.sh ARTIFACT}
ARTIFACT=$(realpath "$ARTIFACT")
export PYTHONPATH="$ROOT/src:$ROOT/review_response:$COMMON_SITE"
export MPLBACKEND=Agg
export OPENBLAS_NUM_THREADS=4
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4
exec >> "$ARTIFACT/logs/recovery_duplicate_truth.log" 2>&1

echo "[$(date --iso-8601=seconds)] waiting for original H01 truth processes"
while pgrep -f "run_h01_approximate_state_calibration.py truth.*$ARTIFACT" >/dev/null; do
  sleep 20
done

echo "[$(date --iso-8601=seconds)] rerun from validated time-level checkpoints"
mapfile -t GPU_IDS < <(
  nvidia-smi --query-gpu=index,memory.free --format=csv,noheader,nounits     | awk -F, '$2+0 >= 4096 {gsub(/ /,"",$1); print $1}'
)
if (( ${#GPU_IDS[@]} == 0 )); then
  echo "No GPU with at least 4096 MiB free; no process was stopped."
  exit 2
fi
conditions=(
  N2_active_eq_sto3g N2_active_stretch150_sto3g
  CO_active_eq_sto3g CO_active_stretch150_sto3g
  HF_full_eq_sto3g HF_full_stretch150_sto3g
)
formulae=(current_m3 yoshida4)
tasks=()
for condition in "${conditions[@]}"; do
  for formula in "${formulae[@]}"; do tasks+=("${condition}__${formula}"); done
done
cursor=0
while (( cursor < ${#tasks[@]} )); do
  pids=()
  for slot in "${!GPU_IDS[@]}"; do
    (( cursor >= ${#tasks[@]} )) && break
    task=${tasks[$cursor]}
    condition=${task%__*}
    formula=${task##*__}
    gpu=${GPU_IDS[$slot]}
    echo "resume $task on physical GPU $gpu"
    CUDA_VISIBLE_DEVICES=$gpu "$PYTHON" "$RUNNER" truth       --project-root "$ROOT" --condition "$condition" --formula "$formula"       --cache "$ARTIFACT/cache/${condition}.pkl"       --echo "$ARTIFACT/echo/${task}.json"       --output "$ARTIFACT/truth/${task}.json"       --backend gpu --gpu-id "$gpu"       > "$ARTIFACT/logs/truth_${task}_retry1.log" 2>&1 &
    pids+=("$!")
    cursor=$((cursor + 1))
  done
  for pid in "${pids[@]}"; do wait "$pid"; done
done
"$PYTHON" -m pytest -q review_tests > "$ARTIFACT/tests/review_tests_retry1.log" 2>&1
"$PYTHON" "$RUNNER" aggregate --artifact-root "$ARTIFACT"
echo "[$(date --iso-8601=seconds)] H01 recovery COMPLETE"
