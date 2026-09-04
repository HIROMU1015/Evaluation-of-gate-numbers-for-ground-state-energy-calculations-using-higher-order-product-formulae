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
OUTPUT_DIR="${PROJECT_ROOT}/artifacts/gpu_sparse_pf_smoke_${RUN_DATE}_${SHORT_COMMIT}${RUN_SUFFIX:+_${RUN_SUFFIX}}"
RAW_DIR="${OUTPUT_DIR}/raw"
STATE_DIR="${OUTPUT_DIR}/states"
LOG_DIR="${OUTPUT_DIR}/logs"
SHARED_DIR="${OUTPUT_DIR}/shared"
PYTHON_BIN="${PROJECT_ROOT}/venv/bin/python"
COMMON_SITE="/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages"
PYTHON_PATH_VALUE="${COMMON_SITE}:${PROJECT_ROOT}/src:${PROJECT_ROOT}/review_response"
BENCHMARK="${PROJECT_ROOT}/review_response/benchmark_sparse_pf_smoke.py"
T_ANA="2.08043234194074"
T_ANA_SOURCE="artifacts/server_cost_validity/h6_h7_analytic_schedule/H6_analytic_direct_validation.json; reused for H8 runtime-only smoke because no H8-specific saved t_ana exists"

if [[ -e "${OUTPUT_DIR}" ]]; then
  echo "ERROR: refusing to overwrite ${OUTPUT_DIR}"
  exit 2
fi
mkdir -p "${RAW_DIR}" "${STATE_DIR}" "${LOG_DIR}" "${SHARED_DIR}"
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
if (( ${#SAFE_ROWS[@]} < 1 )); then
  echo "ERROR: no GPU has at least half of its memory free"
  exit 3
fi
GPU_A="$(awk '{print $1}' <<< "${SAFE_ROWS[0]}")"
if (( ${#SAFE_ROWS[@]} >= 2 )); then
  GPU_B="$(awk '{print $1}' <<< "${SAFE_ROWS[1]}")"
else
  GPU_B="${GPU_A}"
fi

common_env=(
  TROTTER_PROJECT_ROOT="${PROJECT_ROOT}"
  TROTTER_QISKIT_DEVICE=GPU
  TROTTER_QISKIT_AER_METHOD=statevector
  TROTTER_QISKIT_AER_PRECISION=double
  TROTTER_QISKIT_TARGET_GPUS=0
  TROTTER_POOL_PROCESSES=1
  MPLBACKEND=Agg
  PYTHONPATH="${PYTHON_PATH_VALUE}"
)

SHARED_INPUT="${SHARED_DIR}/H6_shared_input.json"
SHARED_ARRAYS="${SHARED_DIR}/H6_shared_arrays.npz"

monitor_gpu_worker() {
  local gpu_id="$1" result_json="$2" samples_csv="$3" worker_log="$4"
  shift 4
  nvidia-smi --query-gpu=memory.used,memory.total \
    --format=csv,noheader,nounits -i "${gpu_id}" -lms 200 \
    > "${samples_csv}" 2> "${samples_csv}.stderr" &
  local monitor_pid=$!
  sleep 0.3
  "$@" > "${worker_log}" 2>&1
  local worker_status=$?
  kill "${monitor_pid}" 2>/dev/null || true
  wait "${monitor_pid}" 2>/dev/null || true
  local attach_status=0
  if [[ -f "${result_json}" ]]; then
    env PYTHONPATH="${PYTHON_PATH_VALUE}" "${PYTHON_BIN}" "${BENCHMARK}" attach-memory \
      --result-json "${result_json}" \
      --samples-csv "${samples_csv}" \
      --physical-gpu-id "${gpu_id}" \
      --interval-ms 200 || attach_status=$?
  else
    attach_status=1
  fi
  if (( worker_status != 0 )); then
    return "${worker_status}"
  fi
  return "${attach_status}"
}

run_cpu_h6() {
  env "${common_env[@]}" OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 MKL_NUM_THREADS=8 \
    "${PYTHON_BIN}" "${BENCHMARK}" cpu-dense \
      --h-chain 6 --t-ana "${T_ANA}" --t-ana-source "${T_ANA_SOURCE}" \
      --shared-input "${SHARED_INPUT}" \
      --output "${RAW_DIR}/H6_cpu_dense.json" \
      --state-output "${STATE_DIR}/H6_cpu_dense_state.npz" \
      > "${LOG_DIR}/H6_cpu_dense.log" 2>&1
}

run_gpu_dense_h6() {
  local gpu_id="$1"
  monitor_gpu_worker "${gpu_id}" \
    "${RAW_DIR}/H6_gpu_dense.json" \
    "${LOG_DIR}/H6_gpu_dense_memory.csv" \
    "${LOG_DIR}/H6_gpu_dense.log" \
    env "${common_env[@]}" CUDA_VISIBLE_DEVICES="${gpu_id}" \
      OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 \
      "${PYTHON_BIN}" "${BENCHMARK}" gpu-dense \
        --h-chain 6 --t-ana "${T_ANA}" --t-ana-source "${T_ANA_SOURCE}" \
        --shared-input "${SHARED_INPUT}" \
        --physical-gpu-id "${gpu_id}" \
        --output "${RAW_DIR}/H6_gpu_dense.json" \
        --state-output "${STATE_DIR}/H6_gpu_dense_state.npz"
}

run_aer() {
  local h_chain="$1" gpu_id="$2"
  local shared_args=()
  if [[ "${h_chain}" == "6" ]]; then
    shared_args=(--shared-input "${SHARED_INPUT}")
  fi
  monitor_gpu_worker "${gpu_id}" \
    "${RAW_DIR}/H${h_chain}_aer_matrix_free.json" \
    "${LOG_DIR}/H${h_chain}_aer_matrix_free_memory.csv" \
    "${LOG_DIR}/H${h_chain}_aer_matrix_free.log" \
    env "${common_env[@]}" CUDA_VISIBLE_DEVICES="${gpu_id}" \
      OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 \
      "${PYTHON_BIN}" "${BENCHMARK}" aer \
        --h-chain "${h_chain}" --t-ana "${T_ANA}" --t-ana-source "${T_ANA_SOURCE}" \
        "${shared_args[@]}" \
        --physical-gpu-id "${gpu_id}" \
        --output "${RAW_DIR}/H${h_chain}_aer_matrix_free.json" \
        --state-output "${STATE_DIR}/H${h_chain}_aer_matrix_free_state.npz"
}

echo "RUN_START $(date --iso-8601=seconds) commit=${SHORT_COMMIT} output=${OUTPUT_DIR}"
echo "Preparing one shared H6 orbital basis, Hamiltonian decomposition, ground state, and sector spectra."
env "${common_env[@]}" OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 MKL_NUM_THREADS=8 \
  "${PYTHON_BIN}" "${BENCHMARK}" prepare-h6 \
    --output "${SHARED_INPUT}" \
    --arrays-output "${SHARED_ARRAYS}" \
    > "${LOG_DIR}/H6_shared_preparation.log" 2>&1
PREPARE_STATUS=$?
if (( PREPARE_STATUS != 0 )); then
  echo "Shared H6 preparation failed; no benchmark worker was started."
  printf 'status=h6_shared_preparation_failed\ncommit=%s\n' "${SHORT_COMMIT}" > "${OUTPUT_DIR}/FAILED"
  exit 4
fi
echo "GPU_SELECTION first=${GPU_A} second=${GPU_B} (sorted by memory used, then utilization; only <=50% occupied admitted)"
echo "H6 CPU dense, H6 GPU dense, and H6 Aer matrix-free start in parallel when two safe GPUs are available."

run_cpu_h6 &
CPU_PID=$!
if [[ "${GPU_A}" != "${GPU_B}" ]]; then
  run_gpu_dense_h6 "${GPU_A}" &
  DENSE_PID=$!
  run_aer 6 "${GPU_B}" &
  AER_PID=$!
else
  (
    run_gpu_dense_h6 "${GPU_A}" && run_aer 6 "${GPU_A}"
  ) &
  DENSE_AND_AER_PID=$!
fi

FAILED=0
wait "${CPU_PID}" || FAILED=1
if [[ "${GPU_A}" != "${GPU_B}" ]]; then
  wait "${DENSE_PID}" || FAILED=1
  wait "${AER_PID}" || FAILED=1
else
  wait "${DENSE_AND_AER_PID}" || FAILED=1
fi

if (( FAILED != 0 )); then
  echo "H6 raw measurement failed; H8 was not started."
  printf 'status=h6_raw_failed\ncommit=%s\n' "${SHORT_COMMIT}" > "${OUTPUT_DIR}/FAILED"
  exit 4
fi

env PYTHONPATH="${PYTHON_PATH_VALUE}" "${PYTHON_BIN}" "${BENCHMARK}" verify-h6 \
  --cpu-json "${RAW_DIR}/H6_cpu_dense.json" \
  --gpu-dense-json "${RAW_DIR}/H6_gpu_dense.json" \
  --aer-json "${RAW_DIR}/H6_aer_matrix_free.json" \
  --output "${RAW_DIR}/H6_state_agreement.json"
VERIFY_STATUS=$?
if (( VERIFY_STATUS != 0 )); then
  echo "H6 agreement failed; H8 was not started."
  printf 'status=h6_agreement_failed\ncommit=%s\n' "${SHORT_COMMIT}" > "${OUTPUT_DIR}/FAILED"
  exit 5
fi

mapfile -t H8_SAFE_ROWS < <(gpu_rows)
if (( ${#H8_SAFE_ROWS[@]} < 1 )); then
  echo "ERROR: no safe GPU available for H8 after H6 verification"
  printf 'status=no_safe_gpu_for_h8\ncommit=%s\n' "${SHORT_COMMIT}" > "${OUTPUT_DIR}/FAILED"
  exit 6
fi
H8_GPU="$(awk '{print $1}' <<< "${H8_SAFE_ROWS[0]}")"
echo "H6 agreement passed. Starting H8 Aer matrix-free on GPU ${H8_GPU} at $(date --iso-8601=seconds)."
run_aer 8 "${H8_GPU}"
H8_STATUS=$?

env PYTHONPATH="${PYTHON_PATH_VALUE}" "${PYTHON_BIN}" "${BENCHMARK}" summarize \
  --raw-dir "${RAW_DIR}" \
  --verification "${RAW_DIR}/H6_state_agreement.json" \
  --output-dir "${OUTPUT_DIR}"
SUMMARY_STATUS=$?

if (( H8_STATUS == 0 && SUMMARY_STATUS == 0 )); then
  printf 'status=complete\ncommit=%s\n' "${SHORT_COMMIT}" > "${OUTPUT_DIR}/COMPLETE"
else
  printf 'status=complete_with_failure\ncommit=%s\n' "${SHORT_COMMIT}" > "${OUTPUT_DIR}/FAILED"
fi
echo "RUN_FINISH $(date --iso-8601=seconds) h8_status=${H8_STATUS} summary_status=${SUMMARY_STATUS}"
exit "$(( H8_STATUS != 0 || SUMMARY_STATUS != 0 ))"
