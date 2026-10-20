# Implementation and verification record

This record summarizes the completed simulation-and-generic-synthesis
project. Commands and detailed coverage are in [verification](verification.md);
measurements and interpretation are in [results](results.md).

| Date | Completed evidence |
|---|---|
| 2026-10-13 | WSL environment, register smoke test, and fresh-checkout smoke reproduction |
| 2026-10-13–14 | Signed PE arithmetic, forwarding, control priority, and stall tests |
| 2026-10-15 | PE-array integration and independent matrix reference checks |
| 2026-10-17 | Operand banks, valid/data alignment, and buffered-array integration |
| 2026-10-18 | Read scheduling, K-chunk accumulation, output tiling, and full-matrix simulation |
| 2026-10-19 | Serialized host interface, invalid-input checks, and reset/recovery tests |
| 2026-10-19 | Strict lint cleanup and reproducible baseline cycle measurements |
| 2026-10-19 | Full-host generic synthesis using the installed slang frontend |
| 2026-10-19 | Double-buffer ownership, concurrent K-chunk loading, and reset/stall verification |
| 2026-10-19 | Same-bandwidth comparison, architecture documentation, and complete regression |

## Recorded comparison

For the default 4x4/depth16 configuration, the 6x35 by 35x5 workload uses
1422 cycles with single buffering and 1230 with double buffering, a 13.5%
reduction. Generic mapped cells are 21576 and 23819 respectively, a 10.4%
increase. Both modes retain 16 compute PEs.

Saved baseline JSON snapshots match the rerun exactly. All result elements
in measurement tests match the independent mathematical reference.

## Final regression evidence

The complete regression passes 34 simulation runs (46 cocotb tests), eight
lint configurations, four performance snapshots, frontend loading, and
both full-host synthesis checks. Logs and test XML are written to
tests/sim_build/regression/.

The scope is RTL simulation, static lint, and generic synthesis. Physical
timing, device-specific resource use, and power are not measured.
