#!/bin/bash
# LSF job: wave-5 solving scenarios for one model size, all four judge modes.
# Args: <size: 3b|8b|30b>
set -uo pipefail
BASE=/proj/dmfexp/eiger/users/jonesn/issue-1679-bench
SIZE="$1"
MODEL="ibm-granite/granite-4.1-${SIZE}"
SWITCH="ibm-granite/granite-switch-4.1-${SIZE}-preview"
export HF_HOME=/proj/dmfexp/eiger/users/jonesn/hf_cache
export TRANSFORMERS_CACHE=/proj/dmfexp/eiger/users/jonesn/hf_cache
OUT="$BASE/results/wave5/${MODEL//\//_}_{}.json"
echo "== host: $(hostname) =="
run_mode() {
  local code=$1 mode=$2 m=$3
  echo "=== scen mode=$mode model=$m start $(date) ==="
  (cd "$BASE/code/$code" && .venv/bin/python -u "$BASE/bench/bench_scenarios.py" \
     --mode "$mode" --model "$m" --out "$(echo "$OUT" | sed "s/{}/$mode/")") \
    || echo "SCEN $mode FAILED"
  echo "=== scen mode=$mode done $(date) ==="
}
run_mode before base "$MODEL"
run_mode after  lora "$MODEL"
run_mode after  alora "$MODEL"
run_mode switch switch "$SWITCH"
echo "SCENARIOS $SIZE ALL DONE"
