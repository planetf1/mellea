#!/bin/bash
# LSF job: wave-9 for one size: 112 item-variance probes + growing session.
set -uo pipefail
BASE=/proj/dmfexp/eiger/users/jonesn/issue-1679-bench
SIZE="$1"
MODEL="ibm-granite/granite-4.1-${SIZE}"
SWITCH="ibm-granite/granite-switch-4.1-${SIZE}-preview"
export HF_HOME=/proj/dmfexp/eiger/users/jonesn/hf_cache
export TRANSFORMERS_CACHE=/proj/dmfexp/eiger/users/jonesn/hf_cache
run_mode() {
  local code=$1 mode=$2 m=$3
  echo "=== w9 mode=$mode start $(date) ==="
  (cd "$BASE/code/$code" && .venv/bin/python -u "$BASE/bench/bench_probes.py" \
     --mode "$mode" --probes "$BASE/bench/probes4_full.json" \
     --model "$m" --out "$BASE/results/wave9a/${MODEL//\//_}_${mode}_p4.json") || echo "W9A $mode FAILED"
  (cd "$BASE/code/$code" && .venv/bin/python -u "$BASE/bench/bench_session.py" \
     --mode "$mode" --model "$m" \
     --out "$BASE/results/wave9b/${MODEL//\//_}_${mode}_sess.json") || echo "W9B $mode FAILED"
  echo "=== w9 mode=$mode done $(date) ==="
}
run_mode before base "$MODEL"
run_mode after  lora "$MODEL"
run_mode after  alora "$MODEL"
run_mode switch switch "$SWITCH"
echo "W9 $SIZE ALL DONE"
