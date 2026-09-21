#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
PYTHON=/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/venv/bin/python
COMMON_SITE=/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages
RUNNER="$ROOT/review_response/run_h01_approximate_state_calibration.py"
RUN_ID=${1:?usage: run_h01_approximate_state_calibration_tmux.sh RUN_ID}
GIT_SHORT=$(git -C "$ROOT" rev-parse --short HEAD)
ARTIFACT="$ROOT/artifacts/server_h01_approximate_state_calibration_${RUN_ID}_${GIT_SHORT}"

export PYTHONPATH="$ROOT/src:$ROOT/review_response:$COMMON_SITE"
export MPLBACKEND=Agg
export OPENBLAS_NUM_THREADS=4
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4

mkdir -p "$ARTIFACT"/{cache,echo,truth,logs,aggregate,tests}
exec > >(tee -a "$ARTIFACT/logs/run.log") 2>&1

echo "[$(date --iso-8601=seconds)] H01 start: $ARTIFACT"
cd "$ROOT"

"$PYTHON" "$RUNNER" manifest --project-root "$ROOT" --output "$ARTIFACT/manifest.json"

echo "[$(date --iso-8601=seconds)] focused tests"
"$PYTHON" -m pytest -q review_tests/test_h01_approximate_state_calibration.py \
  > "$ARTIFACT/tests/focused.log" 2>&1

conditions=(
  N2_active_eq_sto3g N2_active_stretch150_sto3g
  CO_active_eq_sto3g CO_active_stretch150_sto3g
  HF_full_eq_sto3g HF_full_stretch150_sto3g
)
formulae=(current_m3 yoshida4)

echo "[$(date --iso-8601=seconds)] rebuild H01 state/Hamiltonian caches"
active=0
for condition in "${conditions[@]}"; do
  "$PYTHON" "$RUNNER" prepare \
    --project-root "$ROOT" --condition "$condition" \
    --component-processes 4 --output "$ARTIFACT/cache/${condition}.pkl" \
    > "$ARTIFACT/logs/prepare_${condition}.log" 2>&1 &
  active=$((active + 1))
  if (( active == 2 )); then
    wait
    active=0
  fi
done
wait

for condition in "${conditions[@]}"; do
  test "$(jq -r .status "$ARTIFACT/cache/${condition}.metadata.json")" = complete
done

mapfile -t GPU_IDS < <(
  nvidia-smi --query-gpu=index,memory.free --format=csv,noheader,nounits \
    | awk -F, '$2+0 >= 4096 {gsub(/ /,"",$1); print $1}'
)
if (( ${#GPU_IDS[@]} == 0 )); then
  echo "No GPU with at least 4096 MiB free; stopping without touching any process."
  exit 2
fi
printf 'eligible physical GPUs: %s\n' "${GPU_IDS[*]}"

pilot_gpu=${GPU_IDS[0]}
echo "[$(date --iso-8601=seconds)] representative CPU/GPU pilot on physical GPU $pilot_gpu"
CUDA_VISIBLE_DEVICES=$pilot_gpu "$PYTHON" "$RUNNER" pilot \
  --project-root "$ROOT" \
  --cache "$ARTIFACT/cache/CO_active_eq_sto3g.pkl" \
  --gpu-id "$pilot_gpu" --output "$ARTIFACT/pilot.json" \
  > "$ARTIFACT/logs/pilot.log" 2>&1
test "$(jq -r .status "$ARTIFACT/pilot.json")" = complete

echo "[$(date --iso-8601=seconds)] echo calibration (CPU, six independent conditions in parallel)"
active=0
for condition in "${conditions[@]}"; do
  for formula in "${formulae[@]}"; do
    "$PYTHON" "$RUNNER" echo \
      --project-root "$ROOT" --condition "$condition" --formula "$formula" \
      --cache "$ARTIFACT/cache/${condition}.pkl" \
      --output "$ARTIFACT/echo/${condition}__${formula}.json" --backend cpu \
      > "$ARTIFACT/logs/echo_${condition}__${formula}.log" 2>&1 &
    active=$((active + 1))
    if (( active == 6 )); then
      wait
      active=0
    fi
  done
done
wait

for condition in "${conditions[@]}"; do
  for formula in "${formulae[@]}"; do
    echo_json="$ARTIFACT/echo/${condition}__${formula}.json"
    test "$(jq -r .status "$echo_json")" = complete
    test "$(jq -r .sanity.passed_before_approximate_state_interpretation "$echo_json")" = true
  done
done

echo "[$(date --iso-8601=seconds)] full review_tests before direct truth"
"$PYTHON" -m pytest -q review_tests > "$ARTIFACT/tests/review_tests.log" 2>&1

echo "[$(date --iso-8601=seconds)] direct truth, one condition/PF per GPU"
tasks=()
for condition in "${conditions[@]}"; do
  for formula in "${formulae[@]}"; do
    tasks+=("${condition}__${formula}")
  done
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
    echo "launch $task on physical GPU $gpu"
    CUDA_VISIBLE_DEVICES=$gpu "$PYTHON" "$RUNNER" truth \
      --project-root "$ROOT" --condition "$condition" --formula "$formula" \
      --cache "$ARTIFACT/cache/${condition}.pkl" \
      --echo "$ARTIFACT/echo/${task}.json" \
      --output "$ARTIFACT/truth/${task}.json" \
      --backend gpu --gpu-id "$gpu" \
      > "$ARTIFACT/logs/truth_${task}.log" 2>&1 &
    pids+=("$!")
    cursor=$((cursor + 1))
  done
  for pid in "${pids[@]}"; do
    wait "$pid"
  done
done

"$PYTHON" "$RUNNER" aggregate --artifact-root "$ARTIFACT"
echo "[$(date --iso-8601=seconds)] H01 COMPLETE: $ARTIFACT"
