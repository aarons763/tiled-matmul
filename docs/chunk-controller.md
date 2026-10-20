# Chunk Controller

Sequences one output tile across K chunks using a tile_engine and an
external loader. DEPTH defaults to 16. Total K and the global K offset
are unsigned 17-bit values. Legal requests require 1 <= total_k <= 131071,
1 <= DEPTH <= 131071, and K_WIDTH large enough to represent DEPTH.
Invalid requests are outside this module's contract.

## Clocked protocol

- Reset is synchronous and returns to idle without reporting completion.
  Command outputs are suppressed while reset is asserted. System reset
  must reach the controller and tile engine together.
- Pulse start while idle. The controller captures total_k, ignoring later
  changes and starts while busy. The tile engine must initially be idle.
- CLEAR asserts engine_clear for one full clock, once per output tile.
- LOAD asserts load_req and holds k_offset and chunk_len stable. The loader
  writes chunk_len operands per bank starting at local address zero,
  sourcing global K indices k_offset through k_offset + chunk_len - 1.
- Assert load_done only in response to the current load_req and after all
  writes have completed. Deassert it before the next request. A permanently
  high acknowledgment would incorrectly acknowledge subsequent chunks.
- START asserts engine_start for one full clock. Connect chunk_len to
  tile_engine.k_len.
- WAIT_ENGINE waits for engine_done. Completion advances the offset and
  requests another chunk, or returns idle and pulses done for one clock.
- Connect tile_engine.done to engine_done. Intermediate sums persist:
  later chunks do not assert engine_clear.
- The tile engine's step input handles compute stalls; this controller
  waits for completion and has no separate step input.

Example: K=35 requests (offset, length) = (0,16), (16,16), (32,3).

## Verification

Run make -C tests -f Makefile.chunk in the activated project environment.
At DEPTH=16, the directed test passed at 1055 ns: K=1,16,17,32,35,
loading/engine delays, ignored out-of-phase acknowledgments, one clear
per operation, one-cycle start/done, and reset in every active phase.
The maximum K request is checked only for its initial chunk, not complete
execution. The standalone test supplies loader and engine responses. The integrated
wrapper below checks real computation against the mathematical reference.

## Integrated wrapper

chunked_tile_engine connects this controller to tile_engine. External
step controls computation; the controller and loading handshake continue
independently. The wrapper exposes overall busy/done and gates every bank
write with load_req and not rst. The child engine's busy is not the
operation-level busy signal. Reset must be shared through the wrapper.

The integration testbench supplies operands in response to each request.
matmul_host provides the complete design's serialized operand-write interface. The integration test uses bounded waits
and compares accumulated partial and final results with the mathematical
reference. K=35 exercises offsets 0,16,32 with lengths 16,16,3; K=17 and
K=1 run afterward without reset to check automatic accumulator clearing.
All operations include loading delays and deterministic compute stalls.

Run make -C tests -f Makefile.chunked for 4x4 (passed at 2585 ns), or add
ROWS=2 COLS=3 for 2x3 (passed at 2285 ns), both at depth 16.
This covers one output tile per operation, not output-dimension tiling.
Invalid lengths and addresses are caller errors at this internal interface.
Host-level reset and validation coverage is described in [verification](verification.md).
