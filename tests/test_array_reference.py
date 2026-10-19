import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb.triggers import FallingEdge
from cocotb.triggers import ReadOnly

from matmul_reference import matmul_reference

a = [
    [1, -2, 3],
    [0, 4, -1],
    [-3, 2, 1],
    [2, 0, -2],
]

b = [
    [2, 1, -1, 3],
    [-1, 3, 2, 0],
    [4, -2, 1, -1],
]

expected = matmul_reference(a, b)
rows = len(a)
cols = len(b[0])
K = len(a[0])

@cocotb.test()
async def test_array_reference(dut):

    dut.clk.value = 0
    dut.rst.value = 1
    dut.step.value = 0
    dut.clear.value = 0

    for r in range(rows):
        dut.a_in[r].value = 0
        dut.a_valid_in[r].value = 0

    for c in range(cols):
        dut.b_in[c].value = 0
        dut.b_valid_in[c].value = 0

    clock = Clock(dut.clk, 10, unit="ns")  # Create a clock with a period of 10 ns
    clock.start(start_high=False)  # Start the clock low

    await RisingEdge(dut.clk)
    await ReadOnly()

    dut._log.info("Starting test_array_reference")

    for t in range(rows + cols + K - 2):
        await FallingEdge(dut.clk)
        dut.rst.value = 0
        dut.clear.value = 0
        dut.step.value = 1
        for r in range (rows):
            k = t - r
            if 0 <= k < K:
                dut.a_in[r].value = a[r][k]
                dut.a_valid_in[r].value = 1
            else:
                dut.a_in[r].value = 0
                dut.a_valid_in[r].value = 0
        for c in range (cols):
            k = t - c
            if 0 <= k < K:
                dut.b_in[c].value = b[k][c]
                dut.b_valid_in[c].value = 1
            else:
                dut.b_in[c].value = 0
                dut.b_valid_in[c].value = 0
        await RisingEdge(dut.clk)
        await ReadOnly()
    
    for r in range(rows):
        for c in range(cols):
            actual = dut.acc[r * cols + c].value.to_signed()
            assert actual == expected[r][c], f"acc[{r}][{c}] should be {expected[r][c]}, but got {actual}"