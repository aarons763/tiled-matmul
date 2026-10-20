# Verification

Run the complete checked configuration set from the repository root:

```bash
bash scripts/regression.sh
```

The regression uses the existing .venv for cocotb and the separately
installed OSS CAD Suite for synthesis. OSS_CAD_ENV can override the suite
environment-file location. Missing dependencies are reported before testing.

## Checks

| Area | Coverage |
|---|---|
| Tool connection | Register smoke test |
| PE | Signed arithmetic, valid combinations, forwarding, clear/reset priority, stalls |
| Array | 2x2 directed schedule and 4x4 reference multiplication |
| Storage | Registered reads, independent bank accesses, valid/data alignment, reset gating |
| Scheduling | 4x4 and 2x3 staggered requests, stalls, completion, restart |
| Single-buffer integration | Tile computation, K chunks, partial tiles, output sequencing |
| Coordinate bounds | DIM_WIDTH=4 output traversal through a 15x15 matrix |
| Host | Invalid commands/destinations, signed extremes, repeat commands, stalls, result backpressure |
| Double buffering | Loader-first, compute-first, same-edge completion, bank ownership, prefetched-buffer stalls |
| Reset | Loading, computation, partial output, partial prefetch, ready prefetch, fresh recovery |
| Performance | Exact reference results, traffic counts, bounded completion, four JSON snapshots |
| Lint | Both modes on all four system configurations, with warnings treated as failures |
| Synthesis | Both full-host modes, generic mapping, final check -assert |

System configurations are 4x4/depth16 and 2x3/depth16, depth1, and depth3.
The ownership controller is also tested separately at depths 1, 3, and 16.

The host workload suite uses seed 763 for reproducible operands, loading
gaps, compute stalls, and result pauses. Cases include K near chunk boundaries,
all -128 operands, mixed -128/127 operands, zeros, and rectangular matrices.
The mathematical reference uses Python integer multiplication independently
of the RTL scheduling implementation.

## Regression behavior and evidence

The complete run passes **34 simulation invocations containing 46 cocotb
tests**, plus eight strict lint configurations, one frontend check, one
four-file performance-snapshot check, and two synthesis checks. This is
46 top-level checks in the script.

Commands execute sequentially because simulations share results.xml.
The runner checks both process status and XML: missing tests, failures,
errors, or skipped cases cause failure. Successful XML files are copied
alongside per-command logs under tests/sim_build/regression/.

All four measured JSON files must exactly match docs/results:
baseline and double-buffer modes for 4x4 and 2x3, at depth 16.
The 10 ns testbench clock and total test duration are not hardware timing
measurements.

## Interpretation

Directed and seeded simulations check behavior on the listed configurations.
Strict lint checks static RTL diagnostics. Generic synthesis establishes
that the selected design elaborates and maps into structural logic without
reported structural errors. These checks are not exhaustive formal
verification or a post-synthesis equivalence proof.

The Icarus 1x1-array configuration aborts during elaboration and is outside
the verified set. This is distinct from multiplying 1x1 matrices, which is
tested using a larger physical array. Full-range M/N/K field values are
interface limits rather than exhaustive workload coverage.
