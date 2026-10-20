# Processing Element Contract

## Purpose and scope

This processing element (PE) is instantiated in the parameterized
output-stationary array. Each PE retains one output's partial sum,
forwards A operands to the right, and forwards B operands downward.
The same PE is used in both buffering modes.

## Interface

| Signal | Direction | Meaning |
| --- | --- | --- |
| clk | Input | Clock; state changes on rising edges |
| rst | Input | Active-high synchronous reset |
| step | Input | Global enable for an array advance |
| clear | Input | Clear the accumulator on an enabled edge |
| a_in, b_in | Input | Signed 8-bit operands |
| a_valid_in, b_valid_in | Input | Whether each input contains an operand |
| a_out, b_out | Output | Registered signed 8-bit forwarded operands |
| a_valid_out, b_valid_out | Output | Registered validity of forwarded operands |
| acc | Output | Signed 32-bit accumulator register |

The scheduler must align operands belonging to the same shared-dimension
index k. Valid flags indicate presence, not the identity of k.

## State behavior

At each rising edge, apply this priority:

1. If rst is high, zero the accumulator, forwarded operands, and output
   valid flags, regardless of step or clear.
2. Otherwise, if step is low, hold all PE state. No forwarding, clear,
   or MAC occurs.
3. Otherwise, advance both operand paths: register each incoming operand
   and its valid flag independently.
   - If clear is high, zero the accumulator and perform no MAC.
   - Otherwise, if both input valid flags are high, add their signed
     product to the accumulator.
   - Otherwise, hold the accumulator.

Clear affects the accumulator only; it does not flush operand paths.
A scheduler must issue clear with invalid inputs and only after previous
work has drained. Clear must be held until an enabled edge accepts it.
Do not clear between K chunks belonging to the same output tile.

An invalid operand is a bubble, not a numeric zero. A valid zero is a real
operand. Forwarding one valid stream does not depend on the other stream
being valid.

## Timing model

A MAC uses input values present immediately before its rising edge.
Those same input values become registered forwarding outputs after that
edge. A neighboring PE can use them at the next enabled edge.
There is no additional product pipeline register in this implementation.

Without stalls, if the top-left PE processes k=0 at edge 1, input
staggering gives MAC edge 1+i+j+k for PE row i and column j (zero-based).
With stalls, this relation counts enabled compute advances, not elapsed
clock edges. Reset and preparation/clear edges are outside that count.

The step signal must freeze the scheduler and all array state together.
The PE has no independent ready signal or completion detector; the
scheduler tracks progress and determines when acc is a complete result.

## Arithmetic and verification

The product is signed 16-bit and is explicitly sign-extended to 32 bits
before accumulation. The host limits K to 131071, keeping all supported
signed 8-bit dot products within signed 32-bit range. Standalone callers
must respect the accumulator range; the PE itself does not detect overflow.

Run make -C tests -f Makefile.pe. Directed checks cover signed extremes,
negative sums, valid-zero inputs, all valid combinations, clear/reset
priority, forwarding, stalls, and resumption.
