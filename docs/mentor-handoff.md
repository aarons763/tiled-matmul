# Mentor handoff: tiled matrix-multiplication accelerator

## Start here

Continue mentoring Aaron Sun; do not implement the accelerator for him.
The working simulation setup is verified. The accelerator specification has
not been written and no accelerator RTL exists. Read this file, README.md,
docs/progress.md, docs/decisions.md, and the actual RTL/test before teaching
the next step. Do not restart installation or Git onboarding.

## Teaching agreement (latest preferences)

- Aaron writes all RTL, testbenches, reference models, and verification or
  benchmark/analysis Python himself. Review his work; do not replace it or
  supply complete solutions.
- The assistant writes supporting documentation, Makefiles, dependency files,
  and other configuration. This explicitly supersedes the original rule
  requiring Aaron to write every file.
- Aaron performs installations, Git commits, and pushes.
- Read-only inspection and existing builds/simulations are authorized.
  Explain meaningful commands before running them.
- Give one coherent, manageable task per turn and review it before advancing.
  Aaron has asked for larger steps than one tiny edit or command at a time.
- Use graduated help: concepts first, then timing/data flow, then pseudocode
  or unrelated examples if needed. Targeted RTL/Python syntax examples only
  when requested.
- Explain terminology, signed arithmetic, clock cycles, memory latency, and
  handshake acceptance precisely. Ask focused understanding questions.
- Keep checkpoints and update documentation at meaningful milestones.
- Use current official tool documentation for compatibility and API details.
- No code copied from accelerator projects; no unsupported performance,
  power, novelty, or ASIC claims.

## Background and constraints

Waterloo Electrical Engineering student targeting ASIC, silicon, RTL design,
and design verification internships. Previously completed a single-cycle
RISC-V CPU; familiar with basic Verilog, ALUs, counters, testbenches, Icarus,
GTKWave, and Python. Learning cocotb through hardware-team onboarding.
Do not assume knowledge of systolic arrays, banking, formal, timing
constraints, or physical implementation.

Windows user, now comfortable working in Ubuntu via WSL 2 and VS Code.
No FPGA board; no purchase needed. Flexible schedule, no deadline.
University commercial-tool access remains unknown and is not needed yet.

## Workspace and Git

- Main checkout: /home/aarons763/projects/tiled-matmul
- Verification copy: /home/aarons763/projects/tiled-matmul-setup-check
- Repository: https://github.com/aarons763/tiled-matmul (public)
- Branch: main, tracking origin/main
- HTTPS authentication works through Ubuntu GitHub CLI as aarons763.
- Aaron elected to retain his existing Git author identity.
- GitHub CLI reported plaintext credential storage. Never read, expose,
  or commit credential files.
- Commit b5172e5 contains the passing smoke test.
- Commit faaeef6 adds README.md and requirements.txt.
- Check current status/history: later setup documentation may have been
  committed after this handoff was written.
- Both checkouts have separate ignored .venv directories.
- File Explorer can open the Linux folder via explorer.exe . from Ubuntu.
- This earlier Codex chat was attached to a different Windows directory.
  Its restricted Windows shell could not access WSL directly. Approved
  exec_command calls using wsl.exe -d Ubuntu worked for read-only access
  and supporting documentation edits.
- A web retrieval failure for GitHub did not mean the repo was private.
  Ubuntu gh repo view successfully accessed it.

## Verified environment

- Ubuntu 26.04.1 LTS, WSL 2
- Python executable version reported 3.14.4
- Git 2.53.0
- Icarus compiler and vvp runtime 12.0 stable
- GNU Make 4.4.1
- GTKWave 3.3.126 (version checked; GUI waveform inspection not yet done)
- cocotb 2.1.0, pinned in requirements.txt
- Verible v0.0-4296-g0f262651
- VS Code in WSL: Ubuntu with mshr-h Verilog-HDL/SystemVerilog extension
- Formatter executable:
  /home/aarons763/tools/verible/verible-v0.0-4296-g0f262651/bin/verible-verilog-format
- Formatter configured in VS Code Remote settings via
  verilog.formatting.veribleVerilogFormatter.path.
- pip check reported no broken requirements.
- cocotb startup logs print Python 3.14.0, while shell version checks
  reported 3.14.4. The reason for that reporting difference was not
  investigated; do not assume the runtime was independently verified as
  either patch version from the log alone.

The project uses Ubuntu tools and its Linux .venv, not Windows Python.
Activate the environment in a new terminal:
  cd ~/projects/tiled-matmul
  source .venv/bin/activate

## Current implementation and tests

rtl/smoke_reg.sv is only an environment smoke-test module:
- clk and rst are one-bit inputs; d and q are eight bits.
- Positive-edge clocked register, active-high synchronous reset.
- Reset takes priority over capture; q holds between rising edges.
- No assumption about q before its first reset/capture edge.

tests/test_smoke_reg.py drives this sequence:
- 10 ns Clock, started low with clock.start(start_high=False).
- 5 ns: reset high, expect q=0.
- 10 ns falling edge: reset low, d=0xA5.
- 15 ns: expect q=0xA5.
- 20 ns falling edge: reset high, d=0x3C; after ReadOnly expect q still 0xA5.
- 25 ns: expect q=0.
- RisingEdge followed by ReadOnly is used for settled output checks.
- Input writes occur before clock start or at falling edges.
- Passing result: TESTS=1 PASS=1 FAIL=0 SKIP=0, 25 ns.
This is directed setup verification, not complete register coverage or
accelerator verification.

tests/Makefile selects Icarus, SystemVerilog via the verilog interface,
../rtl/smoke_reg.sv, top-level smoke_reg, test module test_smoke_reg,
default time unit 1 ns and precision 1 ps, and cocotb's Makefile.sim.
Run from the main checkout with make -C tests.

.gitignore excludes .venv/, sim_build/, results.xml, __pycache__/,
*.pyc, *.vcd, and *.fst.

## Reproducibility evidence

Aaron cloned GitHub into tiled-matmul-setup-check, created a fresh .venv
using /usr/bin/python3, installed requirements.txt, and ran make -C tests.
The output showed a new Icarus compilation and one passing test at 25 ns.
git status --short was empty afterward.
This reuses installed Ubuntu system tools; it is not a clean-machine test.
Aaron then returned to the main checkout and activated its original .venv.

## Accelerator goal: planned, not a finalized specification

Compute C[M,N] = A[M,K] * B[K,N].
Initial direction: 4x4 output-stationary systolic array, signed 8-bit
operands, signed 32-bit accumulators/outputs, one clock domain, and a global
step enable freezing the complete array and scheduler during stalls.
Local operand storage, tiled execution, rectangular shapes, partial edge
tiles, and a simple documented host interface.
Independent Python mathematical reference and self-checking verification.
Measure a single-buffer baseline before adding double buffering.

Main investigation:
How much performance can better memory scheduling and buffering recover
without adding compute units?

Before implementation, explicitly decide supported dimension/capacity
limits, maximum K, overflow semantics, reset/error/host behavior, data
layout, memory read latency, result ordering, and buffer ownership.
Do not assume unlimited K fits a 32-bit accumulator. Derive array timing
from the actual register placement.

## Roadmap to preserve

0. Environment assessment (functional setup established; commercial access unknown).
1. Repository/reproducible setup (working and fresh-checkout tested).
2. Independent specification, interface table, block diagram, scheduling math.
3. Aaron's independent Python reference with validation and integer semantics.
4. One PE: signed multiplication/extension, clear/reset priority, valid,
   forwarding, step enable, stalls; review waveforms.
5. Testbench-driven 2x2 array, then 4x4; operand staggering and exact timing.
6. Local memory and scheduler: bandwidth, banks/wide words, synchronous
   latency, conflicts, inference, stalls. FPGA BRAM is not ASIC SRAM.
7. Tiling over output tiles and K chunks; preserve accumulation, drain
   in-flight operands correctly, mask partial edges, enforce bounds.
8. Simple host control/result storage with exact acceptance semantics.
9. Full-system cocotb, deterministic random tests, delays/stalls, timeouts,
   reset/error tests, verification plan, assertions and selected formal.
10. Lint, synthesis and constrained timing; record target/library/corner,
    memory implementation, and synthesis versus physical-flow limits.
11. Double buffering with ownership, safe swaps, overlap feasibility,
    delayed loads and randomized verification.
12. Fair baseline comparison: load/compute/drain/total cycles, useful MACs,
    defined utilization denominator, throughput, traffic, area and timing.
13. Optional FPGA, standard interface, scaling or physical implementation
    only after the main project is complete and based on resources.
14. Portfolio: accurate documentation, benchmarks, tradeoffs, bugs,
    limitations, acknowledgments, resume evidence and interview questions.

Build directories/modules only when needed, not a speculative empty tree.

## References and setup items still requiring a decision

Aaron supplied this related Cornell project as background:
https://people.ece.cornell.edu/land/courses/ece5760/FinalProjects/f2020/bjd86_lgp36/bjd86_lgp36/index.html

Aaron describes it as comparing a register-parallel multiplier and a
memory-based single-MAC implementation. The mentor has not yet independently
reviewed the page. Read it before making detailed comparison claims.
Acknowledge references honestly and never copy its RTL/tests.

Aaron explicitly deferred the repository license decision on 2026-10-13.
No LICENSE file was added. Do not reopen this choice as a blocker to
architecture work or add a license without his later instruction.
Architecture decisions remain open and must be taught before documenting
them as final.

## Next teaching step

First confirm the final setup documentation is committed/pushed.
The license decision is explicitly deferred. Then begin Stage 2 with a
small hand-calculated matrix product and dot-product/MAC explanation.
Review Aaron's arithmetic before teaching output-stationary dataflow.
Do not generate accelerator RTL or the reference model.

