#!/usr/bin/env bash
set -u -o pipefail

PROJECT_ROOT="/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae"
SHORT_COMMIT="$(git -C "${PROJECT_ROOT}" rev-parse --short=7 HEAD)"
RUN_DATE="$(date +%Y%m%d)"
RUN_SUFFIX="${1:-}"
if [[ -n "${RUN_SUFFIX}" && ! "${RUN_SUFFIX}" =~ ^[A-Za-z0-9._-]+$ ]]; then
  echo "ERROR: invalid run suffix: ${RUN_SUFFIX}"
  exit 2
fi
OUTPUT_DIR="${PROJECT_ROOT}/artifacts/server_direct_solver_benchmark_${RUN_DATE}_${SHORT_COMMIT}${RUN_SUFFIX:+_${RUN_SUFFIX}}"
RAW_DIR="${OUTPUT_DIR}/raw"
LOG_DIR="${OUTPUT_DIR}/logs"
PYTHON_BIN="${PROJECT_ROOT}/venv/bin/python"
COMMON_SITE="/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages"
PYTHON_PATH_VALUE="${COMMON_SITE}:${PROJECT_ROOT}/src:${PROJECT_ROOT}/review_response"
BENCHMARK="${PROJECT_ROOT}/review_response/benchmark_direct_pf_solvers.py"

if [[ -e "${OUTPUT_DIR}" ]]; then
  echo "ERROR: refusing to overwrite ${OUTPUT_DIR}"
  exit 2
fi
mkdir -p "${RAW_DIR}" "${LOG_DIR}"
cd "${PROJECT_ROOT}" || exit 2
exec > >(tee -a "${LOG_DIR}/master.log") 2>&1

gpu_is_safe() {
  local gpu_id="$1"
  local line used total
  line="$(timeout 90s nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits -i "${gpu_id}")" || return 1
  IFS=',' read -r used total <<< "${line}"
  used="${used// /}"
  total="${total// /}"
  if (( used * 2 > total )); then
    echo "GPU ${gpu_id}: unsafe, ${used}/${total} MiB used"
    return 1
  fi
  echo "GPU ${gpu_id}: safe, ${used}/${total} MiB used"
}

run_case() {
  local h_chain="$1" label="$2" slug="$3" t_ana="$4" source="$5" gpu_id="$6" repeats="$7"
  local output="${RAW_DIR}/H${h_chain}_${slug}.json"
  local log="${LOG_DIR}/H${h_chain}_${slug}.log"
  gpu_is_safe "${gpu_id}" || return 2
  echo "START H${h_chain} ${label} GPU=${gpu_id} $(date --iso-8601=seconds)"
  env \
    CUDA_VISIBLE_DEVICES="${gpu_id}" \
    TROTTER_PROJECT_ROOT="${PROJECT_ROOT}" \
    TROTTER_QISKIT_DEVICE=GPU \
    TROTTER_QISKIT_AER_METHOD=statevector \
    TROTTER_QISKIT_AER_PRECISION=double \
    TROTTER_QISKIT_TARGET_GPUS=0 \
    TROTTER_POOL_PROCESSES=1 \
    OMP_NUM_THREADS=4 \
    OPENBLAS_NUM_THREADS=4 \
    MKL_NUM_THREADS=4 \
    MPLBACKEND=Agg \
    PYTHONPATH="${PYTHON_PATH_VALUE}" \
    "${PYTHON_BIN}" "${BENCHMARK}" run \
      --h-chain "${h_chain}" \
      --label "${label}" \
      --t-ana "${t_ana}" \
      --t-ana-source "${source}" \
      --gpu-id "${gpu_id}" \
      --repeats "${repeats}" \
      --output "${output}" > "${log}" 2>&1
  local status=$?
  echo "FINISH H${h_chain} ${label} status=${status} $(date --iso-8601=seconds)"
  return "${status}"
}

echo "RUN_START $(date --iso-8601=seconds) commit=${SHORT_COMMIT}"

# H4 smoke: two independent PFs on two GPUs.  Continue only if both raw jobs
# finish; scientific pass/fail remains recorded by the automatic summary.
run_case 4 '4th(m5_best)' m5 2.5008214570783696 \
  'artifacts/server_cost_validity/wide_gpu/H4_m5_wide_refined.json fixed-order alpha' 0 3 &
H4_M5_PID=$!
run_case 4 '8th(Morales-Y8m10b)' y8 5.130858254277709 \
  'artifacts/server_cost_validity/wide_gpu/H4_y8m10b_wide_refined.json fixed-order alpha' 1 3 &
H4_Y8_PID=$!
H4_FAILED=0
wait "${H4_M5_PID}" || H4_FAILED=1
wait "${H4_Y8_PID}" || H4_FAILED=1
if (( H4_FAILED != 0 )); then
  echo "H4 smoke execution failed; H6/H7 not started"
  env PYTHONPATH="${PYTHON_PATH_VALUE}" "${PYTHON_BIN}" "${BENCHMARK}" summarize \
    --raw-json "${RAW_DIR}"/*.json --output-dir "${OUTPUT_DIR}" || true
  printf 'status=failed\nreason=h4_raw_job_failed\ncommit=%s\n' \
    "${SHORT_COMMIT}" > "${OUTPUT_DIR}/FAILED"
  exit 3
fi

# Main calibration: each (system, PF) owns one GPU and one process.  No other
# process is terminated or modified.
run_case 6 '4th(m5_best)' m5 2.08043234194074 \
  'artifacts/server_cost_validity/h6_h7_analytic_schedule/H6_analytic_direct_validation.json' 2 3 &
H6_M5_PID=$!
run_case 6 '8th(Morales-Y8m10b)' y8 3.8111081333521963 \
  'artifacts/server_cost_validity/h6_h7_analytic_schedule/H6_analytic_direct_validation.json' 3 3 &
H6_Y8_PID=$!
run_case 7 '4th(m5_best)' m5 2.1695932395491946 \
  'artifacts/server_cost_validity/h6_h7_analytic_schedule/fci_checked/H7_analytic_direct_validation_fci_checked.json' 4 1 &
H7_M5_PID=$!
run_case 7 '8th(Morales-Y8m10b)' y8 4.386367415958895 \
  'artifacts/server_cost_validity/h6_h7_analytic_schedule/fci_checked/H7_analytic_direct_validation_fci_checked.json' 5 1 &
H7_Y8_PID=$!

FAILED=0
for pid in "${H6_M5_PID}" "${H6_Y8_PID}" "${H7_M5_PID}" "${H7_Y8_PID}"; do
  wait "${pid}" || FAILED=1
done

SUMMARY_FAILED=0
env PYTHONPATH="${PYTHON_PATH_VALUE}" "${PYTHON_BIN}" "${BENCHMARK}" summarize \
  --raw-json "${RAW_DIR}"/*.json --output-dir "${OUTPUT_DIR}" || SUMMARY_FAILED=1

if (( FAILED == 0 && SUMMARY_FAILED == 0 )); then
  printf 'status=calibration_complete\ncommit=%s\n' "${SHORT_COMMIT}" > "${OUTPUT_DIR}/COMPLETE"
else
  printf 'status=failed\nraw_jobs_failed=%s\nsummary_failed=%s\ncommit=%s\n' \
    "${FAILED}" "${SUMMARY_FAILED}" "${SHORT_COMMIT}" > "${OUTPUT_DIR}/FAILED"
fi
echo "RUN_FINISH $(date --iso-8601=seconds) raw_failed=${FAILED} summary_failed=${SUMMARY_FAILED}"
exit "$(( FAILED != 0 || SUMMARY_FAILED != 0 ))"
