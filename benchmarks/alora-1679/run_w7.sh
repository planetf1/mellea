#!/bin/bash
# LSF job: wave-7 expanded data for one model size.
# probes2 (79 requirement), policy2 (30, 3 policies), S1 expanded (20 gates).
set -uo pipefail
BASE=/proj/dmfexp/eiger/users/jonesn/issue-1679-bench
SIZE="$1"
MODEL="ibm-granite/granite-4.1-${SIZE}"
SWITCH="ibm-granite/granite-switch-4.1-${SIZE}-preview"
export HF_HOME=/proj/dmfexp/eiger/users/jonesn/hf_cache
export TRANSFORMERS_CACHE=/proj/dmfexp/eiger/users/jonesn/hf_cache
OUT="$BASE/results/wave7/${MODEL//\//_}_{}.json"
run_mode() {
  local code=$1 mode=$2 m=$3
  echo "=== w7 mode=$mode start $(date) ==="
  (cd "$BASE/code/$code" && .venv/bin/python -u "$BASE/bench/bench_probes.py" \
     --mode "$mode" --probes "$BASE/bench/probes2.json" \
     --model "$m" --out "$(echo "$OUT" | sed "s/{}/${mode}_req2/")") || echo "W7 req2 $mode FAILED"
  (cd "$BASE/code/$code" && .venv/bin/python -u "$BASE/bench/bench_probes.py" \
     --mode "$mode" --kind policy --probes "$BASE/bench/policy2.json" \
     --model "$m" --out "$(echo "$OUT" | sed "s/{}/${mode}_pol2/")") || echo "W7 pol2 $mode FAILED"
  echo "=== w7 mode=$mode done $(date) ==="
}
run_mode before base "$MODEL"
run_mode after  lora "$MODEL"
run_mode after  alora "$MODEL"
run_mode switch switch "$SWITCH"
# S1 expanded (certainty gating) — scenario script, S1 only
echo "=== w7 S1-20 start $(date) ==="
for pair in "before base $MODEL" "after lora $MODEL" "after alora $MODEL" "switch switch $SWITCH"; do
  set -- $pair
  (cd "$BASE/code/$1" && .venv/bin/python -u "$BASE/bench/bench_scenarios.py" \
     --mode "$2" --scenarios S1 --model "$3" \
     --out "$BASE/results/wave7/${MODEL//\//_}_${2}_s1_20.json") || echo "W7 s1 $2 FAILED"
done
echo "=== w7 S1-20 done $(date) ==="
echo "W7 $SIZE ALL DONE"
