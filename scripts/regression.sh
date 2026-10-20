#!/usr/bin/env bash
# Run from any directory. Simulation and synthesis environments stay separate.
set -euo pipefail
cd "$(dirname "$0")/.."
project_root="$PWD"
cad_environment="${OSS_CAD_ENV:-$HOME/tools/cad-20261019/oss-cad-suite/environment}"

if [[ ! -f .venv/bin/activate ]]; then
    echo "Missing .venv. See README.md for the simulation environment." >&2
    exit 1
fi
if [[ ! -f "$cad_environment" ]]; then
    echo "Missing synthesis environment: $cad_environment" >&2
    echo "Set OSS_CAD_ENV to the suite environment file; see docs/synthesis-setup.md." >&2
    exit 1
fi
source .venv/bin/activate
for command_name in python make iverilog vvp verilator cocotb-config; do
    command -v "$command_name" >/dev/null || {
        echo "Missing required tool: $command_name" >&2
        exit 1
    }
done
log_dir="$project_root/tests/sim_build/regression"
mkdir -p "$log_dir"
checks=0
simulations=0

run_check() {
    local label="$1"
    shift
    printf '%s ... ' "$label"
    if "$@" >"$log_dir/$label.log" 2>&1; then
        printf 'PASS\n'
        checks=$((checks + 1))
    else
        printf 'FAIL\n'
        tail -n 40 "$log_dir/$label.log"
        echo "Full log: $log_dir/$label.log" >&2
        exit 1
    fi
}

run_sim() {
    local label="$1"
    local makefile="$2"
    shift 2
    run_check "$label" make -C tests -f "$makefile" "$@"
    # Check the XML as well: a successful process alone is not test evidence.
    python - <<'PY'
from pathlib import Path
import xml.etree.ElementTree as ET

path = Path("tests/results.xml")
root = ET.parse(path).getroot()
cases = list(root.iter("testcase"))
assert cases, "No test cases in results.xml"
bad = [case.get("name") for case in cases
       if any(case.find(tag) is not None for tag in ("failure", "error", "skipped"))]
assert not bad, f"Failed or skipped test cases: {bad}"
PY
    cp tests/results.xml "$log_dir/$label.xml"
    simulations=$((simulations + 1))
}

run_check synthesis-frontend bash -c 'source "$1"; yosys -V; yosys -Q -T -m slang -p "help read_slang"' _ "$cad_environment"

for mode in 0 1; do
    run_check "lint-db$mode-4x4-d16" bash scripts/lint.sh "-GDOUBLE_BUFFER=$mode"
    for depth in 16 1 3; do
        run_check "lint-db$mode-2x3-d$depth" bash scripts/lint.sh "-GDOUBLE_BUFFER=$mode" -GROWS=2 -GCOLS=3 "-GDEPTH=$depth"
    done
done

run_sim smoke Makefile
for component in pe array array4 bank buffer buffered chunk; do
    run_sim "$component" "Makefile.$component"
done
for component in scheduler tile chunked output_tile matmul; do
    run_sim "$component-4x4" "Makefile.$component"
    run_sim "$component-2x3" "Makefile.$component" ROWS=2 COLS=3
done
run_sim output-coordinate-boundary Makefile.output_tile DIM_WIDTH=4

for mode in host double; do
    run_sim "$mode-4x4-d16" "Makefile.$mode"
    for depth in 16 1 3; do
        run_sim "$mode-2x3-d$depth" "Makefile.$mode" ROWS=2 COLS=3 "DEPTH=$depth"
    done
done
for depth in 16 1 3; do
    run_sim "ownership-d$depth" Makefile.double_controller "DEPTH=$depth"
done
for mode in perf perf_double; do
    run_sim "$mode-4x4" "Makefile.$mode"
    run_sim "$mode-2x3" "Makefile.$mode" ROWS=2 COLS=3
done

run_check performance-snapshots python - <<'PY'
from pathlib import Path
import json

for mode in ("baseline", "double"):
    for shape in ("4x4", "2x3"):
        name = f"{mode}_{shape}_depth16.json"
        actual = json.loads((Path("tests/sim_build") / name).read_text())
        expected = json.loads((Path("docs/results") / name).read_text())
        assert actual == expected, f"Performance snapshot changed: {name}"
        print(f"{name}: exact match")
PY

run_check synthesis-single bash -c 'source "$1"; exec yosys -s scripts/synth-host.ys' _ "$cad_environment"
run_check synthesis-double bash -c 'source "$1"; exec yosys -s scripts/synth-double.ys' _ "$cad_environment"
printf '\nRegression passed: %s simulation runs; %s total checks.\nLogs: %s\n' "$simulations" "$checks" "$log_dir"
