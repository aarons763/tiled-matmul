# Full-design synthesis tool setup

The recorded full-design flow uses OSS CAD Suite 2026-10-19 with its
compatible SystemVerilog frontend. The system Yosys 0.52 built-in reader
does not accept this design's unpacked array ports.

Official references:
- https://github.com/povik/sv-elab
- https://github.com/YosysHQ/oss-cad-suite-build
- https://github.com/YosysHQ/oss-cad-suite-build/releases/tag/2026-10-19

## Installation in Ubuntu WSL

The Linux x64 asset below was verified through the official release API.
Run these commands in Ubuntu. No administrator privileges are required.
Use a new dated directory; mkdir deliberately fails if it already exists.

```bash
mkdir -p "$HOME/tools"
mkdir "$HOME/tools/cad-20261019"
cd "$HOME/tools/cad-20261019"
curl -fL --retry 3 -o oss-cad-suite-linux-x64-20261019.tgz \
  https://github.com/YosysHQ/oss-cad-suite-build/releases/download/2026-10-19/oss-cad-suite-linux-x64-20261019.tgz
tar -xzf oss-cad-suite-linux-x64-20261019.tgz
```

Stop if a command fails. The dated bundle identifies the tool versions
used for the recorded results.

## Verify the frontend

Use a subshell so suite environment changes do not persist in the normal
simulation terminal:

```bash
(
  source "$HOME/tools/cad-20261019/oss-cad-suite/environment"
  yosys -V
  yosys -Q -T -m slang -p "help read_slang"
)
```

Expected: a version followed by read_slang command help, with no plugin
load error. Installation and frontend loading were verified on 2026-10-19.

## Full synthesis after frontend verification

The existing scripts/synth-host.ys loads slang, elaborates matmul_host,
runs generic synthesis, checks the resulting design, and prints statistics.
Run from the repository root in the suite environment:

```bash
(
  source "$HOME/tools/cad-20261019/oss-cad-suite/environment"
  cd "$HOME/projects/tiled-matmul"
  yosys -s scripts/synth-host.ys
  yosys -s scripts/synth-double.ys
)
```

Both flows passed on 2026-10-19; see [single-buffer statistics](results/host-synthesis.md)
and [double-buffer statistics](results/double-synthesis.md). Generic cell
statistics do not establish timing or area on a particular FPGA or ASIC.
Continue using the existing system tools and project virtual environment
for the already measured simulation baseline.
