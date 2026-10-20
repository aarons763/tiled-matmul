# Double-buffered K chunks

## Select the implementation

DOUBLE_BUFFER=0 remains the default on matmul_host and tiled_matmul.
DOUBLE_BUFFER=1 selects double_buffered_tile_engine. Both modes keep the
same host ports, matrix arithmetic, output order, operand bandwidth, and
result backpressure behavior.

The new engine contains two operand_buffer instances, one read_scheduler,
and one systolic_array. It doubles operand storage, not the number of MACs.
double_buffer_controller manages bank ownership and independent loading
and computation completion.

## Ownership and scheduling

1. Clear accumulators once at the start of each output tile.
2. Load the first K chunk into buffer 0.
3. Start its computation and request the next chunk into buffer 1.
4. Wait for both the active computation to drain and the next load to finish.
5. Swap read ownership, start the prefetched chunk, and reuse the old buffer
   for the following load.
6. Finish the output tile only after its last chunk drains. Hold all results
   until the host accepts them.

Loading first: next_ready holds the completed buffer until computation ends.
Computation first: WAIT_NEXT holds the drained array until loading ends.
Same-edge completion: the controller accepts both and schedules one swap.
The read bank never changes while its scheduler is active.

The loader's k_offset/chunk_len are separate from engine_k_len. A new load
request can describe chunk n+1 while the scheduler still runs chunk n.
Write enables are gated by load_req and write_bank; active reads go only to
read_bank. The banks differ whenever loading overlaps active computation.
Both buffer-valid pipelines advance with the datapath; unselected reads
are invalid. This prevents stale valid operands replaying after a swap.

step gates computation, not writes or load-complete handshakes. A loader
can fill the next buffer while computation is stalled. Reset aborts both
ownership and computation, clears valid state, and invalidates prefetched
contents; subsequent commands must reload all required locations.

## Host contract changes

No pin changes. The important behavioral change is that load_req can be
high during computation. It identifies only the chunk to load, not the
chunk currently computing. Service requests independently of compute
progress; a host that holds step low throughout loading will lose most
overlap benefits.

Metadata is stable for each outstanding request. Complete all required
writes (including inactive-bank zero padding), then acknowledge loading
on a separate cycle as before. The host cannot select a physical buffer.
Results remain row-major within each tile, with global coordinates.

This implementation overlaps K chunks within an output tile only.
It does not prefetch another output tile while draining results. K <= DEPTH
therefore offers no opportunity for overlap in this design.

## Reproduce

From the repository root with the existing simulation environment active:

```bash
make -C tests -f Makefile.double_controller
make -C tests -f Makefile.double
make -C tests -f Makefile.double ROWS=2 COLS=3
make -C tests -f Makefile.double ROWS=2 COLS=3 DEPTH=1
make -C tests -f Makefile.double ROWS=2 COLS=3 DEPTH=3
make -C tests -f Makefile.perf
make -C tests -f Makefile.perf_double
bash scripts/lint.sh -GDOUBLE_BUFFER=1
```

Both performance makefiles also accept ROWS=2 COLS=3. Baseline Makefile.host
and Makefile.matmul continue to select the original implementation.

For generic synthesis in the verified suite environment:

```bash
(
  source "$HOME/tools/cad-20261019/oss-cad-suite/environment"
  yosys -s scripts/synth-double.ys
)
```

## Verification evidence

- Three host tests pass on 4x4/depth16 (73785 ns), 2x3/depth16 (56395 ns),
  2x3/depth1 (39555 ns), and 2x3/depth3 (36175 ns).
- The regular host test now permits computation during writes in double
  mode, with reproducible operand values, loading gaps, and compute stalls.
- Dedicated prefetch tests reset with a partially written buffer and with
  a full next buffer waiting on stalled computation. Both are followed by
  successful multi-chunk recovery. A separate ready-buffer case stalls for
  five cycles and resumes to a correct result without reset.
- Controller tests pass at depths 1, 3, and 16 (785 ns each), explicitly
  checking loader-first, engine-first, and same-edge completion, chunk
  lengths, bank alternation, one clear, and final completion.
- Strict lint passes in both modes for all four configurations, with no
  warning-disable flags.
- Legacy host tests pass on 4x4 and 2x3, and the legacy matrix test passes.
  Both baseline performance JSON outputs exactly match the saved snapshots.
- Both performance tests check every result, write counts, chunk counts,
  and completion. Double mode additionally counts scheduler-enabled edges
  and proves nonzero load/compute overlap on multi-chunk workloads.

These are directed and seeded simulation checks plus structural synthesis,
not exhaustive verification or post-synthesis equivalence. The pre-existing
Icarus 1x1-array elaboration failure excludes that configuration from the verified set.

## Performance comparison

Depth is 16. The host sends one operand per clock without deliberate pauses
and accepts one result per clock. Matrices, arithmetic reference, bandwidth,
and clock-count boundaries are identical between modes.

| Array | M x K by K x N | Single cycles | Double cycles | Cycle reduction |
|---|---|---:|---:|---:|
| 4x4 | 4x16 by 16x4 | 173 | 173 | 0.0% |
| 4x4 | 6x35 by 35x5 | 1422 | 1230 | 13.5% |
| 4x4 | 8x32 by 32x8 | 1308 | 1212 | 7.3% |
| 2x3 | 4x16 by 16x4 | 440 | 440 | 0.0% |
| 2x3 | 6x35 by 35x5 | 1434 | 1212 | 15.5% |
| 2x3 | 8x32 by 32x8 | 2572 | 2320 | 9.8% |

Cycle reduction is (single - double) / single. These are cycle improvements,
not measured wall-clock hardware speedups; maximum frequency is unknown.

The existing exclusive counters classify loading first, result output
second, and all other cycles as compute_control. In double mode, overlapped
computation is included in load, so compute_control is only the remainder,
not total computation. New counters report:

- scheduler_enabled_cycles: all cycles advancing the read/compute pipeline;
- load_compute_overlap: those enabled cycles with load_req also high.

For the 4x4 K=35 workload, 184 of 224 scheduler-enabled cycles overlap a
load request. The shortened controller handoff also saves cycles, so total
savings need not equal the overlap count. Operand traffic is unchanged.

Snapshots are in results/double_4x4_depth16.json and
results/double_2x3_depth16.json; baseline snapshots remain unchanged.

## Generic hardware comparison

Both runs use OSS CAD Suite 2026-10-19, Yosys 0.70+157 (af9f71e51), and the
same generic synth/ABC flow. Frontends report zero errors and warnings;
final structural checks report zero problems.

| Default 4x4, depth16 | Single | Double |
|---|---:|---:|
| Logical operand storage bits | 1024 | 2048 |
| Mapped generic cells | 21576 | 23819 |
| Flip-flop bits | 1952 | 3055 |

Generic cell count increases by 10.4%. Both runs map operand memories to
registers and logic. These figures are not physical area or FPGA LUT,
DSP, or BRAM estimates. A target-specific implementation may map them
differently. Detailed statistics are in results/double-synthesis.md.

## Evaluation scope

The comparison covers simulation cycles and generic synthesis, with no
target-specific physical timing, area, or power claim. It demonstrates the
bandwidth limit: overlap helps, but does not increase one-byte-per-clock
input bandwidth or remove repeated and padded operand traffic.
