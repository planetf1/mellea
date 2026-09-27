#!/bin/bash
# LSF job: wave-8a realistic 149-probe suite for one size, all four arms.
set -uo pipefail
BASE=/proj/dmfexp/eiger/users/jonesn/issue-1679-bench
SIZE="$1"
MODEL="ibm-granite/granite-4.1-${SIZE}"
SWITCH="ibm-granite/granite-switch-4.1-${SIZE}-preview"
export HF_HOME=/proj/dmfexp/eiger/users/jonesn/hf_cache
export TRANSFORMERS_CACHE=/proj/dmfexp/eiger/users/jonesn/hf_cache
OUT="$BASE/results/wave8a/${MODEL//\//_}_{}.json"
run_mode() {
  local code=$1 mode=$2 m=$3
  echo "=== w8a mode=$mode start $(date) ==="
  (cd "$BASE/code/$code" && .venv/bin/python -u "$BASE/bench/bench_probes.py" \
     --mode "$mode" --probes "$BASE/bench/probes3_full.json" \
     --model "$m" --out "$(echo "$OUT" | sed "s/{}/$mode/")") || echo "W8A $mode FAILED"
  echo "=== w8a mode=$mode done $(date) ==="
}
run_mode before base "$MODEL"
run_mode after  lora "$MODEL"
run_mode after  alora "$MODEL"
run_mode switch switch "$SWITCH"
echo "W8A $SIZE ALL DONE"
