# Tiled Matrix Multiplication Interface

tiled_matmul connects output_tile_controller to the selected chunk engine:
chunked_tile_engine for DOUBLE_BUFFER=0 or double_buffered_tile_engine
for DOUBLE_BUFFER=1. The default is 0.
It captures total_k on an idle start acceptance edge. The output controller
captures M and N on that same edge. Overall busy/done refer to the complete
matrix operation, not one chunk or output tile.

## Command and loading contract

- Pulse start while idle with nonzero m_len, n_len, and total_k.
- M and N must fit DIM_WIDTH (default 16); 1 <= total_k <= 131071.
- Invalid dimensions, addresses, or incomplete loads are caller errors;
  this internal interface has no error response or hardware bounds validation.
  matmul_host validates commands and serialized write destinations.
- The synchronous reset must initialize the complete hierarchy before use.
  Reset aborts the operation without normal completion.
- step freezes compute progress but not command, loading, or result
  handshakes. A paused computation cannot complete until step resumes.
- On load_req, load chunk_len entries per bank at addresses 0 onward.
  A bank r receives A[tile_row+r][k_offset+k]; B bank c receives
  B[k_offset+k][tile_col+c]. Supply zero for rows/columns outside M/N.
- Write enables are accepted only while load_req is high and reset is low.
- Pulse load_done after the final write has completed; clear it before
  acknowledging another request. Loading is still performed externally.

## Results

When result_valid is high, acc_outputs contains one completed tile.
Only valid_rows by valid_cols elements belong to the output matrix.
The receiver captures these elements and tile coordinates at a rising
edge where result_valid and result_ready are both high. The entire
tile is acknowledged at once; a receiver reading elements serially must
wait until all valid elements are copied before raising result_ready.
The next tile cannot start until this acknowledgment. The final accepted
tile lowers busy and produces a one-clock done pulse.

Accumulator outputs and coordinates are only meaningful as completed
results while result_valid is asserted. There is no whole-matrix result
RAM or serialized host interface in this module.

## Verification

make -C tests -f Makefile.matmul passed at 6435 ns (4x4).
The same command with ROWS=2 COLS=3 passed at 8545 ns.
The test multiplies 6x35 by 35x5, then 2x1 by 1x1 without reset. It checks
every output against the independent reference, zero-padded edge tiles,
K chunks, loading delays, compute stalls, held results, latched dimensions,
ignored busy starts, and final result acknowledgment. Tests use bounded
waits to report missing requests/results.

Host-level workloads and reset/error checks are listed in
[verification](verification.md). Generic synthesis and cycle measurements
are recorded in [results](results.md). Maximum field values are interface
limits, not exhaustively simulated matrix sizes.
Simulation durations above include deliberate delays and are not
throughput measurements.
