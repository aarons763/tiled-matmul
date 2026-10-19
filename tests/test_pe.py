import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb.triggers import FallingEdge
from cocotb.triggers import ReadOnly

@cocotb.test()
async def test_pe(dut):

    dut.clk.value = 0
    dut.rst.value = 0
    dut.step.value = 0
    dut.clear.value = 0
    dut.a_in.value = 0
    dut.b_in.value = 0
    dut.a_valid_in.value = 1
    dut.b_valid_in.value = 1

    clock = Clock(dut.clk, 10, unit="ns")  # Create a clock with a period of 10 ns
    clock.start(start_high=False)  # Start the clock low

    dut._log.info("Starting test_pe")

    dut._log.info("Reset Test")
    await FallingEdge(dut.clk)
    dut.rst.value = 1
    dut.a_in.value = 0xA5
    dut.b_in.value = 0x3C
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.a_out.value == 0 and dut.b_out.value == 0 and dut.a_valid_out.value == 0 and dut.b_valid_out.value == 0 and dut.acc.value == 0, f"Expected a_out, b_out, a_valid_out, b_valid_out, and acc to be 0, but got a_out={dut.a_out.value}, b_out={dut.b_out.value}, a_valid_out={dut.a_valid_out.value}, b_valid_out={dut.b_valid_out.value}, acc={dut.acc.value}"

    dut._log.info("Step-Enable Test")
    await FallingEdge(dut.clk)
    dut.rst.value = 0
    dut.step.value = 1
    dut.a_in.value = 2
    dut.b_in.value = 3
    dut.a_valid_in.value = 1
    dut.b_valid_in.value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.a_out.value == 2 and dut.b_out.value == 3 and dut.a_valid_out.value == 1 and dut.b_valid_out.value == 1 and dut.acc.value == 6, f"Expected a_out, b_out, a_valid_out, b_valid_out, and acc to be 2, 3, 1, 1, and 6 respectively, but got a_out={dut.a_out.value}, b_out={dut.b_out.value}, a_valid_out={dut.a_valid_out.value}, b_valid_out={dut.b_valid_out.value}, acc={dut.acc.value}"

    dut._log.info("Step-Disable Test")
    await FallingEdge(dut.clk)
    dut.step.value = 0
    dut.a_in.value = 7
    dut.b_in.value = 8
    dut.a_valid_in.value = 0
    dut.b_valid_in.value = 0
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.a_out.value == 2 and dut.b_out.value == 3 and dut.a_valid_out.value == 1 and dut.b_valid_out.value == 1 and dut.acc.value == 6, f"Expected a_out, b_out, a_valid_out, b_valid_out, and acc to be 2, 3, 1, 1, and 6 respectively, but got a_out={dut.a_out.value}, b_out={dut.b_out.value}, a_valid_out={dut.a_valid_out.value}, b_valid_out={dut.b_valid_out.value}, acc={dut.acc.value}"

    dut._log.info("Negative Test")
    await FallingEdge(dut.clk)
    dut.step.value = 1
    dut.a_in.value = -1
    dut.b_in.value = 4
    dut.a_valid_in.value = 1
    dut.b_valid_in.value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.a_out.value.to_signed() == -1 and dut.b_out.value == 4 and dut.a_valid_out.value == 1 and dut.b_valid_out.value == 1 and dut.acc.value == 2, f"Expected a_out, b_out, a_valid_out, b_valid_out, and acc to be -1, 4, 1, 1, and 2 respectively, but got a_out={dut.a_out.value.to_signed()}, b_out={dut.b_out.value}, a_valid_out={dut.a_valid_out.value}, b_valid_out={dut.b_valid_out.value}, acc={dut.acc.value}"
    
    dut._log.info("Only A Valid Test")
    await FallingEdge(dut.clk)
    dut.step.value = 1
    dut.a_in.value = 7
    dut.b_in.value = 9
    dut.a_valid_in.value = 1
    dut.b_valid_in.value = 0
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.a_out.value == 7 and dut.b_out.value == 9 and dut.a_valid_out.value == 1 and dut.b_valid_out.value == 0 and dut.acc.value == 2, f"Expected a_out, b_out, a_valid_out, b_valid_out, and acc to be 7, 9, 1, 0, and 2 respectively, but got a_out={dut.a_out.value}, b_out={dut.b_out.value}, a_valid_out={dut.a_valid_out.value}, b_valid_out={dut.b_valid_out.value}, acc={dut.acc.value}"

    dut._log.info("Only B Valid Test")
    await FallingEdge(dut.clk)
    dut.step.value = 1
    dut.a_in.value = 7
    dut.b_in.value = 9
    dut.a_valid_in.value = 0
    dut.b_valid_in.value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.a_out.value == 7 and dut.b_out.value == 9 and dut.a_valid_out.value == 0 and dut.b_valid_out.value == 1 and dut.acc.value == 2, f"Expected a_out, b_out, a_valid_out, b_valid_out, and acc to be 7, 9, 0, 1, and 2 respectively, but got a_out={dut.a_out.value}, b_out={dut.b_out.value}, a_valid_out={dut.a_valid_out.value}, b_valid_out={dut.b_valid_out.value}, acc={dut.acc.value}"

    dut._log.info("Clear Test")
    await FallingEdge(dut.clk)
    dut.step.value = 1
    dut.clear.value = 1
    dut.a_in.value = 2
    dut.b_in.value = 3
    dut.a_valid_in.value = 1
    dut.b_valid_in.value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.a_out.value == 2 and dut.b_out.value == 3 and dut.a_valid_out.value == 1 and dut.b_valid_out.value == 1 and dut.acc.value == 0, f"Expected a_out, b_out, a_valid_out, b_valid_out, and acc to be 2, 3, 1, 1, and 0 respectively, but got a_out={dut.a_out.value}, b_out={dut.b_out.value}, a_valid_out={dut.a_valid_out.value}, b_valid_out={dut.b_valid_out.value}, acc={dut.acc.value}"

    dut._log.info("Boundary Neg-Pos Test")
    await FallingEdge(dut.clk)
    dut.step.value = 1
    dut.clear.value = 0
    dut.a_in.value = -128
    dut.b_in.value = 127
    dut.a_valid_in.value = 1
    dut.b_valid_in.value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.a_out.value.to_signed() == -128 and dut.b_out.value == 127 and dut.a_valid_out.value == 1 and dut.b_valid_out.value == 1 and dut.acc.value.to_signed() == -16256, f"Expected a_out, b_out, a_valid_out, b_valid_out, and acc to be -128, 127, 1, 1, and -16256 respectively, but got a_out={dut.a_out.value.to_signed()}, b_out={dut.b_out.value}, a_valid_out={dut.a_valid_out.value}, b_valid_out={dut.b_valid_out.value}, acc={dut.acc.value.to_signed()}"

    dut._log.info("Boundary Neg-Neg Test")
    await FallingEdge(dut.clk)
    dut.step.value = 1
    dut.a_in.value = -128
    dut.b_in.value = -128
    dut.a_valid_in.value = 1
    dut.b_valid_in.value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.a_out.value.to_signed() == -128 and dut.b_out.value.to_signed() == -128 and dut.a_valid_out.value == 1 and dut.b_valid_out.value == 1 and dut.acc.value.to_signed() == 128, f"Expected a_out, b_out, a_valid_out, b_valid_out, and acc to be -128, -128, 1, 1, and 128 respectively, but got a_out={dut.a_out.value.to_signed()}, b_out={dut.b_out.value.to_signed()}, a_valid_out={dut.a_valid_out.value}, b_valid_out={dut.b_valid_out.value}, acc={dut.acc.value}"

    dut._log.info("Boundary Pos-Pos Test")
    await FallingEdge(dut.clk)
    dut.step.value = 1
    dut.a_in.value = 127
    dut.b_in.value = 127
    dut.a_valid_in.value = 1
    dut.b_valid_in.value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.a_out.value == 127 and dut.b_out.value == 127 and dut.a_valid_out.value == 1 and dut.b_valid_out.value == 1 and dut.acc.value == 16257, f"Expected a_out, b_out, a_valid_out, b_valid_out, and acc to be 127, 127, 1, 1, and 16257 respectively, but got a_out={dut.a_out.value}, b_out={dut.b_out.value}, a_valid_out={dut.a_valid_out.value}, b_valid_out={dut.b_valid_out.value}, acc={dut.acc.value}"

    dut._log.info("Clear During Stall Test")
    await FallingEdge(dut.clk)
    dut.step.value = 0
    dut.clear.value = 1
    dut.a_in.value = 5
    dut.b_in.value = 6
    dut.a_valid_in.value = 1
    dut.b_valid_in.value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.a_out.value == 127 and dut.b_out.value == 127 and dut.a_valid_out.value == 1 and dut.b_valid_out.value == 1 and dut.acc.value == 16257, f"Expected a_out, b_out, a_valid_out, b_valid_out, and acc to be 127, 127, 1, 1, and 16257 respectively, but got a_out={dut.a_out.value}, b_out={dut.b_out.value}, a_valid_out={dut.a_valid_out.value}, b_valid_out={dut.b_valid_out.value}, acc={dut.acc.value}"

    dut._log.info("Clear")
    await FallingEdge(dut.clk)
    dut.step.value = 1
    dut.clear.value = 1
    dut.a_in.value = 5
    dut.b_in.value = 6
    dut.a_valid_in.value = 1
    dut.b_valid_in.value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.a_out.value == 5 and dut.b_out.value == 6 and dut.a_valid_out.value == 1 and dut.b_valid_out.value == 1 and dut.acc.value == 0, f"Expected a_out, b_out, a_valid_out, b_valid_out, and acc to be 5, 6, 1, 1, and 0 respectively, but got a_out={dut.a_out.value}, b_out={dut.b_out.value}, a_valid_out={dut.a_valid_out.value}, b_valid_out={dut.b_valid_out.value}, acc={dut.acc.value}"

    dut._log.info("Reset During Stall Test")
    await FallingEdge(dut.clk)
    dut.rst.value = 1
    dut.step.value = 0
    dut.clear.value = 1
    dut.a_in.value = 5
    dut.b_in.value = 6
    dut.a_valid_in.value = 1
    dut.b_valid_in.value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.a_out.value == 0 and dut.b_out.value == 0 and dut.a_valid_out.value == 0 and dut.b_valid_out.value == 0 and dut.acc.value == 0, f"Expected a_out, b_out, a_valid_out, b_valid_out, and acc to be 0, 0, 0, 0, and 0 respectively, but got a_out={dut.a_out.value}, b_out={dut.b_out.value}, a_valid_out={dut.a_valid_out.value}, b_valid_out={dut.b_valid_out.value}, acc={dut.acc.value}"

    dut._log.info("Resume After Reset")
    await FallingEdge(dut.clk)
    dut.rst.value = 0
    dut.step.value = 1
    dut.clear.value = 0
    dut.a_in.value = 2
    dut.b_in.value = 3
    dut.a_valid_in.value = 1
    dut.b_valid_in.value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.a_out.value == 2 and dut.b_out.value == 3 and dut.a_valid_out.value == 1 and dut.b_valid_out.value == 1 and dut.acc.value == 6, f"Expected a_out, b_out, a_valid_out, b_valid_out, and acc to be 2, 3, 1, 1, and 6 respectively, but got a_out={dut.a_out.value}, b_out={dut.b_out.value}, a_valid_out={dut.a_valid_out.value}, b_valid_out={dut.b_valid_out.value}, acc={dut.acc.value}"

    dut._log.info("Valid Zero Test")
    await FallingEdge(dut.clk)
    dut.step.value = 1
    dut.a_in.value = 0
    dut.b_in.value = -128
    dut.a_valid_in.value = 1
    dut.b_valid_in.value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.a_out.value == 0 and dut.b_out.value.to_signed() == -128 and dut.a_valid_out.value == 1 and dut.b_valid_out.value == 1 and dut.acc.value == 6, f"Expected a_out, b_out, a_valid_out, b_valid_out, and acc to be 0, -128, 1, 1, and 6 respectively, but got a_out={dut.a_out.value}, b_out={dut.b_out.value.to_signed()}, a_valid_out={dut.a_valid_out.value}, b_valid_out={dut.b_valid_out.value}, acc={dut.acc.value}"

    dut._log.info("Negative B Test")
    await FallingEdge(dut.clk)
    dut.step.value = 1
    dut.a_in.value = 3
    dut.b_in.value = -4
    dut.a_valid_in.value = 1
    dut.b_valid_in.value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.a_out.value == 3 and dut.b_out.value.to_signed() == -4 and dut.a_valid_out.value == 1 and dut.b_valid_out.value == 1 and dut.acc.value.to_signed() == -6, f"Expected a_out, b_out, a_valid_out, b_valid_out, and acc to be 3, -4, 1, 1, and -6 respectively, but got a_out={dut.a_out.value}, b_out={dut.b_out.value.to_signed()}, a_valid_out={dut.a_valid_out.value}, b_valid_out={dut.b_valid_out.value}, acc={dut.acc.value.to_signed()}"

    dut._log.info("Both Invalid Test")
    await FallingEdge(dut.clk)
    dut.step.value = 1
    dut.a_in.value = 11
    dut.b_in.value = 12
    dut.a_valid_in.value = 0
    dut.b_valid_in.value = 0
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.a_out.value == 11 and dut.b_out.value == 12 and dut.a_valid_out.value == 0 and dut.b_valid_out.value == 0 and dut.acc.value.to_signed() == -6, f"Expected a_out, b_out, a_valid_out, b_valid_out, and acc to be 11, 12, 0, 0, and -6 respectively, but got a_out={dut.a_out.value}, b_out={dut.b_out.value}, a_valid_out={dut.a_valid_out.value}, b_valid_out={dut.b_valid_out.value}, acc={dut.acc.value.to_signed()}"

    dut._log.info("Three-Edge Stall Test")
    await FallingEdge(dut.clk)
    dut.step.value = 0
    dut.a_in.value = 5
    dut.b_in.value = 6
    dut.a_valid_in.value = 0
    dut.b_valid_in.value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.a_out.value == 11 and dut.b_out.value == 12 and dut.a_valid_out.value == 0 and dut.b_valid_out.value == 0 and dut.acc.value.to_signed() == -6, f"Expected a_out, b_out, a_valid_out, b_valid_out, and acc to be 11, 12, 0, 0, and -6 respectively, but got a_out={dut.a_out.value}, b_out={dut.b_out.value}, a_valid_out={dut.a_valid_out.value}, b_valid_out={dut.b_valid_out.value}, acc={dut.acc.value.to_signed()}"
    await FallingEdge(dut.clk)
    dut.step.value = 0
    dut.a_in.value = 10
    dut.b_in.value = -15
    dut.a_valid_in.value = 1
    dut.b_valid_in.value = 0
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.a_out.value == 11 and dut.b_out.value == 12 and dut.a_valid_out.value == 0 and dut.b_valid_out.value == 0 and dut.acc.value.to_signed() == -6, f"Expected a_out, b_out, a_valid_out, b_valid_out, and acc to be 11, 12, 0, 0, and -6 respectively, but got a_out={dut.a_out.value}, b_out={dut.b_out.value}, a_valid_out={dut.a_valid_out.value}, b_valid_out={dut.b_valid_out.value}, acc={dut.acc.value.to_signed()}"
    await FallingEdge(dut.clk)
    dut.step.value = 0
    dut.a_in.value = -34
    dut.b_in.value = -6
    dut.a_valid_in.value = 1
    dut.b_valid_in.value = 0
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.a_out.value == 11 and dut.b_out.value == 12 and dut.a_valid_out.value == 0 and dut.b_valid_out.value == 0 and dut.acc.value.to_signed() == -6, f"Expected a_out, b_out, a_valid_out, b_valid_out, and acc to be 11, 12, 0, 0, and -6 respectively, but got a_out={dut.a_out.value}, b_out={dut.b_out.value}, a_valid_out={dut.a_valid_out.value}, b_valid_out={dut.b_valid_out.value}, acc={dut.acc.value.to_signed()}"

    dut._log.info("Resume")
    await FallingEdge(dut.clk)
    dut.step.value = 1
    dut.a_in.value = -2
    dut.b_in.value = -3
    dut.a_valid_in.value = 1
    dut.b_valid_in.value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert dut.a_out.value.to_signed() == -2 and dut.b_out.value.to_signed() == -3 and dut.a_valid_out.value == 1 and dut.b_valid_out.value == 1 and dut.acc.value == 0, f"Expected a_out, b_out, a_valid_out, b_valid_out, and acc to be -2, -3, 1, 1, and 0 respectively, but got a_out={dut.a_out.value.to_signed()}, b_out={dut.b_out.value.to_signed()}, a_valid_out={dut.a_valid_out.value}, b_valid_out={dut.b_valid_out.value}, acc={dut.acc.value}"