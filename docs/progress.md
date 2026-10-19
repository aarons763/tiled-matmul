# Development Progress

## 2026-10-13 — Initial environment and repository setup

- Selected Ubuntu under WSL 2, with VS Code connected through its WSL extension.
- Project location: `/home/aarons763/projects/tiled-matmul`.
- Environment: Ubuntu 26.04.1 LTS, Python 3.14.4, and Git 2.53.0.
- Simulation tools: Icarus Verilog/compiler and vvp runtime 12.0, cocotb 2.1.0.
- Supporting tools: GNU Make 4.4.1 and GTKWave 3.3.126.
- Created `.venv` to isolate Python dependencies and excluded it using `.gitignore`.
- Verified that deactivating `.venv` changes command selection without deleting packages.
- Corrected VS Code opening the Linux folder through Windows PowerShell by reconnecting through WSL.
- Initialized the local repository on `main` and committed the virtual-environment ignore rule.
- Resolved HTTPS authentication failure using GitHub CLI browser login as `aarons763`.
- Pushed commit `7ffdb8e` to `aarons763/tiled-matmul`; local `main` now tracks `origin/main`.
- Tool version checks passed, but no RTL simulation or cocotb integration test has run yet.
- Next milestone: establish and verify a minimal simulation smoke test.

## 2026-10-13 — Register simulation smoke test

- Implemented an 8-bit register with active-high synchronous reset.
- Compiled the RTL with Icarus using SystemVerilog 2012 support without diagnostics.
- Installed Verible v0.0-4296-g0f262651 and configured formatting in VS Code’s WSL settings.
- Connected the RTL and cocotb test using tests/Makefile.
- Ran the simulation from the project root using `make -C tests`.
- Verified initial reset at 5 ns and data capture at 15 ns.
- Verified that asserting reset and changing data at 20 ns leaves the output unchanged.
- Verified reset clears the output at 25 ns, taking priority over nonzero input data.
- Result: 1 test passed, 0 failed; simulation duration was 25 ns.
- Added ignore rules for simulation outputs, Python caches, and waveforms.
- This directed smoke test establishes basic tool integration; it is not accelerator verification.
- Next: document reproducible setup and simulation instructions.

## 2026-10-13 — Fresh-checkout reproduction

- Cloned GitHub into `/home/aarons763/projects/tiled-matmul-setup-check`.
- Created a separate virtual environment using Ubuntu's `/usr/bin/python3`.
- Installed dependencies from `requirements.txt` and ran `make -C tests`.
- Icarus compiled the RTL from scratch; the test passed at 25 ns (1 passed, 0 failed).
- `git status --short` was empty afterward, confirming generated files were ignored.
- This check reused installed Ubuntu tools; it was not a clean-machine reproduction.
- Returned to the original checkout and activated its original `.venv`.
- Recorded initial workflow decisions and open architecture questions.
- Aaron explicitly deferred the repository license decision; no LICENSE file was added. Accelerator architecture is not yet specified.

## 2026-10-13 — Initial processing-element simulation

- Implemented a reusable PE with signed 8-bit operands, a signed 16-bit
  product extended to 32 bits, and a signed 32-bit accumulator.
- Added registered operand/valid forwarding, synchronous reset, global
  step enable, and accumulator clear control.
- Compiled the PE with Icarus using SystemVerilog 2012 and warning checks
  without diagnostics.
- Added a separate PE simulation configuration in tests/Makefile.pe.
- Ran `make -C tests -f Makefile.pe` in the existing virtual environment.
- Result: 1 passed, 0 failed, at 35 ns.
- Verified reset with step disabled, positive-product accumulation,
  forwarding, state retention during a stall with changed inputs, and
  accumulation of a negative product.
- Clear priority, enabled invalid-input behavior, negative accumulator
  results, operand extremes, and broader reset/stall cases remain open.
- This is initial component verification, not full PE or accelerator coverage.

## 2026-10-14 — Expanded PE directed verification

- Ran `make -C tests -f Makefile.pe`: 1 passed, 0 failed, at 205 ns.
- Verified all input-valid combinations, clear priority with forwarding,
  clear held during a stall, reset during a stall, and resumption.
- Verified signed operand boundary products, negative accumulator results,
  valid zero, and accumulation across sign changes.
- Verified all five outputs hold across three consecutive stalled edges
  despite changing input operands and valid bits.
- Three stall failure messages still describe obsolete expected values;
  the assertions correctly expect 11, 12, 0, 0, and -6.
- Directed PE coverage is sufficient to begin array wiring review.
  Randomized verification, overflow policy, and system-level specification
  work remain open; the full accelerator is not verified.

## 2026-10-15 — Array and mathematical reference checks

- Array RTL elaborated at 2x2, 4x4, and 2x3 with Icarus without diagnostics.
- The 2x2 directed test passed at 105 ns, checking intermediate sums,
  two stalled edges, final-result retention, and clear.
- The mathematical reference passed seven known-result checks and 29
  invalid-input checks, including rectangular inputs and signed extremes.
- The schedule-driven reference test passed at 2x2 (55 ns), then at
  4x4 (95 ns) after expanding the input matrices.
- The current reference test uses A[4,3] and B[3,4], verifies all 16
  outputs, and executes nine enabled compute edges without stalls.
- Added tests/Makefile.array4 with its own sim_build/array_4x4 directory.
- Icarus exposes the accumulator output as flattened 32-bit elements;
  Python reads element r * COLS + c.
- These are selected directed workloads, not broad array coverage.
  Randomized workloads, broader K values, and full-array stalls remain open.

## 2026-10-17 — Operand-buffer directed verification

- Operand bank previously passed its depth-16 directed test at 155 ns.
- Operand buffer elaborated with 4 A/4 B banks and 2 A/3 B banks.
- Added a depth-16, 4 A/4 B bank directed test and tests/Makefile.buffer.
- Ran `make -C tests -f Makefile.buffer`: 1 passed, 0 failed, at 115 ns.
- Verified loading while step is disabled, distinct per-bank data,
  mixed read requests, data/valid alignment, two stalled edges, resumption,
  invalid cycles, and independent bank read addresses.
- Verified reset clears asserted valid flags during a stall, suppresses
  attempted writes, and preserves previously loaded memory contents.
- No RTL changes were needed. This checks the buffer in isolation;
  buffer-to-array integration and scheduler timing remain unverified.

## 2026-10-17 — Buffered array integration

- Connected operand_buffer to systolic_array in buffered_array.
- Declared the wrapper's child-driven unpacked data, valid, and result
  connections as wires after diagnosing unknown values at the wrapper
  boundary despite correctly reset child accumulators in Icarus 12.0.
- Added tests/Makefile.buffered and a directed 4x4 integration test.
- Ran `make -C tests -f Makefile.buffered`: 1 passed, 0 failed, at 335 ns.
- Verified loading A rows and B columns, the initial read-only edge,
  first MAC timing, the final MAC edge, and all 16 mathematical results.
- Repeated computation from retained memory after draining and clearing,
  with two two-edge stalls while operands were in flight.
- Verified results hold during stalls and after computation, and clear
  resets all accumulators after draining.
- This checks one K=3 workload with and without stalls. Scheduler RTL,
  tiling, and broader workload verification remain outstanding.

## 2026-10-18 — Read scheduler directed verification

- Corrected bank-index/address separation in combinational read requests.
- Added test_read_scheduler.py and Makefile.scheduler, with separate builds
  for each ROWS/COLS configuration and DEPTH fixed at 16.
- 4x4 test passed at 775 ns; 2x3 test passed at 655 ns (1 test each).
- Checked K=1, 3, and 16; every bank address and enable before acceptance;
  read counts; stalls before first, intermediate, and final advances;
  captured K despite live input changes; ignored starts while busy;
  exact completion timing; one-clock done pulse with step low; reset abort
  and restart.
- The ascending packed k_len range is legal and passed these checks.
- Tests assume legal K values. Hardware enforcement of invalid requests is
  not implemented. Scheduler-to-buffered-array integration remains next.

## 2026-10-18 — Tile engine integration

- Added tile_engine to connect read_scheduler and buffered_array.
- Idle clear overrides start and advances the datapath independently of
  external step; busy clear requests are ignored.
- Writes are accepted only while idle and outside reset. Idle writes may
  coincide with clear or start acceptance; callers should normally load
  before issuing commands. Writes at a busy completion edge are blocked.
- Start preserves sums to support accumulation across K chunks.
- Legal requests require 1 <= k_len <= DEPTH, initialized in-range memory,
  and a one-clock start request; invalid lengths are not checked in RTL.
- Added Makefile.tile and a directed test against the mathematical reference.
- 4x4 passed at 555 ns; 2x3 passed at 465 ns (one test each).
- Checked K=3 workloads, stalls, busy write/clear suppression, latched K,
  completion timing, repeated accumulation, idle clear priority with step
  low, retained operands, and reset abort.
- Broader K coverage at the integrated level, partial tiles, host protocol,
  and tile sequencing remain outstanding.

## 2026-10-18 — Chunk controller

- Added chunk_controller and its clocked protocol documentation.
- Clears once, waits for chunk loading, starts the engine, and retains
  partial sums while requesting subsequent K chunks.
- Added Makefile.chunk and directed tests. Result: 1 passed, 0 failed,
  at 1055 ns, with depth 16.
- Tested K=1,16,17,32,35, delayed acknowledgments, control pulse timing,
  ignored busy starts, and reset abort in all active states.
- Maximum K is checked only for its initial chunk. Real tile-engine
  integration and larger mathematical products remain outstanding.

## 2026-10-18 — Multi-chunk tile computation

- Added chunked_tile_engine, connecting the chunk controller and tile engine
  with loading-only write gating and shared reset.
- Added Makefile.chunked and directed mathematical integration checks for
  K=35,17,1 at bank depth 16, repeated without reset.
- 4x4 passed at 2585 ns; 2x3 passed at 2285 ns (one test each).
- Verified chunk metadata, partial sums after each chunk, final products,
  loading delays, compute stalls, blocked writes outside LOAD, new-operation
  clearing, one-cycle done, and idle result retention.
- The loader remains in the testbench. Output tiling, host loading hardware,
  result storage, and broader verification remain outstanding.

## 2026-10-18 — Output tile controller

- Added output_tile_controller with row-major coordinates, valid region
  counts, and result_valid/result_ready acceptance before advancing.
- Used widened next-boundary arithmetic to avoid coordinate wraparound.
- Added Makefile.output_tile and directed tests: 4x4 and 2x3 builds each
  passed at 1195 ns; DIM_WIDTH=4 boundary build passed at 2255 ns.
- Tested partial and exact output regions, result delays, engine delays,
  captured dimensions, and reset abort.
- Real-engine integration, result storage, and full 6x5, K=35 computation
  remain outstanding; this test supplies engine completion events.

## 2026-10-18 — Full matrix compute sequencing

- Added tiled_matmul to connect output sequencing and chunked computation.
- Captures total K at overall start; exposes matrix-level status, loading
  metadata, and a tile-level result acceptance interface.
- Added Makefile.matmul and complete-result comparison against the reference.
- 4x4 passed at 6435 ns; 2x3 passed at 8545 ns (one test each).
- Verified 6x35 times 35x5, followed by a smaller operation without reset,
  loading delays, compute stalls, partial-tile zero padding, stable results
  during delayed acceptance, and all valid output elements.
- The loader and full-matrix result collector remain testbench components.
  No host interface, result RAM, double buffering, or measured performance
  comparison is provided by this milestone.

## 2026-10-19 — Serialized host interface

- Added matmul_host with command acceptance, dimension validation, a single
  operand write port, and per-element result streaming with global coordinates.
- Writes take priority over loading completion. Result data and coordinates
  hold while the receiver pauses; the final accepted result releases the tile.
- Added Makefile.host, directed tests, and docs/host-interface.md.
- 4x4 passed at 17055 ns; 2x3 passed at 17735 ns (one test each).
- Checked a full 6x35 by 35x5 product, subsequent 1x1 operation, partial tiles,
  multiple K chunks, stalls, backpressure, invalid commands/destinations,
  write/completion priority, and reset during loading.
- The external host supplies matrices and stores results. No system-memory
  transport, software driver, synthesis results, or double buffering is included.
