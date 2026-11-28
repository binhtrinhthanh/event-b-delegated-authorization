set -eu
evidence=$1
for i in $(seq -w 1 10); do
  d="$evidence/run-$i"
  mkdir -p "$d"
  python3 implementation/run_experiments.py >"$d/python-main.log" 2>&1
  cp implementation/results/implementation_results.json "$d/"
  python3 implementation/supplement/run_local.py >"$d/python-pilot.log" 2>&1
  cp implementation/supplement/local_results.json "$d/"
  echo "Python/SQLite $i done"
done
