#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ -v CUDA_VISIBLE_DEVICES ]]; then
  echo "Scheduler CUDA_VISIBLE_DEVICES is set; refusing to override it." >&2
  exit 2
fi

PYTHON_BIN="$ROOT/venv/bin/python"
COMMON_SITE="/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages"
export PYTHONPATH="$ROOT/src:$ROOT/review_response:$COMMON_SITE"
export MPLBACKEND=Agg
export OMP_NUM_THREADS=4
export OPENBLAS_NUM_THREADS=4
export MKL_NUM_THREADS=4

SCRIPT="$ROOT/review_response/audit_nh3_branch_protocol.py"
SOURCE_CACHE="$ROOT/artifacts/server_time_scale_fit_diagnosis_20260920_021411_80219a6/runtime/cache/full_stretch150.pkl"
STAMP="${1:-$(date +%Y%m%d_%H%M%S)}"
SHORT="$(git rev-parse --short HEAD)"
OUT="$ROOT/artifacts/server_nh3_branch_protocol_audit_${STAMP}_${SHORT}"
mkdir -p "$OUT/logs" "$OUT/points" "$OUT/vectors"
if [[ ! -f "$SOURCE_CACHE" ]]; then
  echo "Missing prepared NH3 system: $SOURCE_CACHE" >&2
  exit 2
fi

for gpu in 0 1 2 3 4 5 6 7; do
  free_mib="$(nvidia-smi --id="$gpu" --query-gpu=memory.free --format=csv,noheader,nounits | tr -d '[:space:]')"
  if [[ ! "$free_mib" =~ ^[0-9]+$ ]] || (( free_mib < 4096 )); then
    echo "GPU $gpu has insufficient free memory: $free_mib MiB" >&2
    exit 2
  fi
done

"$PYTHON_BIN" - "$OUT/manifest.json" "$SHORT" <<'PY'
import json
from datetime import datetime
from pathlib import Path
import subprocess
import sys
path = Path(sys.argv[1])
path.write_text(json.dumps({
    "status": "running",
    "started_at": datetime.now().astimezone().isoformat(),
    "code_commit": subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip(),
    "short_commit": sys.argv[2],
    "source_commits": ["84a37d1", "1615947"],
    "physical_gpu_ids": list(range(8)),
    "cpu_threads_per_gpu_worker": 4,
    "independent_pf_rebuild_ratios": [0.97, 1.01],
    "other_processes_stopped": False,
    "coefficients_changed": False,
    "new_molecules_added": False,
}, indent=2) + "\n", encoding="utf-8")
PY

echo "[$(date --iso-8601=seconds)] CPU reaggregation A/B" | tee -a "$OUT/logs/master.log"
"$PYTHON_BIN" "$SCRIPT" analyse --out "$OUT" >"$OUT/logs/analysis.log" 2>&1

labels=(
  a030 a060 a100 a140 a160
  r090 r091 r092 r093 r094 r095 r096 r097
  r098 r099 r100 r101 r102 r103 r104 r105
)
echo "[$(date --iso-8601=seconds)] GPU branch audit: ${#labels[@]} times across GPUs 0-7" | tee -a "$OUT/logs/master.log"
pids=()
for gpu in 0 1 2 3 4 5 6 7; do
  (
    for ((index=gpu; index<${#labels[@]}; index+=8)); do
      label="${labels[$index]}"
      echo "[$(date --iso-8601=seconds)] GPU $gpu started $label" >>"$OUT/logs/master.log"
      CUDA_VISIBLE_DEVICES="$gpu" "$PYTHON_BIN" "$SCRIPT" point \
        --out "$OUT" --label "$label" --gpu-id "$gpu" \
        --system-cache "$SOURCE_CACHE" \
        >"$OUT/logs/${label}_gpu${gpu}.log" 2>&1
      echo "[$(date --iso-8601=seconds)] GPU $gpu finished $label" >>"$OUT/logs/master.log"
    done
  ) &
  pids+=("$!")
done

failed=0
for pid in "${pids[@]}"; do
  if ! wait "$pid"; then
    failed=1
  fi
done
if (( failed )); then
  echo "[$(date --iso-8601=seconds)] one or more GPU workers failed; see per-time logs" | tee -a "$OUT/logs/master.log"
  exit 1
fi

echo "[$(date --iso-8601=seconds)] aggregating eigenbranch and cost results" | tee -a "$OUT/logs/master.log"
"$PYTHON_BIN" "$SCRIPT" aggregate --out "$OUT" >"$OUT/logs/aggregate.log" 2>&1

"$PYTHON_BIN" - "$OUT/manifest.json" <<'PY'
import json
from datetime import datetime
from pathlib import Path
import sys
path = Path(sys.argv[1])
record = json.loads(path.read_text(encoding="utf-8"))
record["status"] = "complete"
record["completed_at"] = datetime.now().astimezone().isoformat()
path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
PY
echo "[$(date --iso-8601=seconds)] COMPLETE" | tee -a "$OUT/logs/master.log"
