#!/bin/bash
# LSF job: run the aLoRA before/middle/after arms for one model size.
# Args: <size: 3b|8b|30b>
set -euo pipefail
BASE=/proj/dmfexp/eiger/users/jonesn/issue-1679-bench
SIZE="$1"
MODEL="ibm-granite/granite-4.1-${SIZE}"
export HF_HOME=/proj/dmfexp/eiger/users/jonesn/hf_cache
export TRANSFORMERS_CACHE=/proj/dmfexp/eiger/users/jonesn/hf_cache
OUT="$BASE/results/wave2/${MODEL//\//_}_{}.json"
echo "== host: $(hostname) =="
nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv || true
for arm in before middle after; do
  echo "=== arm=$arm model=$MODEL start $(date) ==="
  (cd "$BASE/code/$arm" && .venv/bin/python -u "$BASE/bench/bench_alora.py" \
     --arm "$arm" --model "$MODEL" --out "$(echo "$OUT" | sed "s/{}/$arm/")")
  echo "=== arm=$arm model=$MODEL done $(date) ==="
done
echo "MODEL $SIZE ALL DONE"
