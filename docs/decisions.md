# Design decisions

## Arithmetic and compute organization

The design uses signed 8-bit operands and signed 32-bit accumulated results.
One output-stationary PE array retains a tile's partial sums across K chunks.
The default array is 4x4; the same parameterized RTL is tested at 2x3.
The host accepts nonzero 16-bit M/N dimensions and nonzero 17-bit K.

## Operand memory

Each array row has an A bank and each column has a B bank, with synchronous
registered reads. DEPTH defaults to 16. Each chunk starts at local address
zero. Inactive edge banks are filled with zero, and only the active output
region is returned.

DOUBLE_BUFFER=0 uses one operand set; DOUBLE_BUFFER=1 uses two sets with
exclusive read/write ownership during overlap. Both modes use one scheduler
and one compute array. The buffers overlap K chunks within an output tile.

## Host and control

The custom synchronous host protocol serializes operands and results.
One accepted write carries one signed byte. Results carry signed 32-bit
data and global coordinates. Command dimensions are captured on acceptance.
The host owns full-matrix storage and supplies every requested chunk.

Reset is active-high and synchronous. step freezes computation but not
loading or result handshakes. A tile's accumulators remain stable during
result backpressure. Reset invalidates buffer ownership and aborts completion.

## Evaluation

The experiment holds workload and host bandwidth constant. The primary
performance metric is accepted-command-to-final-result cycle count, with
the command-acceptance edge excluded. Separate counters describe loading,
result transfers, and overlap. Generic synthesis uses the same tool bundle
and mapping flow for both implementations.

Generic memory mapping uses registers and logic. No physical target, clock
constraint, place-and-route, device resource, power, or maximum-frequency
claim is part of the measured results.

## Reproducibility

Simulation uses Ubuntu/WSL, Icarus 12.0, cocotb 2.1.0, and a project virtual
environment. Lint uses Verilator 5.032. Full-host synthesis uses OSS CAD
Suite 2026-10-19, Yosys 0.70+157 (af9f71e51), and slang.
The regression saves logs and requires exact performance-snapshot matches.

## Repository licensing

No repository license file is supplied. The previously deferred license
decision is unchanged.
