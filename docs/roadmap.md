# Development Roadmap

## Current milestone

Setup and fresh-checkout smoke testing are complete. Matrix multiplication,
dot products, and basic array scheduling have been introduced. A reusable
PE has passed its first directed test while the wider accelerator
specification and independent mathematical reference remain open.
Complete PE verification and resolve the remaining specification decisions
before advancing to array integration.

## Planned stages

2. Define the specification, interface table, block diagram, and scheduling
   math after establishing matrix arithmetic and dataflow.
3. Build an independent mathematical reference with explicit integer semantics.
4. Verify one processing element: signed arithmetic, reset/clear priority,
   valid data, forwarding, step enable, and stalls.
5. Verify a 2x2 array, then a 4x4 array; derive staggering and timing from
   actual register placement.
6. Add local memory and scheduling with explicit bandwidth, read latency,
   conflict handling, and stalls.
7. Add output tiling and K chunks, preserving accumulation and handling
   in-flight operands, partial tiles, and bounds.
8. Define host control and result storage with exact acceptance semantics.
9. Verify the full system with deterministic random tests, stalls, timeouts,
   reset/error cases, assertions, and selected formal checks.
10. Run lint, synthesis, and constrained timing; record the target, library,
    corner, memory implementation, and limits of the results.
11. Add double buffering with explicit ownership, safe swaps, and verified
    load/compute overlap.
12. Compare the single-buffer baseline and double-buffer design on identical
    workloads: load, compute, drain, and total cycles; useful MACs;
    utilization with a defined denominator; throughput; traffic; area;
    and timing.
13. Consider FPGA implementation, standard interfaces, scaling, or physical
    implementation based on available resources.
14. Document measured results, tradeoffs, bugs, limitations, and references.

## Initial direction

Compute C[M,N] = A[M,K] * B[K,N] using a planned 4x4 output-stationary
array, signed 8-bit operands, and signed 32-bit accumulators/outputs.
Use one clock domain and a global step enable that freezes the array and
scheduler during stalls. Support local operand storage, rectangular
matrices, and partial edge tiles.

These are goals rather than finalized requirements. Resolve dimension
and capacity limits, maximum K, overflow semantics, reset/error behavior,
host protocol, layout, memory latency, result order, and buffer ownership
before implementation. Do not assume arbitrary K fits a 32-bit accumulator.

The main investigation is how much performance memory scheduling and
buffering can recover without adding compute units. Measure the
single-buffer baseline before implementing double buffering.

## Background reference

[Related Cornell ECE 5760 project](https://people.ece.cornell.edu/land/courses/ece5760/FinalProjects/f2020/bjd86_lgp36/bjd86_lgp36/index.html)
is background reading, not a source of implementation code. Detailed
comparisons require reviewing its design and measurement conditions.
