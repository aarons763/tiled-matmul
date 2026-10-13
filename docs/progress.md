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
- Prepared a mentor handoff and initial decision log for continuing in a new chat.
- Aaron explicitly deferred the repository license decision; no LICENSE file was added. Accelerator architecture is not yet specified.
