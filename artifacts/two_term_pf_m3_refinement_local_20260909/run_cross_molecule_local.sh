#!/usr/bin/env bash
set -euo pipefail

ROOT=/home/abe/myproject/Evaluation_numGate_highorder
RUNNER_ROOT=/tmp/pf-valid-review-3f47b59
PYTHON="$ROOT/.venv-req/bin/python"
RUNNER="$RUNNER_ROOT/review_response/validate_m3_nonhchain_local.py"
INPUT="$ROOT/artifacts/nonhchain_active_space_local_20260908/inputs"
OUT="$ROOT/artifacts/two_term_pf_m3_refinement_local_20260909/cross_molecule"
FORMULAS="$ROOT/artifacts/two_term_pf_m3_refinement_local_20260909/cross_molecule_formulas.json"

mkdir -p "$OUT"
export PYTHONPATH="$RUNNER_ROOT/src"
export TMPDIR=/tmp
export MPLCONFIGDIR=/tmp/mpl
export OPENBLAS_NUM_THREADS=2
export OMP_NUM_THREADS=2

run_one() {
    local molecule="$1"
    local xyz="$2"
    local active_orbitals="$3"
    local basis="$4"
    local basis_tag="${basis//-/}"
    local output="$OUT/${molecule}_frozen_${basis_tag}_m3_refined.json"
    "$PYTHON" "$RUNNER" \
        --name "${molecule}_frozen_${basis_tag}_m3_refined" \
        --xyz "$xyz" \
        --basis "$basis" \
        --freeze-core 1 \
        --active-orbitals "$active_orbitals" \
        --processes 4 \
        --custom-formulas-json "$FORMULAS" \
        --formulas \
            current_m3 \
            two_term_center \
            m3_two_term_r2_s007 \
            m3_two_term_r2_s027 \
            m3_two_term_r2_s023 \
            m3_two_term_r2_s033 \
            m3_two_term_r2_s009 \
            m3_two_term_r2_s025 \
        --relative-times \
            0.10 0.20 0.30 0.40 0.50 0.60 0.70 \
            0.80 0.90 1.00 1.10 1.20 \
        --output "$output"
}

for basis in sto-3g 6-31g cc-pvdz; do
    run_one lih "$INPUT/lih_reference.xyz" 5 "$basis"
    run_one beh2 "$INPUT/beh2_reference.xyz" 6 "$basis"
    run_one h2o "$INPUT/h2o_qm9_reference.xyz" 6 "$basis"
done

touch "$OUT/COMPUTE_COMPLETE"
