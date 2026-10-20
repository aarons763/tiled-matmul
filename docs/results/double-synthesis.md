# Double-buffer generic synthesis

Run: 2026-10-19; OSS CAD Suite 2026-10-19.
Yosys 0.70+157 (af9f71e51), scripts/synth-double.ys.
Configuration: matmul_host, DOUBLE_BUFFER=1, ROWS=4, COLS=4, DEPTH=16.

Frontend: zero errors/warnings. Final check -assert: zero problems.
No RTL latches are reported in the final generic cell statistics.
Both operand sets are mapped to registers and logic; no target-specific
memory, DSP, area, or timing mapping is claimed.

The same-tool single-buffer rerun reports 21576 cells and 1952 flip-flop
bits, matching the earlier baseline. Double buffering reports 23819 cells
and 3055 flip-flop bits. Generic cell count is not a physical area metric.
ABC's combinational-network messages occur as in the baseline; structural
checks pass. No post-synthesis equivalence proof was performed.

Full logs are stored locally under tests/sim_build.

```text
=== matmul_host ===

        +----------Local Count, excluding submodules.
        | 
    20055 wires
    33879 wire bits
      826 public wires
     8742 public wire bits
       31 ports
      203 port bits
    23819 cells
      280   $_ANDNOT_
     3439   $_AND_
     2176   $_DFFE_PP_
        6   $_DFF_P_
     2333   $_MUX_
     6405   $_NAND_
      985   $_NOR_
      171   $_NOT_
      273   $_ORNOT_
     1376   $_OR_
      869   $_SDFFE_PP0P_
        4   $_SDFF_PP0_
     1627   $_XNOR_
     3875   $_XOR_


```
