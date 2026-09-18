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

SCRIPT="$ROOT/review_response/run_full_electron_nh3_higher_term_diagnosis.py"
STAMP="$(date +%Y%m%d_%H%M%S)"
if [[ $# -ge 1 ]]; then
  STAMP="$1"
fi
SHORT="$(git rev-parse --short HEAD)"
OUT_DIR="$ROOT/artifacts/full_electron_nh3_higher_term_diagnosis_"$STAMP"_"$SHORT
CACHE_DIR="$OUT_DIR/cache"
LOG_DIR="$OUT_DIR/logs"
RAW_EQ="$OUT_DIR/equilibrium_raw"
RAW_ST="$OUT_DIR/stretch150_raw"
mkdir -p "$CACHE_DIR" "$LOG_DIR" "$RAW_EQ" "$RAW_ST"

"$PYTHON_BIN" - "$OUT_DIR/manifest.json" "$STAMP" "$SHORT" <<'PY'
import json
import pathlib
import subprocess
import sys
path = pathlib.Path(sys.argv[1])
payload = {
    "status": "running",
    "stamp": sys.argv[2],
    "source_commit": sys.argv[3],
    "branch": subprocess.run(
        ["git", "branch", "--show-current"], text=True,
        capture_output=True, check=False
    ).stdout.strip(),
    "physical_gpu_ids": [5, 6, 7],
    "safety": {
        "other_processes_stopped": False,
        "cuda_visible_devices_limited_per_worker": True,
    },
    "fit_protocol": {
        "grid": "np.geomspace(0.06, 0.80, 15)",
        "window": 5,
        "noise_floor": 5e-13,
        "order_tolerance": 0.2,
        "minimum_r2": 0.999,
        "selection": "earliest qualifying window",
        "on_failure": "report failure without changing rules",
    },
}
path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
PY

run_prepare() {
  geometry="$1"
  "$PYTHON_BIN" "$SCRIPT" prepare \
    --geometry "$geometry" \
    --component-processes 8 \
    --output "$CACHE_DIR/$geometry.pkl" \
    >"$LOG_DIR/$geometry"_prepare.log 2>&1
}

run_formula() {
  geometry="$1"
  formula="$2"
  gpu="$3"
  backend="$4"
  raw_dir="$5"
  CUDA_VISIBLE_DEVICES="$gpu" \
    "$PYTHON_BIN" "$SCRIPT" formula \
      --system-cache "$CACHE_DIR/$geometry.pkl" \
      --formula "$formula" \
      --backend "$backend" \
      --gpu-id "$gpu" \
      --output "$raw_dir/$formula.json" \
      >"$LOG_DIR/$geometry"_"$formula".log 2>&1
}

run_geometry() {
  geometry="$1"
  backend="$2"
  raw_dir="$3"

  run_formula "$geometry" yoshida4 5 "$backend" "$raw_dir" &
  p1=$!
  run_formula "$geometry" paper_new4 6 "$backend" "$raw_dir" &
  p2=$!
  run_formula "$geometry" m5_best 7 "$backend" "$raw_dir" &
  p3=$!
  wait "$p1"; wait "$p2"; wait "$p3"

  run_formula "$geometry" two_term_center 5 "$backend" "$raw_dir" &
  p1=$!
  run_formula "$geometry" joint_refine_r0_s0046 6 "$backend" "$raw_dir" &
  p2=$!
  run_formula "$geometry" yoshida6_m3 7 "$backend" "$raw_dir" &
  p3=$!
  wait "$p1"; wait "$p2"; wait "$p3"

  "$PYTHON_BIN" "$SCRIPT" aggregate \
    --geometry "$geometry" \
    --raw-dir "$raw_dir" \
    --output "$OUT_DIR/$geometry"_summary.json \
    >"$LOG_DIR/$geometry"_aggregate.log 2>&1
}

echo "[$(date --iso-8601=seconds)] preparing equilibrium" | tee -a "$LOG_DIR/master.log"
run_prepare equilibrium

echo "[$(date --iso-8601=seconds)] benchmarking exact CPU/GPU sector build" | tee -a "$LOG_DIR/master.log"
CUDA_VISIBLE_DEVICES=5 \
  "$PYTHON_BIN" "$SCRIPT" benchmark \
    --system-cache "$CACHE_DIR/equilibrium.pkl" \
    --formula yoshida4 \
    --time 0.4 \
    --gpu-id 5 \
    --output "$OUT_DIR/benchmark.json" \
    >"$LOG_DIR/benchmark.log" 2>&1

BACKEND="$("$PYTHON_BIN" -c "import json; print(json.load(open('$OUT_DIR/benchmark.json'))['chosen_backend'])")"
echo "[$(date --iso-8601=seconds)] selected backend=$BACKEND" | tee -a "$LOG_DIR/master.log"

echo "[$(date --iso-8601=seconds)] starting equilibrium formulae" | tee -a "$LOG_DIR/master.log"
run_geometry equilibrium "$BACKEND" "$RAW_EQ"

echo "[$(date --iso-8601=seconds)] equilibrium healthy; preparing stretch150" | tee -a "$LOG_DIR/master.log"
run_prepare stretch150
run_geometry stretch150 "$BACKEND" "$RAW_ST"
"$PYTHON_BIN" review_response/aggregate_full_electron_nh3_higher_term_results.py \
  --output-dir "$OUT_DIR" \
  >"$LOG_DIR/final_aggregate.log" 2>&1

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
