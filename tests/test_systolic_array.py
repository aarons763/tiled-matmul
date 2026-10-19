import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb.triggers import FallingEdge
from cocotb.triggers import ReadOnly

@cocotb.test()
async def test_systolic_array(dut):

    dut.clk.value = 0
    dut.rst.value = 0
    dut.step.value = 0
    dut.clear.value = 0

    for i in range(2):
        dut.a_in[i].value = 0
        dut.b_in[i].value = 0
        dut.a_valid_in[i].value = 0
        dut.b_valid_in[i].value = 0

    clock = Clock(dut.clk, 10, unit="ns")  # Create a clock with a period of 10 ns
    clock.start(start_high=False)  # Start the clock low

    dut._log.info("Starting test_systolic_array")

    dut._log.info("Reset")
    await FallingEdge(dut.clk)
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()
    for i in range(2):
        for j in range(2):
            assert dut.acc[i * 2 + j].value.to_signed() == 0, f"acc[{i}][{j}] should be 0 after reset, but got {dut.acc[i * 2 + j].value}"

    dut._log.info("2x2 Array Test")

    dut._log.info("Edge 1")
    await FallingEdge(dut.clk)
    dut.rst.value = 0
    dut.step.value = 1
    dut.a_in[0].value = 1
    dut.a_valid_in[0].value = 1
    dut.a_valid_in[1].value = 0
    dut.b_in[0].value = 2
    dut.b_valid_in[0].value = 1
    dut.b_valid_in[1].value = 0
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.acc[0].value.to_signed() == 2, f"acc[0][0] should be 2, but got {dut.acc[0].value}"
    assert dut.acc[1].value.to_signed() == 0, f"acc[0][1] should be 0, but got {dut.acc[1].value}"
    assert dut.acc[2].value.to_signed() == 0, f"acc[1][0] should be 0, but got {dut.acc[2].value}"
    assert dut.acc[3].value.to_signed() == 0, f"acc[1][1] should be 0, but got {dut.acc[3].value}"

    dut._log.info("Edge 2")
    await FallingEdge(dut.clk)
    dut.a_in[0].value = -2
    dut.a_in[1].value = 0
    dut.a_valid_in[1].value = 1
    dut.b_in[0].value = -1
    dut.b_in[1].value = 1
    dut.b_valid_in[1].value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.acc[0].value.to_signed() == 4, f"acc[0][0] should be 4, but got {dut.acc[0].value}"
    assert dut.acc[1].value.to_signed() == 1, f"acc[0][1] should be 1, but got {dut.acc[1].value}"
    assert dut.acc[2].value.to_signed() == 0, f"acc[1][0] should be 0, but got {dut.acc[2].value}"
    assert dut.acc[3].value.to_signed() == 0, f"acc[1][1] should be 0, but got {dut.acc[3].value}"

    dut._log.info("Stall 1")
    await FallingEdge(dut.clk)
    dut.step.value = 0
    dut.a_in[0].value = 6
    dut.a_in[1].value = 3
    dut.b_in[0].value = 5
    dut.b_in[1].value = 2
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.acc[0].value.to_signed() == 4, f"acc[0][0] should be 4, but got {dut.acc[0].value}"
    assert dut.acc[1].value.to_signed() == 1, f"acc[0][1] should be 1, but got {dut.acc[1].value}"
    assert dut.acc[2].value.to_signed() == 0, f"acc[1][0] should be 0, but got {dut.acc[2].value}"
    assert dut.acc[3].value.to_signed() == 0, f"acc[1][1] should be 0, but got {dut.acc[3].value}"

    dut._log.info("Stall 2")
    await FallingEdge(dut.clk)
    dut.a_in[0].value = 1
    dut.a_in[1].value = 4
    dut.b_in[0].value = 3
    dut.b_in[1].value = 9
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.acc[0].value.to_signed() == 4, f"acc[0][0] should be 4, but got {dut.acc[0].value}"
    assert dut.acc[1].value.to_signed() == 1, f"acc[0][1] should be 1, but got {dut.acc[1].value}"
    assert dut.acc[2].value.to_signed() == 0, f"acc[1][0] should be 0, but got {dut.acc[2].value}"
    assert dut.acc[3].value.to_signed() == 0, f"acc[1][1] should be 0, but got {dut.acc[3].value}"

    dut._log.info("Edge 3")
    await FallingEdge(dut.clk)
    dut.step.value = 1
    dut.a_in[0].value = 3
    dut.a_in[1].value = 4
    dut.b_in[0].value = 4
    dut.b_in[1].value = 3
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.acc[0].value.to_signed() == 16, f"acc[0][0] should be 16, but got {dut.acc[0].value}"
    assert dut.acc[1].value.to_signed() == -5, f"acc[0][1] should be -5, but got {dut.acc[1].value}"
    assert dut.acc[2].value.to_signed() == -4, f"acc[1][0] should be -4, but got {dut.acc[2].value}"
    assert dut.acc[3].value.to_signed() == 0, f"acc[1][1] should be 0, but got {dut.acc[3].value}"

    dut._log.info("Edge 4")
    await FallingEdge(dut.clk)
    dut.a_valid_in[0].value = 0
    dut.a_in[1].value = -1
    dut.b_valid_in[0].value = 0
    dut.b_in[1].value = -2
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.acc[0].value.to_signed() == 16, f"acc[0][0] should be 16, but got {dut.acc[0].value}"
    assert dut.acc[1].value.to_signed() == -11, f"acc[0][1] should be -11, but got {dut.acc[1].value}"
    assert dut.acc[2].value.to_signed() == -8, f"acc[1][0] should be -8, but got {dut.acc[2].value}"
    assert dut.acc[3].value.to_signed() == 12, f"acc[1][1] should be 12, but got {dut.acc[3].value}"

    dut._log.info("Edge 5")
    await FallingEdge(dut.clk)
    dut.a_valid_in[1].value = 0
    dut.b_valid_in[1].value = 0
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.acc[0].value.to_signed() == 16, f"acc[0][0] should be 16, but got {dut.acc[0].value}"
    assert dut.acc[1].value.to_signed() == -11, f"acc[0][1] should be -11, but got {dut.acc[1].value}"
    assert dut.acc[2].value.to_signed() == -8, f"acc[1][0] should be -8, but got {dut.acc[2].value}"
    assert dut.acc[3].value.to_signed() == 14, f"acc[1][1] should be 14, but got {dut.acc[3].value}"

    dut._log.info("Hold 1")
    await FallingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.acc[0].value.to_signed() == 16, f"acc[0][0] should be 16, but got {dut.acc[0].value}"
    assert dut.acc[1].value.to_signed() == -11, f"acc[0][1] should be -11, but got {dut.acc[1].value}"
    assert dut.acc[2].value.to_signed() == -8, f"acc[1][0] should be -8, but got {dut.acc[2].value}"
    assert dut.acc[3].value.to_signed() == 14, f"acc[1][1] should be 14, but got {dut.acc[3].value}"

    dut._log.info("Hold 2")
    await FallingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.acc[0].value.to_signed() == 16, f"acc[0][0] should be 16, but got {dut.acc[0].value}"
    assert dut.acc[1].value.to_signed() == -11, f"acc[0][1] should be -11, but got {dut.acc[1].value}"
    assert dut.acc[2].value.to_signed() == -8, f"acc[1][0] should be -8, but got {dut.acc[2].value}"
    assert dut.acc[3].value.to_signed() == 14, f"acc[1][1] should be 14, but got {dut.acc[3].value}"

    dut._log.info("Clear")
    await FallingEdge(dut.clk)
    dut.clear.value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.acc[0].value.to_signed() == 0, f"acc[0][0] should be 0, but got {dut.acc[0].value}"
    assert dut.acc[1].value.to_signed() == 0, f"acc[0][1] should be 0, but got {dut.acc[1].value}"
    assert dut.acc[2].value.to_signed() == 0, f"acc[1][0] should be 0, but got {dut.acc[2].value}"
    assert dut.acc[3].value.to_signed() == 0, f"acc[1][1] should be 0, but got {dut.acc[3].value}"