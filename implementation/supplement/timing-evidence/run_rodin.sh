set -eu
rodin=$1
ecj=$2
evidence=$3
workspace_root=$4
timed_source=implementation/supplement/additional_evaluation/tools/headless/src/delegated/BuildDelegation.java
cp "$timed_source" tools/headless/src/delegated/BuildDelegation.java
mkdir -p "$workspace_root"
for i in $(seq -w 1 10); do
  d="$evidence/run-$i"
  mkdir -p "$d"
  work=$(mktemp -d "$workspace_root/rodin-$i-XXXXXX")
  python3 tools/run_rodin.py --rodin "$rodin" --work "$work" --ecj "$ecj" >"$d/rodin-driver.log" 2>&1
  cp "$work/rodin_native.log" "$d/"
  python3 tools/collect_evidence.py --workspace-project "$work/workspace/DelegatedAuthorization" --native-log "$work/rodin_native.log" >"$d/rodin-summary.json"
  cmp validation/po_inventory.csv validation/rodin_clean_replay/po_inventory.csv
  cp validation/po_inventory.csv "$d/rodin-po-inventory.csv"
  echo "Rodin $i done"
done
