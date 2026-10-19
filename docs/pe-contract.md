# Processing Element Contract (Draft)

Status: proposed behavior for review; not an implementation-ready specification.

## Purpose and scope

This processing element (PE) is intended to be instantiated in the final
4x4 output-stationary array. Each PE retains one output's partial sum,
forwards A operands to the right, and forwards B operands downward.
A smaller array may be used to verify the same reusable component.

## Proposed interface

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

## Proposed state behavior

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
There is no additional product pipeline register in this proposal.

Without stalls, if the top-left PE processes k=0 at edge 1, input
staggering gives MAC edge 1+i+j+k for PE row i and column j (zero-based).
With stalls, this relation counts enabled compute advances, not elapsed
clock edges. Reset and preparation/clear edges are outside that count.

The step signal must freeze the scheduler and all array state together.
The PE has no independent ready signal or completion detector; the
scheduler tracks progress and determines when acc is a complete result.

## Decisions still required before implementation

- Review and accept the control priority and clear behavior above.
- Specify signed product width, sign extension, and accumulator overflow
  semantics; determine a supported maximum K.
- Establish the PE verification cases and how results will be observed.
- Complete the surrounding accelerator specification and independent
  mathematical reference before advancing to PE RTL.
