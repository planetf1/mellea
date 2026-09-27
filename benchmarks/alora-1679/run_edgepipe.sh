#!/bin/bash
# LSF job: wave-7c edges + wave-7d pipelines for one model size, all modes.
set -uo pipefail
BASE=/proj/dmfexp/eiger/users/jonesn/issue-1679-bench
SIZE="$1"
MODEL="ibm-granite/granite-4.1-${SIZE}"
SWITCH="ibm-granite/granite-switch-4.1-${SIZE}-preview"
export HF_HOME=/proj/dmfexp/eiger/users/jonesn/hf_cache
export TRANSFORMERS_CACHE=/proj/dmfexp/eiger/users/jonesn/hf_cache
OUT="$BASE/results/wave7c/${MODEL//\//_}_{}.json"
run_mode() {
  local code=$1 mode=$2 m=$3
  echo "=== edgepipe mode=$mode start $(date) ==="
  (cd "$BASE/code/$code" && .venv/bin/python -u "$BASE/bench/bench_edges.py" \
     --mode "$mode" --model "$m" --out "$BASE/results/wave7c/$(echo "$MODEL" | tr '/' '_')_${mode}_edges.json") || echo "EDGES $mode FAILED"
  (cd "$BASE/code/$code" && .venv/bin/python -u "$BASE/bench/bench_pipeline.py" \
     --mode "$mode" --model "$m" --out "$BASE/results/wave7d/$(echo "$MODEL" | tr '/' '_')_${mode}_pipe.json") || echo "PIPE $mode FAILED"
  echo "=== edgepipe mode=$mode done $(date) ==="
}
run_mode before base "$MODEL"
run_mode after  lora "$MODEL"
run_mode after  alora "$MODEL"
run_mode switch switch "$SWITCH"
echo "EDGEPIPE $SIZE ALL DONE"
