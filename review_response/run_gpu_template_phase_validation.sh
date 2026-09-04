#!/usr/bin/env bash
set -u -o pipefail

PROJECT_ROOT="/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae"
PYTHON_BIN="${PROJECT_ROOT}/venv/bin/python"
COMMON_SITE="/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages"
PYTHON_PATH_VALUE="${COMMON_SITE}:${PROJECT_ROOT}/src:${PROJECT_ROOT}/review_response"
SCRIPT="${PROJECT_ROOT}/review_response/validate_gpu_template_phase.py"
SPARSE_BENCHMARK="${PROJECT_ROOT}/review_response/benchmark_sparse_pf_smoke.py"
SHORT_COMMIT="$(git -C "${PROJECT_ROOT}" rev-parse --short=7 HEAD)"
RUN_DATE="$(date +%Y%m%d)"
RUN_SUFFIX="${1:-}"
if [[ -n "${RUN_SUFFIX}" && ! "${RUN_SUFFIX}" =~ ^[A-Za-z0-9._-]+$ ]]; then
  echo "ERROR: invalid run suffix: ${RUN_SUFFIX}"
  exit 2
fi
OUTPUT_DIR="${PROJECT_ROOT}/artifacts/gpu_template_phase_validation_${RUN_DATE}_${SHORT_COMMIT}${RUN_SUFFIX:+_${RUN_SUFFIX}}"
RAW_DIR="${OUTPUT_DIR}/raw"
LOG_DIR="${OUTPUT_DIR}/logs"
T_ANA="2.08043234194074"
T_ANA_SOURCE="artifacts/server_cost_validity/h6_h7_analytic_schedule/H6_analytic_direct_validation.json; reused for H8 runtime-only timing because no H8-specific saved t_ana exists"
REUSABLE_SHARED_INPUT="${PROJECT_ROOT}/artifacts/gpu_sparse_pf_smoke_20260904_7d1938b_retry1/shared/H6_shared_input.json"

if [[ -e "${OUTPUT_DIR}" ]]; then
  echo "ERROR: refusing to overwrite ${OUTPUT_DIR}"
  exit 2
fi
mkdir -p "${RAW_DIR}" "${LOG_DIR}"
cd "${PROJECT_ROOT}" || exit 2
exec > >(tee -a "${LOG_DIR}/master.log") 2>&1

gpu_rows() {
  timeout 90s nvidia-smi \
    --query-gpu=index,memory.used,memory.total,utilization.gpu \
    --format=csv,noheader,nounits | \
    awk -F',' '{for(i=1;i<=NF;i++) gsub(/ /,"",$i); if ($2*2 <= $3) print $1, $2, $4}' | \
    sort -k2,2n -k3,3n
}

mapfile -t SAFE_ROWS < <(gpu_rows)
if (( ${#SAFE_ROWS[@]} < 2 )); then
  echo "ERROR: two GPUs with at least half their memory free are required for parallel validation"
  printf 'status=insufficient_safe_gpus\ncommit=%s\n' "${SHORT_COMMIT}" > "${OUTPUT_DIR}/FAILED"
  exit 3
fi
GPU_H6="$(awk '{print $1}' <<< "${SAFE_ROWS[0]}")"
GPU_H8="$(awk '{print $1}' <<< "${SAFE_ROWS[1]}")"

common_env=(
  TROTTER_PROJECT_ROOT="${PROJECT_ROOT}"
  TROTTER_QISKIT_DEVICE=GPU
  TROTTER_QISKIT_AER_METHOD=statevector
  TROTTER_QISKIT_AER_PRECISION=double
  TROTTER_QISKIT_TARGET_GPUS=0
  TROTTER_POOL_PROCESSES=1
  MPLBACKEND=Agg
  PYTHONPATH="${PYTHON_PATH_VALUE}"
  OMP_NUM_THREADS=4
  OPENBLAS_NUM_THREADS=4
  MKL_NUM_THREADS=4
)

if [[ -f "${REUSABLE_SHARED_INPUT}" ]]; then
  SHARED_INPUT="${REUSABLE_SHARED_INPUT}"
  echo "Reusing server-local H6 shared input: ${SHARED_INPUT}"
else
  mkdir -p "${OUTPUT_DIR}/shared"
  SHARED_INPUT="${OUTPUT_DIR}/shared/H6_shared_input.json"
  SHARED_ARRAYS="${OUTPUT_DIR}/shared/H6_shared_arrays.npz"
  echo "Preparing H6 shared input because no reusable server-local cache exists."
  env "${common_env[@]}" "${PYTHON_BIN}" "${SPARSE_BENCHMARK}" prepare-h6 \
    --output "${SHARED_INPUT}" \
    --arrays-output "${SHARED_ARRAYS}" \
    > "${LOG_DIR}/H6_shared_preparation.log" 2>&1
  PREPARE_STATUS=$?
  if (( PREPARE_STATUS != 0 )); then
    printf 'status=h6_shared_preparation_failed\ncommit=%s\n' "${SHORT_COMMIT}" > "${OUTPUT_DIR}/FAILED"
    exit 4
  fi
fi

echo "RUN_START $(date --iso-8601=seconds) commit=${SHORT_COMMIT} output=${OUTPUT_DIR}"
echo "GPU_SELECTION H6=${GPU_H6} H8=${GPU_H8}; only GPUs with at least half memory free admitted"

env "${common_env[@]}" CUDA_VISIBLE_DEVICES="${GPU_H6}" \
  "${PYTHON_BIN}" "${SCRIPT}" h6-phase \
    --physical-gpu-id "${GPU_H6}" \
    --t-ana "${T_ANA}" \
    --t-ana-source "${T_ANA_SOURCE}" \
    --shared-input "${SHARED_INPUT}" \
    --output "${RAW_DIR}/H6_m5_global_phase.json" \
    > "${LOG_DIR}/H6_m5_global_phase.log" 2>&1 &
H6_PID=$!

env "${common_env[@]}" CUDA_VISIBLE_DEVICES="${GPU_H8}" \
  "${PYTHON_BIN}" "${SCRIPT}" h8-reuse \
    --physical-gpu-id "${GPU_H8}" \
    --t-ana "${T_ANA}" \
    --t-ana-source "${T_ANA_SOURCE}" \
    --output "${RAW_DIR}/H8_m5_template_reuse.json" \
    > "${LOG_DIR}/H8_m5_template_reuse.log" 2>&1 &
H8_PID=$!

FAILED=0
wait "${H6_PID}" || FAILED=1
wait "${H8_PID}" || FAILED=1

env PYTHONPATH="${PYTHON_PATH_VALUE}" "${PYTHON_BIN}" "${SCRIPT}" summarize \
  --h6-json "${RAW_DIR}/H6_m5_global_phase.json" \
  --h8-json "${RAW_DIR}/H8_m5_template_reuse.json" \
  --output-dir "${OUTPUT_DIR}"
SUMMARY_STATUS=$?

echo "RUN_FINISH $(date --iso-8601=seconds) worker_failure=${FAILED} summary_status=${SUMMARY_STATUS}"
exit "$(( FAILED != 0 || SUMMARY_STATUS != 0 ))"
