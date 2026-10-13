import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb.triggers import FallingEdge
from cocotb.triggers import ReadOnly

@cocotb.test()
async def test_smoke_reg(dut):
    
    dut.clk.value = 0
    dut.rst.value = 1
    dut.d.value = 0

    clock = Clock(dut.clk, 10, unit="ns")  # Create a clock with a period of 10 ns
    clock.start(start_high=False)  # Start the clock low

    await RisingEdge(dut.clk)  # Wait for the first rising edge of the clock
    await ReadOnly()  # Wait for the read-only phase of the simulation
    assert dut.q.value == 0, f"Expected q to be 0, but got {dut.q.value}"

    await FallingEdge(dut.clk)  # Wait for the falling edge of the clock
    dut.rst.value = 0
    dut.d.value = 0xA5
    await RisingEdge(dut.clk)  # Wait for the next rising edge of the clock
    await ReadOnly()  # Wait for the read-only phase of the simulation
    assert dut.q.value == 0xA5, f"Expected q to be 0xA5, but got {dut.q.value} (Capture failure)"

    await FallingEdge(dut.clk)  # Wait for the falling edge of the clock
    dut.rst.value = 1
    dut.d.value = 0x3C
    await ReadOnly()  # Wait for the read-only phase of the simulation
    assert dut.q.value == 0xA5, f"Expected q to be 0xA5, but got {dut.q.value} (Unexpected change before rising edge)"
    
    await RisingEdge(dut.clk)  # Wait for the next rising edge of the clock
    await ReadOnly()  # Wait for the read-only phase of the simulation
    assert dut.q.value == 0, f"Expected q to be 0 but got {dut.q.value}"