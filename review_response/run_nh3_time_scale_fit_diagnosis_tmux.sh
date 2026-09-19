#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PYTHON_BIN="$ROOT/venv/bin/python"
COMMON_SITE="/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages"
export PYTHONPATH="$ROOT/src:$ROOT/review_response:$COMMON_SITE"
export MPLBACKEND=Agg
export OMP_NUM_THREADS=8
export OPENBLAS_NUM_THREADS=8
export MKL_NUM_THREADS=8

SCRIPT="$ROOT/review_response/run_nh3_time_scale_fit_diagnosis.py"
STAMP="${1:-$(date +%Y%m%d_%H%M%S)}"
SHORT="$(git rev-parse --short HEAD)"
OUT_DIR="$ROOT/artifacts/server_time_scale_fit_diagnosis_${STAMP}_${SHORT}"
CACHE_DIR="$OUT_DIR/runtime/cache"
WORK_DIR="$OUT_DIR/runtime/work"
RAW_DIR="$OUT_DIR/raw"
FINE_DIR="$OUT_DIR/fine_raw"
VECTOR_DIR="$OUT_DIR/runtime/vectors"
LOG_DIR="$OUT_DIR/logs"
mkdir -p "$CACHE_DIR" "$WORK_DIR" "$RAW_DIR" "$FINE_DIR" "$VECTOR_DIR" "$LOG_DIR"

"$PYTHON_BIN" - "$OUT_DIR/manifest.json" "$STAMP" "$SHORT" <<'PY'
import json
import pathlib
import subprocess
import sys
from datetime import datetime
path = pathlib.Path(sys.argv[1])
payload = {
    "status": "running",
    "started_at": datetime.now().astimezone().isoformat(),
    "stamp": sys.argv[2],
    "source_commit": sys.argv[3],
    "branch": subprocess.run(
        ["git", "branch", "--show-current"], text=True,
        capture_output=True, check=False
    ).stdout.strip(),
    "physical_gpu_ids": [0, 1, 2, 3],
    "one_condition_process_per_gpu": True,
    "cpu_threads_per_process": 8,
    "component_preparation_processes_per_condition": 4,
    "other_processes_stopped": False,
    "existing_results_overwritten": False,
    "scope": {
        "coefficient_reoptimization": False,
        "new_molecules": False,
        "morales_8th": False,
    },
}
path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
PY

conditions=(active_equilibrium active_stretch150 full_equilibrium full_stretch150)
gpus=(0 1 2 3)

echo "[$(date --iso-8601=seconds)] preparing four NH3 Hamiltonians in parallel" | tee -a "$LOG_DIR/master.log"
prepare_pids=()
for condition in "${conditions[@]}"; do
  "$PYTHON_BIN" "$SCRIPT" prepare \
    --condition "$condition" \
    --component-processes 4 \
    --work-dir "$WORK_DIR/$condition" \
    --output "$CACHE_DIR/$condition.pkl" \
    >"$LOG_DIR/prepare_${condition}.log" 2>&1 &
  prepare_pids+=("$!")
done
for pid in "${prepare_pids[@]}"; do
  wait "$pid"
done

echo "[$(date --iso-8601=seconds)] running four Hamiltonian conditions on GPUs 0-3" | tee -a "$LOG_DIR/master.log"
condition_pids=()
for index in 0 1 2 3; do
  condition="${conditions[$index]}"
  gpu="${gpus[$index]}"
  CUDA_VISIBLE_DEVICES="$gpu" "$PYTHON_BIN" "$SCRIPT" condition \
    --condition "$condition" \
    --system-cache "$CACHE_DIR/$condition.pkl" \
    --gpu-id "$gpu" \
    --output "$RAW_DIR/$condition.json" \
    >"$LOG_DIR/condition_${condition}_gpu${gpu}.log" 2>&1 &
  condition_pids+=("$!")
done
for pid in "${condition_pids[@]}"; do
  wait "$pid"
done

echo "[$(date --iso-8601=seconds)] adding only fine ratios 0.91, 1.03, 1.04" | tee -a "$LOG_DIR/master.log"
ratios=(0.91 1.03 1.04)
fine_pids=()
for index in 0 1 2; do
  ratio="${ratios[$index]}"
  gpu="${gpus[$index]}"
  key="$("$PYTHON_BIN" -c "import run_full_electron_nh3_followup_diagnostics as f; print(f.ratio_key($ratio))")"
  CUDA_VISIBLE_DEVICES="$gpu" "$PYTHON_BIN" "$SCRIPT" fine \
    --system-cache "$CACHE_DIR/full_stretch150.pkl" \
    --source-json "$ROOT/artifacts/full_electron_nh3_higher_term_diagnosis_20260919_230358_605384c/stretch150_raw/joint_refine_r0_s0046.json" \
    --ratio "$ratio" \
    --gpu-id "$gpu" \
    --output "$FINE_DIR/$key.json" \
    --vector-output "$VECTOR_DIR/$key.npy" \
    >"$LOG_DIR/fine_${key}_gpu${gpu}.log" 2>&1 &
  fine_pids+=("$!")
done
for pid in "${fine_pids[@]}"; do
  wait "$pid"
done

echo "[$(date --iso-8601=seconds)] aggregating JSON, CSV, and figures" | tee -a "$LOG_DIR/master.log"
"$PYTHON_BIN" "$SCRIPT" aggregate \
  --raw-dir "$RAW_DIR" \
  --fine-dir "$FINE_DIR" \
  --output-dir "$OUT_DIR" \
  >"$LOG_DIR/aggregate.log" 2>&1

touch "$OUT_DIR/COMPLETE"
"$PYTHON_BIN" - "$OUT_DIR/manifest.json" <<'PY'
import json
import pathlib
import sys
from datetime import datetime
path = pathlib.Path(sys.argv[1])
payload = json.loads(path.read_text(encoding="utf-8"))
payload["status"] = "complete"
payload["completed_at"] = datetime.now().astimezone().isoformat()
path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
PY
echo "[$(date --iso-8601=seconds)] COMPLETE" | tee -a "$LOG_DIR/master.log"
