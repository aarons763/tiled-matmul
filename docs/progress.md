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