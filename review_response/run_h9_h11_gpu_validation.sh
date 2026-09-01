#!/usr/bin/env bash
set -u -o pipefail

GPU_H9="${1:?physical GPU list for H9 is required}"
GPU_H10="${2:?physical GPU list for H10 is required}"
GPU_H11="${3:?physical GPU list for H11 is required}"
OUTPUT_SUBDIR="${4:-h9_h11_gpu}"

if [[ ! "${OUTPUT_SUBDIR}" =~ ^[A-Za-z0-9._-]+$ ]]; then
  echo "ERROR: invalid output subdirectory: ${OUTPUT_SUBDIR}"
  exit 2
fi

PROJECT_ROOT="/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae"
PYTHON_BIN="/home/AbeHiromu/venvs/trotter-common/bin/python"
OUTPUT_DIR="${PROJECT_ROOT}/artifacts/server_cost_validity/${OUTPUT_SUBDIR}"
LOG_DIR="${OUTPUT_DIR}/logs"
MEMORY_DIR="${OUTPUT_DIR}/memory"
TIMING_DIR="${OUTPUT_DIR}/timings"
MAIN_LOG="${LOG_DIR}/h9_h11_gpu_master.log"
SCHEDULE_JSON="${OUTPUT_DIR}/analytic_schedule.json"
SUMMARY_JSON="${OUTPUT_DIR}/summary.json"
README_PATH="${OUTPUT_DIR}/README.md"
COMPLETE_PATH="${OUTPUT_DIR}/COMPLETE"
RUNNER="review_response/run_morales_y8m10b_hchain.py"
ANALYZER="review_response/analyze_h9_h11_gpu_cost.py"

mkdir -p "${LOG_DIR}" "${MEMORY_DIR}" "${TIMING_DIR}"
cd "${PROJECT_ROOT}" || exit 1

expected_outputs=(
  "${MAIN_LOG}"
  "${SCHEDULE_JSON}"
  "${SUMMARY_JSON}"
  "${README_PATH}"
  "${COMPLETE_PATH}"
)
for h_chain in 9 10 11; do
  expected_outputs+=(
    "${OUTPUT_DIR}/H${h_chain}_h9_h11_m5_pilot.json"
    "${OUTPUT_DIR}/H${h_chain}_h9_h11_y8_pilot.json"
    "${OUTPUT_DIR}/H${h_chain}_h9_h11_m5_tana.json"
    "${OUTPUT_DIR}/H${h_chain}_h9_h11_y8_tana.json"
    "${LOG_DIR}/H${h_chain}.log"
  )
done
for target in "${expected_outputs[@]}"; do
  if [[ -e "${target}" ]]; then
    echo "ERROR: refusing to overwrite ${target}"
    exit 2
  fi
done

exec > >(tee -a "${MAIN_LOG}") 2>&1

if [[ -n "${CUDA_VISIBLE_DEVICES:-}" ]]; then
  echo "ERROR: inherited CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES}; refusing to replace scheduler allocation"
  exit 2
fi

declare -A ASSIGNED_GPUS=()
validate_gpu_list() {
  local h_chain="$1"
  local gpu_csv="$2"
  if [[ ! "${gpu_csv}" =~ ^[0-9]+(,[0-9]+)*$ ]]; then
    echo "ERROR: invalid H${h_chain} GPU list: ${gpu_csv}"
    return 1
  fi
  local gpu_id
  IFS=',' read -r -a gpu_ids <<< "${gpu_csv}"
  for gpu_id in "${gpu_ids[@]}"; do
    if [[ -n "${ASSIGNED_GPUS[${gpu_id}]:-}" ]]; then
      ASSIGNED_GPUS["${gpu_id}"]+=",H${h_chain}"
    else
      ASSIGNED_GPUS["${gpu_id}"]="H${h_chain}"
    fi
  done
}

validate_gpu_list 9 "${GPU_H9}" || exit 2
validate_gpu_list 10 "${GPU_H10}" || exit 2
validate_gpu_list 11 "${GPU_H11}" || exit 2

echo "START $(date --iso-8601=seconds)"
echo "GPU allocations: H9=${GPU_H9} H10=${GPU_H10} H11=${GPU_H11}"
echo "Python: ${PYTHON_BIN}"
echo "Output: ${OUTPUT_DIR}"

for gpu_id in "${!ASSIGNED_GPUS[@]}"; do
  if ! memory_line="$(timeout 90s nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits -i "${gpu_id}")"; then
    echo "ERROR: nvidia-smi failed for GPU ${gpu_id}"
    exit 2
  fi
  IFS=',' read -r used_mib total_mib <<< "${memory_line}"
  used_mib="${used_mib// /}"
  total_mib="${total_mib// /}"
  if [[ ! "${used_mib}" =~ ^[0-9]+$ || ! "${total_mib}" =~ ^[0-9]+$ ]]; then
    echo "ERROR: could not parse GPU ${gpu_id} memory: ${memory_line}"
    exit 2
  fi
  if (( used_mib * 2 > total_mib )); then
    echo "ERROR: GPU ${gpu_id} has less than half its memory free"
    exit 2
  fi
  echo "GPU ${gpu_id} assigned to ${ASSIGNED_GPUS[${gpu_id}]}: ${used_mib}/${total_mib} MiB used"
  if ! timeout 90s env CUDA_VISIBLE_DEVICES="${gpu_id}" PYTHONPATH=src "${PYTHON_BIN}" -c "import trotterlib.qiskit_time_evolution_utils as u; print('devices=',u.available_aer_devices()); from qiskit import QuantumCircuit; from qiskit_aer import AerSimulator; import numpy as np; qc=QuantumCircuit(2); qc.h(0); qc.cx(0,1); qc.save_statevector(); result=AerSimulator(method='statevector',device='GPU',precision='double',fusion_enable=False).run(qc).result(); state=np.asarray(result.get_statevector(qc)); assert result.success and np.isclose(np.linalg.norm(state),1.0); print('gpu_smoke_success=',result.success)"; then
    echo "ERROR: Aer GPU smoke failed on physical GPU ${gpu_id}"
    exit 2
  fi
done

PYTHONPATH=src "${PYTHON_BIN}" -c "import importlib.metadata as m,sys; print('python',sys.version); print('qiskit',m.version('qiskit')); print('qiskit-aer-gpu',m.version('qiskit-aer-gpu')); print('pyscf',m.version('pyscf')); print('numpy',m.version('numpy')); print('scipy',m.version('scipy'))" || exit 2
nvidia-smi

configure_chain_environment() {
  local gpu_csv="$1"
  local logical_ids=""
  local index
  IFS=',' read -r -a chain_gpu_ids <<< "${gpu_csv}"
  export CUDA_VISIBLE_DEVICES="${gpu_csv}"
  export TROTTER_POOL_PROCESSES="${#chain_gpu_ids[@]}"
  if (( ${#chain_gpu_ids[@]} > 1 )); then
    for index in "${!chain_gpu_ids[@]}"; do
      if [[ -n "${logical_ids}" ]]; then
        logical_ids+=","
      fi
      logical_ids+="${index}"
    done
    export TROTTER_QISKIT_TARGET_GPUS="${logical_ids}"
  else
    unset TROTTER_QISKIT_TARGET_GPUS
  fi
  export TROTTER_PROJECT_ROOT="${PROJECT_ROOT}"
  export TROTTER_QISKIT_DEVICE=GPU
  export TROTTER_QISKIT_AER_METHOD=statevector
  export TROTTER_QISKIT_AER_PRECISION=double
  export MPLBACKEND=Agg
  export OMP_NUM_THREADS=4
  export OPENBLAS_NUM_THREADS=4
  export MKL_NUM_THREADS=4
  export PYTHONPATH=src:review_response
}

run_monitored() {
  local task_id="$1"
  local gpu_csv="$2"
  shift 2
  local monitor_pids=()
  local gpu_id
  IFS=',' read -r -a monitored_gpu_ids <<< "${gpu_csv}"
  for gpu_id in "${monitored_gpu_ids[@]}"; do
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
  local h_chain="$1"
  local gpu_csv="$2"
  local slug="$3"
  local label="$4"
  local t_start="$5"
  local t_stop="$6"
  local run_name="$7"
  local command=(
    "${PYTHON_BIN}" "${RUNNER}"
    --h-chains "${h_chain}"
    --labels "${label}"
    --t-start "${t_start}"
    --t-stop "${t_stop}"
    --num-times 8
    --grid-kind geometric
    --min-fit-error 5e-12
    --output-dir "${OUTPUT_DIR}"
    --run-name "${run_name}"
  )
  run_monitored "H${h_chain}_${slug}_pilot" "${gpu_csv}" "${command[@]}"
}

run_chain_pilots() {
  local h_chain="$1"
  local gpu_csv="$2"
  configure_chain_environment "${gpu_csv}"
  echo "H${h_chain} pilot environment CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES} TARGET_GPUS=${TROTTER_QISKIT_TARGET_GPUS:-<unset>} processes=${TROTTER_POOL_PROCESSES}"
  run_pilot "${h_chain}" "${gpu_csv}" m5 '4th(m5_best)' 0.15 0.8 h9_h11_m5_pilot || return 1
  run_pilot "${h_chain}" "${gpu_csv}" y8 '8th(Morales-Y8m10b)' 0.8 1.6 h9_h11_y8_pilot
}

run_refinement() {
  local h_chain="$1"
  local gpu_csv="$2"
  local slug="$3"
  local label="$4"
  local run_name="$5"
  local times_line
  if ! times_line="$(PYTHONPATH=src "${PYTHON_BIN}" "${ANALYZER}" emit-times --schedule "${SCHEDULE_JSON}" --h-chain "${h_chain}" --label "${label}")"; then
    echo "H${h_chain} ${label}: refinement skipped by schedule"
    return 0
  fi
  read -r -a include_times <<< "${times_line}"
  local last_index=$(( ${#include_times[@]} - 1 ))
  local command=(
    "${PYTHON_BIN}" "${RUNNER}"
    --h-chains "${h_chain}"
    --labels "${label}"
    --t-start "${include_times[0]}"
    --t-stop "${include_times[${last_index}]}"
    --num-times 2
    --grid-kind linear
    --include-times "${include_times[@]}"
    --min-fit-error 5e-12
    --output-dir "${OUTPUT_DIR}"
    --run-name "${run_name}"
  )
  run_monitored "H${h_chain}_${slug}_refine" "${gpu_csv}" "${command[@]}"
}

run_chain_refinements() {
  local h_chain="$1"
  local gpu_csv="$2"
  configure_chain_environment "${gpu_csv}"
  echo "H${h_chain} refinement environment CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES} TARGET_GPUS=${TROTTER_QISKIT_TARGET_GPUS:-<unset>} processes=${TROTTER_POOL_PROCESSES}"
  run_refinement "${h_chain}" "${gpu_csv}" m5 '4th(m5_best)' h9_h11_m5_tana || return 1
  run_refinement "${h_chain}" "${gpu_csv}" y8 '8th(Morales-Y8m10b)' h9_h11_y8_tana
}

echo "PILOT STAGE START $(date --iso-8601=seconds)"
pilot_failed=0
if ! run_chain_pilots 9 "${GPU_H9}" > >(tee -a "${LOG_DIR}/H9.log") 2>&1; then
  pilot_failed=1
fi
if ! run_chain_pilots 10 "${GPU_H10}" > >(tee -a "${LOG_DIR}/H10.log") 2>&1; then
  pilot_failed=1
fi
if ! run_chain_pilots 11 "${GPU_H11}" > >(tee -a "${LOG_DIR}/H11.log") 2>&1; then
  pilot_failed=1
fi
if (( pilot_failed != 0 )); then
  echo "ERROR: at least one pilot worker failed; refinement will not start"
  exit 3
fi

echo "PLAN STAGE START $(date --iso-8601=seconds)"
plan_args=(
  plan
  --output-dir "${OUTPUT_DIR}"
  --schedule "${SCHEDULE_JSON}"
  --noise-floor 5e-12
  --window-sizes 4 5 6
  --epsilon-e 1.5936001019904e-4
  --max-time 10.0
)
PYTHONPATH=src "${PYTHON_BIN}" "${ANALYZER}" "${plan_args[@]}" || exit 4

echo "REFINEMENT STAGE START $(date --iso-8601=seconds)"
refine_failed=0
if ! run_chain_refinements 9 "${GPU_H9}" >> "${LOG_DIR}/H9.log" 2>&1; then
  refine_failed=1
fi
if ! run_chain_refinements 10 "${GPU_H10}" >> "${LOG_DIR}/H10.log" 2>&1; then
  refine_failed=1
fi
if ! run_chain_refinements 11 "${GPU_H11}" >> "${LOG_DIR}/H11.log" 2>&1; then
  refine_failed=1
fi
if (( refine_failed != 0 )); then
  echo "ERROR: at least one refinement worker failed"
  exit 5
fi

echo "FINALIZE STAGE START $(date --iso-8601=seconds)"
finalize_args=(
  finalize
  --output-dir "${OUTPUT_DIR}"
  --schedule "${SCHEDULE_JSON}"
  --summary "${SUMMARY_JSON}"
  --readme "${README_PATH}"
  --complete "${COMPLETE_PATH}"
  --beta 1.2
  --epsilon-e 1.5936001019904e-4
)
PYTHONPATH=src "${PYTHON_BIN}" "${ANALYZER}" "${finalize_args[@]}" || exit 6

echo "FINISH $(date --iso-8601=seconds)"
