#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_BIN="/home/AbeHiromu/venvs/trotter-common/bin/python"
SOURCE_ROOT="/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/.worktrees/trotter-h01-calibration/artifacts/server_h01_approximate_state_calibration_20260922_011228_e0692a8"
HOLDOUT_ROOT="$ROOT/artifacts/server_unused_molecule_frozen_holdout_20260921_d288797"
STAMP="$(date +%Y%m%d)"
SHORT="$(git -C "$ROOT" rev-parse --short HEAD)"
OUT="$ROOT/artifacts/server_f_hf_mechanism_bridge_$STAMP"_"$SHORT"
DRIVER_LOG="$ROOT/artifacts/server_f_hf_mechanism_bridge_$STAMP"_"$SHORT.driver.log"

if [[ -e "$OUT" ]]; then
  echo "refusing to overwrite $OUT" >&2
  exit 2
fi
if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "missing Python: $PYTHON_BIN" >&2
  exit 2
fi

exec > >(tee -a "$DRIVER_LOG") 2>&1
echo "[$(date --iso-8601=seconds)] starting F01/F02/F05 HF mechanism bridge"
echo "root=$ROOT"
echo "source=$SOURCE_ROOT"
echo "output=$OUT"

export PYTHONPATH="$ROOT/src:$ROOT/review_response:$ROOT"

echo "[$(date --iso-8601=seconds)] running bridge unit tests"
"$PYTHON_BIN" -m pytest -q review_tests/test_f_hf_mechanism_bridge.py

echo "[$(date --iso-8601=seconds)] running frozen mechanism bridge"
"$PYTHON_BIN" review_response/run_f_hf_mechanism_bridge.py \
  --source-root "$SOURCE_ROOT" \
  --holdout-root "$HOLDOUT_ROOT" \
  --output-dir "$OUT"

echo "[$(date --iso-8601=seconds)] running related tests"
"$PYTHON_BIN" -m pytest -q \
  review_tests/test_f_hf_mechanism_bridge.py \
  review_tests/test_bch_matrix_series.py \
  review_tests/test_f01_effective_hamiltonian_pilot.py \
  review_tests/test_f01_effective_hamiltonian_multipf.py \
  review_tests/test_f02_tau8_state_mixing.py \
  review_tests/test_f05_energy_phase_gap.py \
  review_tests/test_h01_approximate_state_calibration.py \
  | tee "$OUT/related_tests.log"

echo "[$(date --iso-8601=seconds)] running all review_tests"
set +e
"$PYTHON_BIN" -m pytest -q review_tests | tee "$OUT/all_review_tests.log"
FULL_TEST_RC="$?"
set -e

"$PYTHON_BIN" review_response/finalize_f_hf_mechanism_bridge.py \
  --output-dir "$OUT" \
  --all-review-tests-exit-code "$FULL_TEST_RC"

STATUS="$(jq -r .status "$OUT/audit.json")"
if [[ "$STATUS" != "complete_with_findings" ]]; then
  echo "numerical status is $STATUS; COMPLETE will not be created" >&2
  exit 2
fi
touch "$OUT/COMPLETE"

git -C "$ROOT" add "$OUT"
if ! git -C "$ROOT" diff --cached --quiet; then
  git -C "$ROOT" commit -m "Record HF mechanism bridge results"
fi

BRANCH="$(git -C "$ROOT" branch --show-current)"
echo "[$(date --iso-8601=seconds)] attempting normal push of $BRANCH"
set +e
git -C "$ROOT" push -u origin "$BRANCH"
PUSH_RC="$?"
set -e
if [[ "$PUSH_RC" -ne 0 ]]; then
  echo "push failed with exit code $PUSH_RC; local commit and artifacts retained" >&2
fi
echo "[$(date --iso-8601=seconds)] bridge driver finished; push_rc=$PUSH_RC"
