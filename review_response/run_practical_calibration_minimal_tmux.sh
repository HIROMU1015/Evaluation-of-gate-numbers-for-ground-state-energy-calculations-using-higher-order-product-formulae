#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_BIN="/home/AbeHiromu/venvs/trotter-common/bin/python"
H01_ROOT="/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/.worktrees/trotter-h01-calibration/artifacts/server_h01_approximate_state_calibration_20260922_011228_e0692a8"
P03_ROOT="/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/.worktrees/trotter-unused-molecule-holdout/artifacts/server_unused_molecule_frozen_holdout_20260921_d288797"
STAMP="$(date +%Y%m%d)"
PHASE_A_SHORT="$(git -C "$ROOT" rev-parse --short HEAD)"
OUT="$ROOT/artifacts/server_practical_calibration_minimal_${STAMP}_${PHASE_A_SHORT}"

if [[ -e "$OUT" ]]; then
  echo "refusing to overwrite $OUT" >&2
  exit 2
fi
mkdir -p "$OUT"
exec > >(tee -a "$OUT/driver.log") 2>&1

export PYTHONPATH="$ROOT/src:$ROOT/review_response:$ROOT"
export CUDA_VISIBLE_DEVICES=""
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

echo "[$(date --iso-8601=seconds)] practical calibration minimal starting"
echo "phase_a_commit=$(git -C "$ROOT" rev-parse HEAD)"
echo "protocol_sha256=$(sha256sum "$ROOT/review_response/practical_calibration_minimal_protocol.json" | awk '{print $1}')"
echo "output=$OUT"

echo "[$(date --iso-8601=seconds)] pre-scoring focused tests"
"$PYTHON_BIN" -m pytest -q review_tests/test_practical_calibration_minimal.py

echo "[$(date --iso-8601=seconds)] selector, freeze, and scorer"
set +e
"$PYTHON_BIN" review_response/run_practical_calibration_minimal.py run-all \
  --h01-root "$H01_ROOT" \
  --p03-root "$P03_ROOT" \
  --output-dir "$OUT" \
  | tee "$OUT/computation.log"
RUN_RC="${PIPESTATUS[0]}"
set -e

if [[ ! -f "$OUT/audit.json" || ! -f "$OUT/manifest.json" ]]; then
  echo "run-all failed without complete auditable outputs; rc=$RUN_RC" >&2
  exit "$RUN_RC"
fi

echo "[$(date --iso-8601=seconds)] focused tests"
set +e
"$PYTHON_BIN" -m pytest -q review_tests/test_practical_calibration_minimal.py \
  | tee "$OUT/focused_tests.log"
FOCUSED_RC="${PIPESTATUS[0]}"

echo "[$(date --iso-8601=seconds)] related tests"
"$PYTHON_BIN" -m pytest -q \
  review_tests/test_practical_calibration_minimal.py \
  review_tests/test_h01_approximate_state_calibration.py \
  review_tests/test_unused_molecule_frozen_holdout.py \
  | tee "$OUT/related_tests.log"
RELATED_RC="${PIPESTATUS[0]}"

echo "[$(date --iso-8601=seconds)] all review_tests"
"$PYTHON_BIN" -m pytest -q review_tests | tee "$OUT/all_review_tests.log"
FULL_RC="${PIPESTATUS[0]}"
set -e

"$PYTHON_BIN" review_response/run_practical_calibration_minimal.py finalize \
  --output-dir "$OUT" \
  --focused-exit-code "$FOCUSED_RC" \
  --related-exit-code "$RELATED_RC" \
  --all-review-tests-exit-code "$FULL_RC"

git -C "$ROOT" add "$OUT"
if ! git -C "$ROOT" diff --cached --quiet; then
  git -C "$ROOT" commit -m "Record oracle-free practical calibration results"
fi

BRANCH="$(git -C "$ROOT" branch --show-current)"
echo "[$(date --iso-8601=seconds)] attempting non-interactive normal push of $BRANCH"
set +e
GIT_TERMINAL_PROMPT=0 git -C "$ROOT" push -u origin "$BRANCH"
PUSH_RC="$?"
set -e
if [[ "$PUSH_RC" -ne 0 ]]; then
  echo "push failed with exit code $PUSH_RC; local commit and artifacts retained" >&2
fi
echo "[$(date --iso-8601=seconds)] finished run_rc=$RUN_RC focused_rc=$FOCUSED_RC related_rc=$RELATED_RC full_rc=$FULL_RC push_rc=$PUSH_RC"
