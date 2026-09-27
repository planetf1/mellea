#!/bin/bash
# LSF job: wave-3 labeled-probe accuracy eval for one model size, all four
# judge modes (base on pre-fix code, lora/alora on fixed code, switch on the
# embedded model).
# Args: <size: 3b|8b|30b>
set -uo pipefail
BASE=/proj/dmfexp/eiger/users/jonesn/issue-1679-bench
SIZE="$1"
MODEL="ibm-granite/granite-4.1-${SIZE}"
SWITCH="ibm-granite/granite-switch-4.1-${SIZE}-preview"
export HF_HOME=/proj/dmfexp/eiger/users/jonesn/hf_cache
export TRANSFORMERS_CACHE=/proj/dmfexp/eiger/users/jonesn/hf_cache
OUT="$BASE/results/wave3/${MODEL//\//_}_{}.json"
echo "== host: $(hostname) =="
run_mode() {
  local code=$1 mode=$2 m=$3
  echo "=== mode=$mode model=$m start $(date) ==="
  (cd "$BASE/code/$code" && .venv/bin/python -u "$BASE/bench/bench_probes.py" \
     --mode "$mode" --model "$m" --out "$(echo "$OUT" | sed "s/{}/$mode/")") \
    || echo "MODE $mode FAILED"
  echo "=== mode=$mode done $(date) ==="
}
run_mode before base "$MODEL"
run_mode after  lora "$MODEL"
run_mode after  alora "$MODEL"
run_mode switch switch "$SWITCH"
echo "PROBES $SIZE ALL DONE"
