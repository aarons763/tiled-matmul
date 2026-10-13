# Tiled Matrix-Multiplication Accelerator

An educational SystemVerilog project investigating how memory scheduling
and buffering affect matrix-multiplication performance with a fixed
number of compute units.

## Current status

The development environment and a small register simulation smoke test
are working. The accelerator itself is not implemented yet.

The smoke test checks:
- Synchronous reset.
- Data capture on a rising clock edge.
- Output holding between rising edges.
- Reset priority over nonzero input data.

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
