#!/bin/bash
# LSF job: wave-8b switch-value measurement (PEFT multi-adapter vs switch) for one size.
set -uo pipefail
BASE=/proj/dmfexp/eiger/users/jonesn/issue-1679-bench
SIZE="$1"
export HF_HOME=/proj/dmfexp/eiger/users/jonesn/hf_cache
export TRANSFORMERS_CACHE=/proj/dmfexp/eiger/users/jonesn/hf_cache
(cd "$BASE/code/after" && .venv/bin/python -u "$BASE/bench/bench_switchvalue.py" \
   --model "ibm-granite/granite-4.1-${SIZE}" \
   --switch-model "ibm-granite/granite-switch-4.1-${SIZE}-preview" \
   --out "$BASE/results/wave8b/granite-4.1-${SIZE}_switchvalue.json") || echo "W8B $SIZE FAILED"
echo "W8B $SIZE ALL DONE"
