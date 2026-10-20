# Full-host generic synthesis

The default 4x4, depth-16 matmul_host completed synthesis on 2026-10-19.
Tool: OSS CAD Suite 2026-10-19, Yosys 0.70+157, git af9f71e51.
Command: yosys -s scripts/synth-host.ys in the suite environment.

Frontend: 0 errors, 0 warnings. Final check -assert: 0 problems.
The generic mapped design has 21576 cells, including 1952 flip-flop bits.
All eight 16x8 operand banks were mapped to registers and logic by
memory_map. No target FPGA, ASIC library, timing constraints, or physical
implementation was selected. These numbers do not establish area, FPGA
LUT/DSP/BRAM usage, or achievable clock frequency.

ABC emitted repeated messages that its network was combinational. ABC
mapped combinational portions of the design; the final design still
contains the sequential cells listed below. These messages did not stop
synthesis or the final structural check. This run is not a proof of
equivalence between the synthesized netlist and the RTL.

The full run log is saved locally in tests/sim_build/host-synthesis.log.
The summary below is retained for comparison using the same tool and flow.

```text
=== matmul_host ===

        +----------Local Count, excluding submodules.
        | 
    18789 wires
    32866 wire bits
      622 public wires
     8223 public wire bits
       31 ports
      203 port bits
    21576 cells
      267   $_ANDNOT_
     3430   $_AND_
     1088   $_DFFE_PP_
        5   $_DFF_P_
     1299   $_MUX_
     6437   $_NAND_
      883   $_NOR_
      189   $_NOT_
      107   $_ORNOT_
     1476   $_OR_
      855   $_SDFFE_PP0P_
        4   $_SDFF_PP0_
     1687   $_XNOR_
     3849   $_XOR_


```
