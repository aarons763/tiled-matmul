# Single-buffer baseline measurements

Measured 2026-10-19 using Icarus 12.0 and cocotb 2.1.0.
The test verifies every result against matmul_reference before reporting.
No RTL was changed for measurement.

## Reproduce

From the repository root with the virtual environment active:

```bash
make -C tests -f Makefile.perf
make -C tests -f Makefile.perf ROWS=2 COLS=3
bash scripts/lint.sh
yosys -s scripts/synth-pe.ys
```

The performance tests pass on both configurations. Generated JSON is in
tests/sim_build/baseline_ROWSxCOLS_depthDEPTH.json; recorded snapshots are
in docs/results. Strict lint passes for the four configurations listed below.
Run simulations sequentially because their results.xml is shared.

## Measurement contract

- One operand write per clock, including inactive-bank zero padding.
- step stays high; result_ready stays high.
- No deliberate host delay. Load completion occupies a separate clock
  after the final operand write.
- Count from the edge after command acceptance through the edge accepting
  the final result, inclusive. Reset, command acceptance, and between-job
  idle cycles are excluded.
- Classify each counted edge using signals before that edge: load_req
  means loading; otherwise result_valid means result output; all remaining
  edges are computation/control.
- Computation/control includes pipeline fill/drain and controller overhead;
  it is not a count of active MAC edges.
- Useful MACs = M*N*K. End-to-end utilization = useful MACs divided by
  (ROWS*COLS*total cycles). Padding operations do not count as useful MACs.
- Operand writes count transferred bytes because each write carries one
  signed 8-bit operand; no external bus overhead is modeled.

The test asserts write counts, chunk-completion counts, result counts,
unique coordinates, exact arithmetic, and bounded completion.

## Results

Bank depth is 16 in all rows. Workload notation is M x K by K x N.

| Array | Workload | Load | Compute/control | Output | Total cycles | Useful MAC utilization |
|---|---|---:|---:|---:|---:|---:|
| 4x4 | 4x16 by 16x4 | 129 | 28 | 16 | 173 | 9.25% |
| 4x4 | 6x35 by 35x5 | 1132 | 260 | 30 | 1422 | 4.61% |
| 4x4 | 8x32 by 32x8 | 1032 | 212 | 64 | 1308 | 9.79% |
| 2x3 | 4x16 by 16x4 | 324 | 100 | 16 | 440 | 9.70% |
| 2x3 | 6x35 by 35x5 | 1068 | 336 | 30 | 1434 | 12.20% |
| 2x3 | 8x32 by 32x8 | 1944 | 564 | 64 | 2572 | 13.27% |

Loading dominates this serialized interface. Double buffering can overlap
some loading with computation but cannot increase the one-byte-per-clock
input bandwidth. Partial tiles and repeated loading also affect utilization.
Higher utilization on a smaller array does not necessarily mean lower latency.

These are simulation cycle counts, not hardware timing measurements.
The testbench's 10 ns clock is not evidence of achievable 100 MHz operation.
The double-buffer comparison uses identical workloads, bandwidth, and
clock-count boundaries. Its additional overlap counters are defined in
[double buffering](double-buffering.md).

## Lint and synthesis status

Lint uses Verilator 5.032. PE-only synthesis used system Yosys 0.52;
full-host synthesis uses the tool bundle specified below.

Strict full-host lint now passes without warning-disable flags for 4x4/depth16
and 2x3/depth16, depth1, and depth3. Run parameter overrides with:

```bash
bash scripts/lint.sh -GROWS=2 -GCOLS=3 -GDEPTH=1
```

The original 49 warnings were resolved by explicit sign extension, sized
arithmetic conversions, consistent descending k_len indexing, documented
unused child-busy wires, and final newlines. Narrow address/count conversions
remain guarded by the existing range checks. Result array indices use the
index width, while counters retain their original count width.

The complete [regression](verification.md) checks both buffering modes,
including all four host configurations. Recorded baseline JSON matches
exactly, including all cycle counts.

Generic PE synthesis with scripts/synth-pe.ys passes check -assert with zero
structural problems. Before technology mapping, it reports 1105 generic
cells, including 50 enabled synchronous-reset flip-flops. These counts are
not area, FPGA resource counts, or timing results.

Full-host generic synthesis now passes using OSS CAD Suite 2026-10-19:
Yosys 0.70+157 with the slang frontend. Frontend elaboration reported zero
errors and warnings; final structural checks reported zero problems.
See [the synthesis report](results/host-synthesis.md) for cell statistics,
memory mapping, ABC messages, and interpretation limits.
