#!/bin/bash
# LSF job: Granite Switch comparison arm for one model size.
# Args: <size: 3b|8b|30b>
set -euo pipefail
BASE=/proj/dmfexp/eiger/users/jonesn/issue-1679-bench
SIZE="$1"
MODEL="ibm-granite/granite-switch-4.1-${SIZE}-preview"
export HF_HOME=/proj/dmfexp/eiger/users/jonesn/hf_cache
export TRANSFORMERS_CACHE=/proj/dmfexp/eiger/users/jonesn/hf_cache
echo "== host: $(hostname) =="
nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv || true
echo "=== switch model=$MODEL start $(date) ==="
(cd "$BASE/code/switch" && .venv/bin/python -u "$BASE/bench/bench_switch.py" \
   --model "$MODEL" --out "$BASE/results/wave2/${MODEL//\//_}_switch.json")
echo "=== switch model=$MODEL done $(date) ==="
echo "SWITCH $SIZE ALL DONE"
