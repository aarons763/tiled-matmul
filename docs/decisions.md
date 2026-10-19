# Design and Workflow Decisions

## Accepted workflow decisions

### D001 — Use Ubuntu under WSL 2

Use Linux development tools with VS Code connected through WSL. Keep the
project in /home/aarons763/projects/tiled-matmul. Native Windows Icarus
setup was troublesome; the existing Ubuntu environment already contained
Icarus, Make, Git, and GTKWave.

### D002 — Isolate Python dependencies

Use the ignored project .venv and pin cocotb 2.1.0 in requirements.txt.
This isolates Python packages from Ubuntu's system Python. A fresh virtual
environment installed the requirements and passed the smoke test.

### D003 — Begin with Icarus and cocotb

Use Icarus 12.0 and cocotb 2.1.0 for initial simulation, with a small Makefile
and explicit 1 ns / 1 ps simulation defaults. This combination passed the
register smoke test. Future RTL constructs must be checked for simulator
support; passing this test does not establish full SystemVerilog support.

### D004 — Track development evidence in version control

Use aarons763/tiled-matmul, main tracking origin/main, and meaningful
commits. Record verified milestones, design decisions, and reproducible
validation commands alongside the implementation.

### D005 — Defer the license decision

On 2026-10-13 Aaron chose to defer selecting a repository license.
No LICENSE file is added. This decision does not block continued development.

## Open architecture decisions

- Supported matrix dimensions and local-memory capacity.
- Maximum K, signed arithmetic details, and overflow policy.
- Host protocol, reset behavior, errors, and output ordering.
- Memory layout, parallel access organization, and read latency.
- Exact PE/register schedule, stalls, tiling, and buffer ownership.
- Synthesis target, timing constraints, and later implementation flow.

The 4x4 output-stationary array, 8-bit operands, 32-bit accumulators, and
single-buffer-to-double-buffer comparison are planned directions, not yet
a completed architectural specification.

