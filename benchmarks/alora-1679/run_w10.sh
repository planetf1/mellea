#!/bin/bash
# LSF job: wave-10 coverage (query_clarification + guardian-core) for one size.
set -uo pipefail
BASE=/proj/dmfexp/eiger/users/jonesn/issue-1679-bench
SIZE="$1"
MODEL="ibm-granite/granite-4.1-${SIZE}"
SWITCH="ibm-granite/granite-switch-4.1-${SIZE}-preview"
export HF_HOME=/proj/dmfexp/eiger/users/jonesn/hf_cache
export TRANSFORMERS_CACHE=/proj/dmfexp/eiger/users/jonesn/hf_cache
run_mode() {
  local code=$1 mode=$2 m=$3
  echo "=== w10 mode=$mode start $(date) ==="
  (cd "$BASE/code/$code" && .venv/bin/python -u "$BASE/bench/bench_coverage.py" \
     --mode "$mode" --model "$m" \
     --out "$BASE/results/wave10/${MODEL//\//_}_${mode}_cov.json") || echo "W10 $mode FAILED"
  echo "=== w10 mode=$mode done $(date) ==="
}
run_mode before base "$MODEL"
run_mode after  lora "$MODEL"
run_mode after  alora "$MODEL"
run_mode switch switch "$SWITCH"
echo "W10 $SIZE ALL DONE"
