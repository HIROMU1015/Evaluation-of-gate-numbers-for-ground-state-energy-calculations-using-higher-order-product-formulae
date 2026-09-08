#!/usr/bin/env bash
set -euo pipefail

project_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$project_root"

output_dir=${1:?output directory is required}
h8_gpu=${2:-2}
h9_gpu=${3:-7}
python_bin=/home/AbeHiromu/venvs/trotter-common/bin/python
cupy_site=/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/venv/lib/python3.12/site-packages
m3_dir=artifacts/m3_h8_h9_20260908_a5f9512
wide_point=/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/artifacts/server_direct_cost_landscape_20260905_4058e84/fine_H9_d/direct_1p24.json

if [[ -e "$output_dir" ]]; then
    printf 'Refusing to overwrite existing output: %s\n' "$output_dir" >&2
    exit 2
fi
mkdir -p "$output_dir"

export PYTHONPATH="$cupy_site:src:review_response"
export MPLBACKEND=Agg
export OMP_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export MKL_NUM_THREADS=2

CUDA_VISIBLE_DEVICES="$h8_gpu" "$python_bin" -u \
    review_response/run_m5_h8_h9_same_protocol.py worker \
    --h 8 --gpu "$h8_gpu" \
    --system "$m3_dir/H8.pkl" \
    --output "$output_dir/H8_m5.json" \
    >"$output_dir/H8_m5.log" 2>&1 &
h8_pid=$!

CUDA_VISIBLE_DEVICES="$h9_gpu" "$python_bin" -u \
    review_response/run_m5_h8_h9_same_protocol.py worker \
    --h 9 --gpu "$h9_gpu" \
    --system "$m3_dir/H9.pkl" \
    --output "$output_dir/H9_m5.json" \
    >"$output_dir/H9_m5.log" 2>&1 &
h9_pid=$!

if wait "$h8_pid"; then
    h8_status=0
else
    h8_status=$?
fi
if wait "$h9_pid"; then
    h9_status=0
else
    h9_status=$?
fi

if [[ "$h8_status" -ne 0 || "$h9_status" -ne 0 ]]; then
    printf 'Worker failure: H8=%s H9=%s\n' "$h8_status" "$h9_status" >&2
    exit 3
fi

"$python_bin" review_response/run_m5_h8_h9_same_protocol.py aggregate \
    --h8 "$output_dir/H8_m5.json" \
    --h9 "$output_dir/H9_m5.json" \
    --m3-summary "$m3_dir/summary.json" \
    --wide-time-point "$wide_point" \
    --output "$output_dir/summary.json" \
    --report "$output_dir/report.md" \
    --complete "$output_dir/COMPLETE"
