# Host interface

`rtl/matmul_host.sv` wraps the tiled compute core with a serialized operand
write port and a serialized result port. All transfers occur on a rising
clock edge when both the corresponding valid and ready signals are high.
A sender holds valid and its payload until acceptance.

## Commands

Supply M, N, and K on cmd_m, cmd_n, and cmd_k with cmd_valid.
cmd_ready is high only when idle and outside reset. An accepted nonzero
command starts C[M][N] = A[M][K] * B[K][N]; dimensions are captured then.

An accepted command with any zero dimension does not start work. error is
high for the following cycle. Consecutive accepted invalid commands can
keep error high across consecutive cycles. Commands presented while busy
are not accepted.

With default widths, M and N range from 1 to 65535 and K from 1 to 131071.
These are interface limits, not fully tested workload sizes. Operands are
signed 8-bit and results signed 32-bit. The K limit keeps every possible
signed 8-bit dot product within signed 32-bit range.

## Loading a chunk

When load_req is high, tile_row and tile_col identify the output tile,
valid_rows and valid_cols identify its active region, and k_offset and
chunk_len identify the requested slice of the reduction dimension.

For each local address q from 0 through chunk_len-1, write:
- A bank r: A[tile_row+r][k_offset+q], or zero if r >= valid_rows.
- B bank c: B[k_offset+q][tile_col+c], or zero if c >= valid_cols.

Set wr_is_b to 0 for A or 1 for B. wr_bank selects the bank, wr_addr is q,
and wr_data is the signed operand. One operand is written per accepted
transfer. Writes are accepted only during load_req, with an existing bank
and wr_addr < chunk_len. Invalid destinations hold wr_ready low and do
not assert error.

The host must initialize every required location, including padding.
Hardware does not track missing writes. After the last accepted write,
deassert wr_valid and assert load_complete_valid until
load_complete_ready accepts it. A high wr_valid takes priority over load
completion, even if the write destination is invalid.

Each chunk starts at local bank address zero. Data must be supplied again
for each requested output tile and chunk; the wrapper does not fetch from
system memory.

## Results and completion

Each result transfer supplies signed result_data and its global
result_row and result_col. Only active elements are emitted, in row-major
order within each tile; tiles also advance in row-major order. This is
not strictly row-major order across the entire output matrix.

When result_valid is high and result_ready is low, data and coordinates
remain stable. The core keeps the current tile's accumulators until its
last element is accepted. done pulses for one cycle after the final
element of the final tile is accepted, and busy clears.

The external receiver stores the full matrix. No separate result RAM is
required for this streaming baseline.

## Reset and stalls

rst synchronously aborts an operation and clears control state; ready and
result-valid outputs are suppressed while rst is high. Operand memory is
not cleared, so reload all required locations for a new operation.

step gates computation only. Commands, operand writes, loading completion,
and result acceptance can proceed while step is low.

## Verification

Run from the repository root with the virtual environment active:

```bash
make -C tests -f Makefile.host
make -C tests -f Makefile.host ROWS=2 COLS=3
```

Directed tests passed: 4x4 at 17055 ns and 2x3 at 17735 ns, one test each.
They compare a 6x35 by 35x5 product and a subsequent 1x1 product against
the reference, checking partial tiles, chunk loading, compute stalls,
result backpressure, command rejection, invalid write destinations,
write/completion priority, and reset during loading.

These tests are not exhaustive verification or synthesis/performance
measurements. The interface is a custom synchronous protocol, not AXI,
PCIe, or a software driver.
