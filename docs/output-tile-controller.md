# Output Tile Controller

Sequences output tiles in row-major order: columns advance first, then rows.
Parameters default to ROWS=4, COLS=4, DIM_WIDTH=16. Dimensions must be
positive; tile sizes must be positive and fit in DIM_WIDTH bits. Count
widths must represent ROWS and COLS themselves. Invalid dimensions are
outside the current interface contract.

Pulse start while idle to capture m_len and n_len. The engine must be idle.
The controller emits one engine_start cycle per tile, then waits for
engine_done. Engine completion enters RESULT, asserting result_valid.
The receiver captures valid_rows by valid_cols outputs at a rising edge
where result_valid and result_ready are both high. Tile coordinates and
counts remain stable until that edge. Ready may already be high, but
cannot acknowledge a result before result_valid is asserted.

Only after result acceptance does the controller start another tile.
Accepting the final tile returns to idle and pulses done for one clock.
Counts are zero while idle or reset; coordinates remain at the final tile
until the next start or reset. Reset is synchronous, aborts without done,
and must be shared with the compute engine. Command outputs are suppressed
while reset is high. Busy starts are ignored.

The external loader uses tile_row and tile_col to select matrix operands.
For partial tiles it must load zero into inactive A-row and B-column banks.
The receiver stores only the indicated valid output region. K handling
belongs to the chunked tile engine, not this controller.

The next-boundary sums use DIM_WIDTH+1 bits before comparison. Truncation
to the stored coordinate width occurs only when another tile is in range.

## Verification

Run make -C tests -f Makefile.output_tile. Default 4x4 and rectangular 2x3
tile builds each passed at 1195 ns. DIM_WIDTH=4 additionally traversed a
15x15 output to exercise coordinate overflow boundaries; passed at 2255 ns.
Tests cover exact and partial tiles, single rows/columns, engine delays,
delayed result acceptance, early ready, latched dimensions, one-clock
commands/completion, and reset in all active phases.
Engine completion is supplied by the testbench. Full matrix multiplication
through the real chunked engine is not yet integrated.
