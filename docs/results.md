# Results and interpretation

The experiment compares operand-buffering strategies while keeping the
compute array, arithmetic, workloads, and host bandwidth fixed. Each
measured result is checked against the independent mathematical reference.

## Cycle counts

The host writes one signed 8-bit operand each clock and accepts one result
each clock, with no deliberate pauses. Bank depth is 16. Counts exclude
command acceptance and include the final accepted result.

| Array | M × K by K × N | Single cycles | Double cycles | Reduction |
|---|---|---:|---:|---:|
| 4×4 | 4×16 by 16×4 | 173 | 173 | 0.0% |
| 4×4 | 6×35 by 35×5 | 1422 | 1230 | 13.5% |
| 4×4 | 8×32 by 32×8 | 1308 | 1212 | 7.3% |
| 2×3 | 4×16 by 16×4 | 440 | 440 | 0.0% |
| 2×3 | 6×35 by 35×5 | 1434 | 1212 | 15.5% |
| 2×3 | 8×32 by 32×8 | 2572 | 2320 | 9.8% |

Reduction = (single cycles - double cycles) / single cycles.
These are cycle-count reductions, not measured physical clock-speed gains.

## Why overlap helps, and why the gain is limited

For the 4×4 6×35 by 35×5 workload, single buffering spends 1132 of 1422
cycles loading operands and acknowledging chunks: 79.6% of the total.
Computation/control uses 260 cycles and result output uses 30.

Double buffering hides part of computation behind those same loads.
It overlaps 184 of 224 scheduler-enabled cycles with a load request.
Total latency falls by 192 cycles; the savings also include shorter
controller handoffs, so they are not identical to the overlap count.
The number of operand writes remains 1120 in both modes.

The input port still transfers only one byte per clock. Two buffers do
not make that port wider, remove padded-bank writes, or avoid reloading
operands for different output tiles. Loading therefore remains dominant.
The one-chunk workload has no next chunk to prefetch and has identical latency.

The array shape also matters. On the 6×5 output, a 2×3 array requires more
tiles but transfers fewer padded operands than 4×4: 1050 versus 1120 writes.
Consequently, 2×3 double mode finishes in 1212 cycles versus 1230 for 4×4,
despite having fewer PEs. On the regular 8×8 output, the 4×4 array is faster.
Array size alone does not determine end-to-end throughput.

## Generic hardware cost

Both designs were synthesized with OSS CAD Suite 2026-10-19,
Yosys 0.70+157 (af9f71e51), slang, and the same generic synthesis/ABC flow.

| Default 4×4, depth16 | Single | Double |
|---|---:|---:|
| Compute PEs | 16 | 16 |
| Logical operand storage bits | 1024 | 2048 |
| Mapped generic cells | 21576 | 23819 |
| Flip-flop bits | 1952 | 3055 |

The second operand set and its selection/control logic increase generic
cell count by 10.4%. The recorded flow maps operand memories into registers
and logic. These counts are not physical area or FPGA LUT/DSP/BRAM counts.

Both frontends report zero errors and warnings; final structural checks
report zero problems. Simulation, lint, and structural synthesis validate
different properties; no post-synthesis equivalence proof is claimed.

## Measurement scope

The testbench's 10 ns clock is a simulation setting, not an achieved
100 MHz hardware frequency. No target library, FPGA device, place-and-route,
physical timing, or power measurement is part of these results.

The cycle comparison establishes that K-chunk overlap reduces latency on
the measured multi-chunk workloads without adding compute PEs. It also
quantifies the cost and demonstrates the input-bandwidth limit.

See [baseline counting definitions](baseline-performance.md),
[double-buffer counters](double-buffering.md), and the recorded
[measurement files](results/) for reproducible evidence. The complete
regression reruns both modes and requires exact agreement with all four
saved JSON snapshots.
