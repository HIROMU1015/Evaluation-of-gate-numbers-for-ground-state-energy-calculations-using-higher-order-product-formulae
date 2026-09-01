#!/usr/bin/env bash
set -u -o pipefail

STAGE="${1:?stage (pilots or refinements) is required}"
H_CHAIN="${2:?H-chain size is required}"
PHYSICAL_GPU_CSV="${3:?physical GPU list is required}"
OUTPUT_SUBDIR="${4:?output subdirectory is required}"

if [[ "${STAGE}" != "pilots" && "${STAGE}" != "refinements" ]]; then
  echo "ERROR: stage must be pilots or refinements"
  exit 2
fi
if [[ ! "${H_CHAIN}" =~ ^(9|10|11)$ ]]; then
  echo "ERROR: H-chain size must be 9, 10, or 11"
  exit 2
fi
if [[ ! "${PHYSICAL_GPU_CSV}" =~ ^[0-9]+(,[0-9]+)*$ ]]; then
  echo "ERROR: invalid physical GPU list: ${PHYSICAL_GPU_CSV}"
  exit 2
fi
if [[ ! "${OUTPUT_SUBDIR}" =~ ^[A-Za-z0-9._-]+$ ]]; then
  echo "ERROR: invalid output subdirectory: ${OUTPUT_SUBDIR}"
  exit 2
fi
if [[ -n "${CUDA_VISIBLE_DEVICES:-}" ]]; then
  echo "ERROR: inherited CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES}"
  exit 2
fi

PROJECT_ROOT="/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae"
PYTHON_BIN="/home/AbeHiromu/venvs/trotter-common/bin/python"
OUTPUT_DIR="${PROJECT_ROOT}/artifacts/server_cost_validity/${OUTPUT_SUBDIR}"
LOG_DIR="${OUTPUT_DIR}/logs"
MEMORY_DIR="${OUTPUT_DIR}/memory"
TIMING_DIR="${OUTPUT_DIR}/timings"
RUNNER="review_response/run_morales_y8m10b_hchain.py"
ANALYZER="review_response/analyze_h9_h11_gpu_cost.py"
SCHEDULE_JSON="${OUTPUT_DIR}/analytic_schedule.json"

mkdir -p "${LOG_DIR}" "${MEMORY_DIR}" "${TIMING_DIR}"
cd "${PROJECT_ROOT}" || exit 1
exec > >(tee -a "${LOG_DIR}/H${H_CHAIN}.log") 2>&1

IFS=',' read -r -a physical_gpu_ids <<< "${PHYSICAL_GPU_CSV}"
logical_gpu_ids=""
for index in "${!physical_gpu_ids[@]}"; do
  gpu_id="${physical_gpu_ids[${index}]}"
  if ! memory_line="$(timeout 90s nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits -i "${gpu_id}")"; then
    echo "ERROR: nvidia-smi failed for GPU ${gpu_id}"
    exit 2
  fi
  IFS=',' read -r used_mib total_mib <<< "${memory_line}"
  used_mib="${used_mib// /}"
  total_mib="${total_mib// /}"
  if (( used_mib * 2 > total_mib )); then
    echo "ERROR: GPU ${gpu_id} has less than half its memory free"
    exit 2
  fi
  if [[ -n "${logical_gpu_ids}" ]]; then
    logical_gpu_ids+=","
  fi
  logical_gpu_ids+="${index}"
  echo "H${H_CHAIN} ${STAGE}: GPU ${gpu_id} ${used_mib}/${total_mib} MiB used"
done

export CUDA_VISIBLE_DEVICES="${PHYSICAL_GPU_CSV}"
export TROTTER_PROJECT_ROOT="${PROJECT_ROOT}"
export TROTTER_QISKIT_DEVICE=GPU
export TROTTER_QISKIT_AER_METHOD=statevector
export TROTTER_QISKIT_AER_PRECISION=double
export TROTTER_QISKIT_TARGET_GPUS="${logical_gpu_ids}"
export TROTTER_POOL_PROCESSES="${#physical_gpu_ids[@]}"
export MPLBACKEND=Agg
export OMP_NUM_THREADS=4
export OPENBLAS_NUM_THREADS=4
export MKL_NUM_THREADS=4
export PYTHONPATH=src:review_response

run_monitored() {
  local task_id="$1"
  shift
  local monitor_pids=()
  local gpu_id
  for gpu_id in "${physical_gpu_ids[@]}"; do
    nvidia-smi --query-gpu=index,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits -i "${gpu_id}" -lms 1000 > "${MEMORY_DIR}/${task_id}_gpu${gpu_id}.csv" 2> "${MEMORY_DIR}/${task_id}_gpu${gpu_id}.stderr" &
    monitor_pids+=("$!")
  done
  local started
  local finished
  local status
  started="$(date +%s.%N)"
  echo "${task_id} START $(date --iso-8601=seconds)"
  "$@"
  status=$?
  finished="$(date +%s.%N)"
  for monitor_pid in "${monitor_pids[@]}"; do
    if kill -0 "${monitor_pid}" 2>/dev/null; then
      kill "${monitor_pid}" 2>/dev/null || true
    fi
    wait "${monitor_pid}" 2>/dev/null || true
  done
  printf '%s\t%s\t%s\n' "${started}" "${finished}" "${status}" > "${TIMING_DIR}/${task_id}.tsv"
  echo "${task_id} FINISH status=${status} $(date --iso-8601=seconds)"
  return "${status}"
}

run_pilot() {
  local slug="$1"
  local label="$2"
  local t_start="$3"
  local t_stop="$4"
  local run_name="$5"
  run_monitored "H${H_CHAIN}_${slug}_pilot" \
    "${PYTHON_BIN}" "${RUNNER}" \
      --h-chains "${H_CHAIN}" \
      --labels "${label}" \
      --t-start "${t_start}" \
      --t-stop "${t_stop}" \
      --num-times 8 \
      --grid-kind geometric \
      --min-fit-error 5e-12 \
      --output-dir "${OUTPUT_DIR}" \
      --run-name "${run_name}"
}

run_refinement() {
  local slug="$1"
  local label="$2"
  local run_name="$3"
  local times_line
  if ! times_line="$("${PYTHON_BIN}" "${ANALYZER}" emit-times --schedule "${SCHEDULE_JSON}" --h-chain "${H_CHAIN}" --label "${label}")"; then
    echo "H${H_CHAIN} ${label}: refinement skipped by schedule"
    return 0
  fi
  read -r -a include_times <<< "${times_line}"
  local last_index=$(( ${#include_times[@]} - 1 ))
  run_monitored "H${H_CHAIN}_${slug}_refine" \
    "${PYTHON_BIN}" "${RUNNER}" \
      --h-chains "${H_CHAIN}" \
      --labels "${label}" \
      --t-start "${include_times[0]}" \
      --t-stop "${include_times[${last_index}]}" \
      --num-times 2 \
      --grid-kind linear \
      --include-times "${include_times[@]}" \
      --min-fit-error 5e-12 \
      --output-dir "${OUTPUT_DIR}" \
      --run-name "${run_name}"
}

echo "H${H_CHAIN} ${STAGE} START $(date --iso-8601=seconds) CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES} logical=${TROTTER_QISKIT_TARGET_GPUS}"
if [[ "${STAGE}" == "pilots" ]]; then
  run_pilot m5 '4th(m5_best)' 0.15 0.8 h9_h11_m5_pilot || exit 3
  run_pilot y8 '8th(Morales-Y8m10b)' 0.8 1.6 h9_h11_y8_pilot || exit 3
else
  if [[ ! -f "${SCHEDULE_JSON}" ]]; then
    echo "ERROR: schedule is missing: ${SCHEDULE_JSON}"
    exit 4
  fi
  run_refinement m5 '4th(m5_best)' h9_h11_m5_tana || exit 5
  run_refinement y8 '8th(Morales-Y8m10b)' h9_h11_y8_tana || exit 5
fi
echo "H${H_CHAIN} ${STAGE} FINISH $(date --iso-8601=seconds)"
