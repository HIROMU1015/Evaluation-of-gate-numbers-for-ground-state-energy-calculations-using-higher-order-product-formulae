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

SOURCE_DIR="$ROOT/artifacts/full_electron_nh3_higher_term_diagnosis_20260919_230358_605384c"
SCRIPT="$ROOT/review_response/run_full_electron_nh3_followup_diagnostics.py"
STAMP="${1:-$(date +%Y%m%d_%H%M%S)}"
SHORT="$(git rev-parse --short HEAD)"
OUT_DIR="$ROOT/artifacts/full_electron_nh3_followup_diagnostics_${STAMP}_${SHORT}"
LOG_DIR="$OUT_DIR/logs"
FINE_DIR="$OUT_DIR/fine_raw"
SHORT_DIR="$OUT_DIR/short_raw"
VECTOR_DIR="$OUT_DIR/runtime/vectors"
mkdir -p "$LOG_DIR" "$FINE_DIR" "$SHORT_DIR" "$VECTOR_DIR"

if [[ ! -f "$SOURCE_DIR/COMPLETE" ]]; then
  echo "source result is incomplete: $SOURCE_DIR" >&2
  exit 2
fi
if [[ ! -f "$SOURCE_DIR/cache/equilibrium.pkl" || ! -f "$SOURCE_DIR/cache/stretch150.pkl" ]]; then
  echo "required local system caches are missing" >&2
  exit 2
fi

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
    "physical_gpu_ids": [5, 6, 7],
    "one_process_per_gpu": True,
    "other_processes_stopped": False,
    "fine_ratios": [round(0.92 + 0.01 * index, 2) for index in range(11)],
    "extended_short_grid": "np.geomspace(0.01, 0.06, 13)",
    "scope": {
        "post_hoc_diagnostic": True,
        "coefficient_reoptimization": False,
        "additional_molecules": False,
    },
}
path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
PY

run_joint() {
  gpu="$1"
  ratios="$2"
  CUDA_VISIBLE_DEVICES="$gpu" "$PYTHON_BIN" "$SCRIPT" joint-worker \
    --system-cache "$SOURCE_DIR/cache/stretch150.pkl" \
    --source-json "$SOURCE_DIR/stretch150_raw/joint_refine_r0_s0046.json" \
    --ratios "$ratios" \
    --gpu-id "$gpu" \
    --output-dir "$FINE_DIR" \
    --vector-dir "$VECTOR_DIR" \
    >"$LOG_DIR/fine_gpu${gpu}.log" 2>&1
}

run_short() {
  gpu="$1"
  conditions="$2"
  CUDA_VISIBLE_DEVICES="$gpu" "$PYTHON_BIN" "$SCRIPT" short-worker \
    --cache-dir "$SOURCE_DIR/cache" \
    --source-dir "$SOURCE_DIR" \
    --conditions "$conditions" \
    --gpu-id "$gpu" \
    --output-dir "$SHORT_DIR" \
    >"$LOG_DIR/short_gpu${gpu}.log" 2>&1
}

echo "[$(date --iso-8601=seconds)] starting 11-point post-hoc fine scan on GPUs 5-7" | tee -a "$LOG_DIR/master.log"
run_joint 5 "0.92,0.95,0.98,1.01" &
p5=$!
run_joint 6 "0.93,0.96,0.99,1.02" &
p6=$!
run_joint 7 "0.94,0.97,1.00" &
p7=$!
wait "$p5"
wait "$p6"
wait "$p7"

echo "[$(date --iso-8601=seconds)] fine scan complete; starting extended short-time diagnostics" | tee -a "$LOG_DIR/master.log"
run_short 5 "equilibrium:yoshida4,equilibrium:yoshida6_m3" &
p5=$!
run_short 6 "equilibrium:paper_new4,stretch150:paper_new4,stretch150:yoshida6_m3" &
p6=$!
run_short 7 "equilibrium:m5_best,stretch150:m5_best" &
p7=$!
wait "$p5"
wait "$p6"
wait "$p7"

echo "[$(date --iso-8601=seconds)] aggregating diagnostics" | tee -a "$LOG_DIR/master.log"
"$PYTHON_BIN" "$SCRIPT" aggregate \
  --source-dir "$SOURCE_DIR" \
  --fine-point-dir "$FINE_DIR" \
  --vector-dir "$VECTOR_DIR" \
  --short-dir "$SHORT_DIR" \
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
