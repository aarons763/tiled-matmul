# Tiled Matrix-Multiplication Accelerator

An educational SystemVerilog project investigating how memory scheduling
and buffering affect matrix-multiplication performance with a fixed
number of compute units.

## Current status

The single-buffer compute core now sequences output tiles and K chunks.
Directed full-matrix simulations pass for 4x4 and 2x3 arrays, including a
6x35 by 35x5 workload with loading delays, compute stalls, and delayed
result acceptance.

A ready/valid host wrapper now accepts serialized operand writes and emits
individual results with global coordinates. Directed host-interface tests
pass for both array configurations. The external host supplies operands
and collects the full output matrix. Broader verification, synthesis, and
the double-buffer performance comparison remain outstanding.

## Planned direction

- A 4×4 output-stationary systolic array.
- Signed 8-bit operands and signed 32-bit accumulators.
- Tiled execution, including rectangular matrices and partial tiles.
- A verified single-buffer baseline followed by double buffering.
- Performance comparisons using identical workloads.

These are initial goals. Dimension limits, overflow behavior, memory
organization, and interface details will be specified before implementation.

## Development environment

Verified tool versions:
- Ubuntu 26.04.1 LTS under WSL 2.
- Python 3.14.4.
- Icarus Verilog and vvp 12.0.
- cocotb 2.1.0.
- GNU Make 4.4.1.
- GTKWave 3.3.126.

VS Code connects through its WSL extension. Run the commands below in
Ubuntu, not Windows PowerShell.

## Setup

Install the Ubuntu prerequisites:

```bash
sudo apt update
sudo apt install git make iverilog gtkwave python3-venv libpython3-dev
```

Clone the repository into your Linux home directory:

```bash
mkdir -p ~/projects
cd ~/projects
git clone https://github.com/aarons763/tiled-matmul.git
cd tiled-matmul
```

Create an isolated Python environment and install the test dependency:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Ubuntu package versions depend on the distribution and repository state.
The versions above describe the tested setup; the setup commands do not
pin system packages.

## Run the smoke test

From the project root:

```bash
source .venv/bin/activate
make -C tests
```

Expected result: one passing test, zero failures, and 25 ns of simulated time.

Generated files appear under `tests/` and are excluded from Git.
The `.venv` directory is also excluded.

## Files

- `rtl/smoke_reg.sv`: 8-bit register used to check the simulation setup.
- `tests/test_smoke_reg.py`: directed cocotb test.
- `tests/Makefile`: simulation configuration.
- `requirements.txt`: selected cocotb version.
- `docs/progress.md`: development history and verified milestones.

## Limitations

The passing smoke test establishes basic simulator/testbench integration.
There are no accelerator performance, synthesis, timing, area, or power
results yet. A fresh GitHub checkout with a newly created Python virtual environment passed the smoke test at 25 ns. This check reused the installed Ubuntu system tools; it was not a clean-machine test.

## Run the PE test

From the project root, with the virtual environment active:

```bash
make -C tests -f Makefile.pe
```

The PE uses a separate build directory, `tests/sim_build/pe/`.
The original `make -C tests` command continues to run the register smoke test.
The expanded PE directed test passed at 205 ns (1 passed, 0 failed).
It covers signed operand boundaries, valid and invalid pairs, clear priority,
reset during a stall, three-edge state retention, and resumption.
This is directed component coverage, not exhaustive PE verification.
Three stall assertion messages still need their expected-value text aligned
with the correct assertions; this does not affect the passing checks.

## Array simulations

With the virtual environment active, run the 2x2 directed test:

```bash
make -C tests -f Makefile.array
```

Run the current 4x4 reference-based test:

```bash
make -C tests -f Makefile.array4
```

The directed test passed at 105 ns; the 4x4 reference test passed at
95 ns. The reference test currently contains a 4x3 by 3x4 workload and
must use the 4x4 configuration. Build directories are separate.
The full accelerator, memory subsystem, and controller are not implemented.

## Operand storage simulations

With the virtual environment active:

```bash
make -C tests -f Makefile.bank
make -C tests -f Makefile.buffer
```

The bank directed test passed at 155 ns. The operand-buffer test passed at
115 ns with four A banks, four B banks, and 16 entries per bank.
These commands test the storage components in isolation. The integrated
buffered array is tested separately below; scheduler RTL remains outstanding.

## Buffered array integration

```bash
make -C tests -f Makefile.buffered
```

The 4x4 buffered-array test passed at 335 ns. It checks a K=3 workload
against the mathematical reference, synchronous read latency, stalls,
result retention, and recomputation after clear using retained operands.
Read requests are still driven by the testbench; there is no hardware
scheduler or complete tiled accelerator yet.

## Read scheduler simulation

```bash
make -C tests -f Makefile.scheduler
make -C tests -f Makefile.scheduler ROWS=2 COLS=3
```

Directed tests passed for 4x4 (775 ns) and 2x3 (655 ns) with bank depth 16.
They check K=1, 3, and 16, read requests, stalls, start handling, completion,
and reset/restart. The scheduler is tested separately from the datapath.

## Tile engine simulation

```bash
make -C tests -f Makefile.tile
make -C tests -f Makefile.tile ROWS=2 COLS=3
```

The tile engine connects the scheduler to buffered computation. Directed
K=3 tests passed at 555 ns (4x4) and 465 ns (2x3), including stalls,
accumulation across repeated runs, clear priority, and busy write blocking.
Inputs must obey the legal-K and loaded-address contract. Higher-level
tiling and host control are not implemented.

## Chunk controller simulation

```bash
make -C tests -f Makefile.chunk
```

The standalone chunk-controller test passed at 1055 ns. It checks full
and partial chunks and delayed loader/engine responses. See
[the chunk-controller contract](docs/chunk-controller.md) for handshake
rules and the limits of the current verification.

## Multi-chunk tile engine

```bash
make -C tests -f Makefile.chunked
make -C tests -f Makefile.chunked ROWS=2 COLS=3
```

Directed K=35,17,1 workloads passed against the mathematical reference with
depth-16 banks: 2585 ns for 4x4 and 2285 ns for 2x3. The testbench loads
operands on request and introduces loading delays and compute stalls.
This computes one output tile across K chunks; larger output matrices
still require output-tile sequencing.

## Output tile sequencing

```bash
make -C tests -f Makefile.output_tile
make -C tests -f Makefile.output_tile ROWS=2 COLS=3
make -C tests -f Makefile.output_tile DIM_WIDTH=4
```

All three directed controller tests passed. The four-bit dimension build
checks a 15x15 output near the coordinate limit. See
[the output-tile protocol](docs/output-tile-controller.md) for result
acceptance and partial-tile rules. Compute-engine integration is pending.

## Full matrix simulation

```bash
make -C tests -f Makefile.matmul
make -C tests -f Makefile.matmul ROWS=2 COLS=3
```

Both directed tests pass. See [the top-level interface contract](docs/tiled-matmul-interface.md)
for loading, partial-tile padding, result acceptance, and current limitations.

## Host interface simulation

```bash
make -C tests -f Makefile.host
make -C tests -f Makefile.host ROWS=2 COLS=3
```

Both directed tests pass: 17055 ns for 4x4 and 17735 ns for 2x3.
See [the host interface contract](docs/host-interface.md) for commands,
operand writes, loading completion, result streaming, and reset behavior.
