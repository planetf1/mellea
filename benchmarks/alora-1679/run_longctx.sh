#!/bin/bash
# LSF job: wave-7a long-context study for one model size, all four modes.
set -uo pipefail
BASE=/proj/dmfexp/eiger/users/jonesn/issue-1679-bench
SIZE="$1"
MODEL="ibm-granite/granite-4.1-${SIZE}"
SWITCH="ibm-granite/granite-switch-4.1-${SIZE}-preview"
export HF_HOME=/proj/dmfexp/eiger/users/jonesn/hf_cache
export TRANSFORMERS_CACHE=/proj/dmfexp/eiger/users/jonesn/hf_cache
OUT="$BASE/results/wave7a/${MODEL//\//_}_{}.json"
run_mode() {
  local code=$1 mode=$2 m=$3
  echo "=== longctx mode=$mode start $(date) ==="
  (cd "$BASE/code/$code" && .venv/bin/python -u "$BASE/bench/bench_longctx.py" \
     --mode "$mode" --model "$m" --out "$(echo "$OUT" | sed "s/{}/$mode/")") \
    || echo "LONGCTX $mode FAILED"
  echo "=== longctx mode=$mode done $(date) ==="
}
run_mode before base "$MODEL"
run_mode after  lora "$MODEL"
run_mode after  alora "$MODEL"
run_mode switch switch "$SWITCH"
echo "LONGCTX $SIZE ALL DONE"
